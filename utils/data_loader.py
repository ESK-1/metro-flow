from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from utils.line_sequences import ALIASES, LINE_SEQUENCES
from utils.station_profiles import BUSINESS_STATIONS, INTERCHANGE_STATIONS

LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
LEGACY_STATION_FILE = DATA_DIR / "delhi_metro_stations.csv"

STATION_COLUMNS = ["station_id", "station_name", "line", "latitude", "longitude", "is_interchange"]
CONNECTION_COLUMNS = ["source", "target", "line", "distance_km", "avg_travel_time_min"]
RIDERSHIP_COLUMNS = ["station_name", "hour", "base_crowd_score", "weekday_factor", "peak_factor"]

FALLBACK_COORDINATES = {
    "Samaypur Badli": (28.7446, 77.1383),
    "Vishwa Vidyalaya": (28.6950, 77.2147),
    "Kashmere Gate": (28.6675, 77.2282),
    "New Delhi": (28.6427, 77.2219),
    "Rajiv Chowk": (28.6328, 77.2197),
    "Central Secretariat": (28.6159, 77.2123),
    "INA": (28.5744, 77.2102),
    "Hauz Khas": (28.5443, 77.2067),
    "Saket": (28.5206, 77.2012),
    "Millennium City Centre Gurugram": (28.4593, 77.0727),
    "HUDA City Centre": (28.4593, 77.0727),
    "Dwarka Sector 21": (28.5518, 77.0586),
    "Janakpuri West": (28.6290, 77.0779),
    "Kirti Nagar": (28.6533, 77.1418),
    "Mandi House": (28.6256, 77.2342),
    "Yamuna Bank": (28.6233, 77.2679),
    "Botanical Garden": (28.5639, 77.3343),
    "Noida Electronic City": (28.6276, 77.3754),
    "Lajpat Nagar": (28.5706, 77.2365),
    "Kalkaji Mandir": (28.5498, 77.2607),
    "Raja Nahar Singh": (28.3400, 77.3164),
    "Rithala": (28.7208, 77.1072),
    "Netaji Subhash Place": (28.6961, 77.1526),
    "Inderlok": (28.6732, 77.1706),
    "Welcome": (28.6718, 77.2776),
    "Shaheed Sthal": (28.6706, 77.4156),
    "Brigadier Hoshiyar Singh": (28.6975, 76.9192),
    "Ashok Park Main": (28.6716, 77.1553),
    "Punjabi Bagh": (28.6689, 77.1325),
    "Mundka": (28.6824, 77.0306),
    "Majlis Park": (28.7244, 77.1820),
    "Azadpur": (28.7077, 77.1755),
    "Rajouri Garden": (28.6422, 77.1161),
    "Anand Vihar ISBT": (28.6468, 77.3180),
    "Shiv Vihar": (28.7027, 77.3020),
    "Janpath": (28.6089, 77.2182),
    "ITO": (28.6305, 77.2414),
    "Okhla NSIC": (28.5545, 77.2648),
    "Munirka": (28.5549, 77.1711),
    "Delhi Aerocity": (28.5488, 77.1208),
    "Indira Gandhi International Airport": (28.5562, 77.1000),
    "Najafgarh": (28.6123, 76.9824),
}


def clean_station_name(value: str) -> str:
    return (
        str(value)
        .replace("†", "")
        .replace("â€ ", "")
        .replace("–", "-")
        .replace("â€“", "-")
        .replace("  ", " ")
        .strip()
    )


def normalize_station_name(value: str) -> str:
    cleaned = clean_station_name(value)
    return clean_station_name(ALIASES.get(cleaned, cleaned))


def _read_first_available(names: list[str]) -> pd.DataFrame | None:
    for name in names:
        path = RAW_DIR / name
        if path.exists():
            LOGGER.info("Loading metro data file: %s", path)
            return pd.read_csv(path)
    return None


def _route_line_lookup() -> dict[str, str]:
    routes = _read_first_available(["routes.txt", "routes.csv"])
    if routes is None or "route_id" not in routes.columns:
        return {}
    line_col = _first_column(routes, ["route_long_name", "route_short_name", "line", "route_name"])
    if not line_col:
        return {}
    return {
        str(route_id): _normalize_line(line_name)
        for route_id, line_name in zip(routes["route_id"], routes[line_col])
    }


def _normalize_line(value: str) -> str:
    value = str(value).strip()
    return ALIASES.get(value, value)


def _station_id(name: str) -> str:
    cleaned = clean_station_name(name).lower()
    return "dmrc_" + "".join(char if char.isalnum() else "_" for char in cleaned).strip("_")


def _sequence_station_line_map() -> dict[str, str]:
    mapping = {}
    for line, sequence in LINE_SEQUENCES.items():
        for station in sequence:
            mapping.setdefault(clean_station_name(ALIASES.get(station, station)), line)
    return mapping


def _existing_station_source() -> pd.DataFrame | None:
    raw = _read_first_available(["stations.csv", "stops.txt", "stops.csv"])
    if raw is not None:
        return raw
    if LEGACY_STATION_FILE.exists():
        LOGGER.info("Loading bundled station file: %s", LEGACY_STATION_FILE)
        return pd.read_csv(LEGACY_STATION_FILE)
    return None


def _fallback_station_data() -> pd.DataFrame:
    LOGGER.info("Station files unavailable; building internal fallback station layer.")
    rows = []
    seen: set[str] = set()
    required_lines = [
        "Yellow Line",
        "Blue Line",
        "Blue Line Branch",
        "Violet Line",
        "Magenta Line",
        "Pink Line",
        "Red Line",
        "Green Line",
        "Orange Line",
        "Grey Line",
    ]
    for line in required_lines:
        sequence = LINE_SEQUENCES.get(line, [])
        for index, station in enumerate(sequence):
            station_name = clean_station_name(ALIASES.get(station, station))
            if station_name in seen:
                continue
            seen.add(station_name)
            lat, lon = _fallback_coordinate(station_name, line, index, len(sequence))
            rows.append(
                {
                    "station_id": _station_id(station_name),
                    "station_name": station_name,
                    "line": line,
                    "latitude": lat,
                    "longitude": lon,
                }
            )
    return pd.DataFrame(rows)


def _fallback_coordinate(station_name: str, line: str, index: int, line_size: int) -> tuple[float, float]:
    if station_name in FALLBACK_COORDINATES:
        return FALLBACK_COORDINATES[station_name]
    anchors = [FALLBACK_COORDINATES[name] for name in LINE_SEQUENCES.get(line, []) if name in FALLBACK_COORDINATES]
    if len(anchors) >= 2:
        progress = index / max(1, line_size - 1)
        start_lat, start_lon = anchors[0]
        end_lat, end_lon = anchors[-1]
        return (
            round(start_lat + (end_lat - start_lat) * progress, 6),
            round(start_lon + (end_lon - start_lon) * progress, 6),
        )
    return round(28.61 + index * 0.004, 6), round(77.20 + index * 0.004, 6)


def load_station_data() -> pd.DataFrame:
    source = _existing_station_source()
    sequence_lines = _sequence_station_line_map()
    route_lines = _route_line_lookup()

    if source is None:
        stations = _fallback_station_data()
    elif {"stop_id", "stop_name"}.issubset(source.columns):
        station_names = source["stop_name"].map(normalize_station_name)
        stations = pd.DataFrame(
            {
                "station_id": source["stop_id"].astype(str),
                "station_name": station_names,
                "line": _line_series(source, station_names, sequence_lines, route_lines),
                "latitude": pd.to_numeric(source.get("stop_lat"), errors="coerce"),
                "longitude": pd.to_numeric(source.get("stop_lon"), errors="coerce"),
            }
        )
    else:
        name_col = _first_column(source, ["station_name", "station", "Station", "name", "stop_name"])
        line_col = _first_column(source, ["line", "Line", "route", "route_long_name"])
        lat_col = _first_column(source, ["latitude", "Latitude", "lat", "stop_lat"])
        lon_col = _first_column(source, ["longitude", "Longitude", "lon", "lng", "stop_lon"])
        id_col = _first_column(source, ["station_id", "stop_id", "id"])

        station_names = source[name_col].map(normalize_station_name)
        stations = pd.DataFrame(
            {
                "station_id": source[id_col].astype(str) if id_col else station_names.map(_station_id),
                "station_name": station_names,
                "line": _line_series(source, station_names, sequence_lines, route_lines, line_col),
                "latitude": pd.to_numeric(source[lat_col], errors="coerce") if lat_col else np.nan,
                "longitude": pd.to_numeric(source[lon_col], errors="coerce") if lon_col else np.nan,
            }
        )

    stations = _complete_station_metadata(stations)
    return stations[STATION_COLUMNS + ["station"]].sort_values("station_name").reset_index(drop=True)


def _line_series(
    source: pd.DataFrame,
    station_names: pd.Series,
    sequence_lines: dict[str, str],
    route_lines: dict[str, str],
    line_col: str | None = None,
) -> pd.Series:
    if line_col:
        return source[line_col].map(_normalize_line)
    for candidate in ["line", "Line", "route_long_name", "route_short_name"]:
        if candidate in source.columns:
            return source[candidate].map(_normalize_line)
    if "route_id" in source.columns and route_lines:
        return source["route_id"].astype(str).map(route_lines).fillna("Metro")
    return station_names.map(lambda name: sequence_lines.get(normalize_station_name(name), "Metro"))


def _first_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lookup = {column.lower(): column for column in df.columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def _complete_station_metadata(stations: pd.DataFrame) -> pd.DataFrame:
    stations = stations.copy()
    stations["station_name"] = stations["station_name"].map(normalize_station_name)
    stations["line"] = stations["line"].fillna("").map(_normalize_line)
    stations.loc[stations["line"].eq("") | stations["line"].eq("nan"), "line"] = stations["station_name"].map(
        lambda name: _sequence_station_line_map().get(name, "Metro")
    )
    stations["station_id"] = stations["station_id"].fillna(stations["station_name"].map(_station_id)).astype(str)
    stations["latitude"] = pd.to_numeric(stations["latitude"], errors="coerce")
    stations["longitude"] = pd.to_numeric(stations["longitude"], errors="coerce")

    for idx, row in stations.iterrows():
        if pd.isna(row["latitude"]) or pd.isna(row["longitude"]):
            lat, lon = FALLBACK_COORDINATES.get(row["station_name"], (np.nan, np.nan))
            if pd.notna(lat) and pd.notna(lon):
                stations.at[idx, "latitude"] = lat
                stations.at[idx, "longitude"] = lon

    duplicate_names = stations["station_name"].duplicated(keep=False)
    stations["is_interchange"] = duplicate_names | stations["station_name"].isin(INTERCHANGE_STATIONS)
    stations = stations.drop_duplicates("station_name", keep="first")
    stations["station"] = stations["station_name"]
    return stations


def load_connection_data(stations: pd.DataFrame | None = None) -> pd.DataFrame:
    stations = stations if stations is not None else load_station_data()
    source = _read_first_available(["connections.csv", "stop_times.txt", "stop_times.csv"])
    station_names = set(stations["station_name"])
    route_lines = _route_line_lookup()

    if source is not None and {"source", "target"}.issubset(source.columns):
        connections = pd.DataFrame(
            {
                "source": source["source"].map(normalize_station_name),
                "target": source["target"].map(normalize_station_name),
                "line": _connection_line_series(source, route_lines),
                "distance_km": pd.to_numeric(source.get("distance_km"), errors="coerce"),
                "avg_travel_time_min": pd.to_numeric(source.get("avg_travel_time_min"), errors="coerce"),
            }
        )
    elif source is not None and {"trip_id", "stop_id", "stop_sequence"}.issubset(source.columns):
        LOGGER.info("Building connections from stop_times sequence.")
        id_to_station = stations.set_index("station_id")["station_name"].to_dict()
        ordered = source.sort_values(["trip_id", "stop_sequence"])
        rows = []
        for _, trip in ordered.groupby("trip_id"):
            names = [id_to_station.get(str(stop_id)) for stop_id in trip["stop_id"]]
            names = [name for name in names if name]
            for start, end in zip(names, names[1:]):
                rows.append({"source": start, "target": end, "line": "Metro"})
        connections = pd.DataFrame(rows)
    else:
        LOGGER.info("Connection files unavailable; deriving adjacent line connections.")
        connections = _fallback_connections(station_names)

    connections = _complete_connection_metadata(connections)
    return connections[CONNECTION_COLUMNS].drop_duplicates(["source", "target", "line"]).reset_index(drop=True)


def _connection_line_series(source: pd.DataFrame, route_lines: dict[str, str]) -> pd.Series | str:
    line_col = _first_column(source, ["line", "Line", "route_long_name", "route_short_name"])
    if line_col:
        return source[line_col].map(_normalize_line)
    if "route_id" in source.columns and route_lines:
        return source["route_id"].astype(str).map(route_lines).fillna("Metro")
    return "Metro"


def _fallback_connections(station_names: set[str]) -> pd.DataFrame:
    rows = []
    for line, sequence in LINE_SEQUENCES.items():
        route = [clean_station_name(ALIASES.get(station, station)) for station in sequence]
        route = [station for station in route if station in station_names]
        for start, end in zip(route, route[1:]):
            rows.append({"source": start, "target": end, "line": line})
    return pd.DataFrame(rows)


def _complete_connection_metadata(connections: pd.DataFrame) -> pd.DataFrame:
    connections = connections.copy()
    if connections.empty:
        return pd.DataFrame(columns=CONNECTION_COLUMNS)
    connections["source"] = connections["source"].map(normalize_station_name)
    connections["target"] = connections["target"].map(normalize_station_name)
    connections["line"] = connections["line"].map(_normalize_line)
    if "distance_km" not in connections:
        connections["distance_km"] = np.nan
    if "avg_travel_time_min" not in connections:
        connections["avg_travel_time_min"] = np.nan
    connections["distance_km"] = pd.to_numeric(connections["distance_km"], errors="coerce")
    connections["avg_travel_time_min"] = pd.to_numeric(connections["avg_travel_time_min"], errors="coerce")
    missing_distance = connections["distance_km"].isna()
    connections.loc[missing_distance, "distance_km"] = 1.25
    missing_time = connections["avg_travel_time_min"].isna()
    connections.loc[missing_time, "avg_travel_time_min"] = (connections.loc[missing_time, "distance_km"] * 1.8).clip(
        lower=1.5, upper=4.5
    )
    return connections


def load_ridership_data(stations: pd.DataFrame | None = None) -> pd.DataFrame:
    stations = stations if stations is not None else load_station_data()
    source = _read_first_available(["ridership.csv"])
    if source is not None and {"station_name", "hour"}.issubset(source.columns):
        ridership = pd.DataFrame(
            {
                "station_name": source["station_name"].map(normalize_station_name),
                "hour": pd.to_numeric(source["hour"], errors="coerce"),
                "base_crowd_score": pd.to_numeric(source.get("base_crowd_score"), errors="coerce"),
                "weekday_factor": pd.to_numeric(source.get("weekday_factor"), errors="coerce"),
                "peak_factor": pd.to_numeric(source.get("peak_factor"), errors="coerce"),
            }
        )
    else:
        LOGGER.info("Ridership file unavailable; generating internal hourly crowd layer.")
        ridership = _fallback_ridership(stations)

    ridership = _complete_ridership_metadata(ridership)
    return ridership[RIDERSHIP_COLUMNS].reset_index(drop=True)


def _fallback_ridership(stations: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for station in stations["station_name"]:
        seed = sum(ord(char) for char in station)
        base = 28 + seed % 22
        if station in INTERCHANGE_STATIONS:
            base += 16
        if station in BUSINESS_STATIONS:
            base += 11
        for hour in range(24):
            morning_peak = 1.0 if 8 <= hour <= 10 else 0.0
            evening_peak = 1.0 if 17 <= hour <= 20 else 0.0
            shoulder = 0.45 if hour in {7, 11, 16, 21} else 0.0
            peak_factor = max(morning_peak, evening_peak, shoulder)
            weekday_factor = 1.22 if station in BUSINESS_STATIONS else 1.12 if station in INTERCHANGE_STATIONS else 1.0
            rows.append(
                {
                    "station_name": station,
                    "hour": hour,
                    "base_crowd_score": min(95, round(base + peak_factor * 24)),
                    "weekday_factor": weekday_factor,
                    "peak_factor": 1.0 + peak_factor * (0.38 if station in INTERCHANGE_STATIONS else 0.28),
                }
            )
    return pd.DataFrame(rows)


def _complete_ridership_metadata(ridership: pd.DataFrame) -> pd.DataFrame:
    ridership = ridership.copy()
    ridership["station_name"] = ridership["station_name"].map(normalize_station_name)
    ridership["hour"] = pd.to_numeric(ridership["hour"], errors="coerce").fillna(0).astype(int).clip(0, 23)
    for column, default in [
        ("base_crowd_score", 45),
        ("weekday_factor", 1.0),
        ("peak_factor", 1.0),
    ]:
        ridership[column] = pd.to_numeric(ridership[column], errors="coerce").fillna(default)
    ridership["base_crowd_score"] = ridership["base_crowd_score"].clip(0, 100)
    ridership["weekday_factor"] = ridership["weekday_factor"].clip(0.7, 1.6)
    ridership["peak_factor"] = ridership["peak_factor"].clip(0.7, 1.8)
    return ridership


def validate_data(
    stations: pd.DataFrame,
    connections: pd.DataFrame,
    ridership: pd.DataFrame,
) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {"stations": [], "connections": [], "ridership": []}
    _require_columns(stations, STATION_COLUMNS, issues["stations"])
    _require_columns(connections, CONNECTION_COLUMNS, issues["connections"])
    _require_columns(ridership, RIDERSHIP_COLUMNS, issues["ridership"])

    if stations["station_name"].duplicated().any():
        issues["stations"].append("Duplicate station_name values found.")
    if len(stations) < 40:
        issues["stations"].append("Station layer contains fewer than 40 stations.")

    station_names = set(stations["station_name"])
    missing_sources = sorted(set(connections["source"]) - station_names)
    missing_targets = sorted(set(connections["target"]) - station_names)
    if missing_sources:
        issues["connections"].append(f"Connections contain unknown source stations: {missing_sources[:5]}")
    if missing_targets:
        issues["connections"].append(f"Connections contain unknown target stations: {missing_targets[:5]}")

    if not ridership["hour"].between(0, 23).all():
        issues["ridership"].append("Ridership hour values must be between 0 and 23.")
    missing_ridership = sorted(station_names - set(ridership["station_name"]))
    if missing_ridership:
        issues["ridership"].append(f"Stations missing ridership rows: {missing_ridership[:5]}")

    for group, group_issues in issues.items():
        for issue in group_issues:
            LOGGER.warning("%s data validation: %s", group, issue)
    return issues


def _require_columns(df: pd.DataFrame, required: list[str], bucket: list[str]) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        bucket.append(f"Missing columns: {missing}")


def prepare_metro_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    stations = load_station_data()
    connections = load_connection_data(stations)
    ridership = load_ridership_data(stations)
    validate_data(stations, connections, ridership)
    return stations, connections, ridership


@st.cache_data(show_spinner=False)
def _prepare_metro_data_cached() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return prepare_metro_data()


def load_stations() -> pd.DataFrame:
    stations, connections, _ = _prepare_metro_data_cached()
    result = stations.copy()
    result.attrs["connections"] = connections.copy()
    return result


def load_connections() -> pd.DataFrame:
    _, connections, _ = _prepare_metro_data_cached()
    return connections.copy()


def load_ridership() -> pd.DataFrame:
    _, _, ridership = _prepare_metro_data_cached()
    return ridership.copy()


def station_options(stations: pd.DataFrame) -> list[str]:
    column = "station_name" if "station_name" in stations.columns else "station"
    return stations[column].sort_values().tolist()
