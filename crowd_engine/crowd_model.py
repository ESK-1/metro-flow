from __future__ import annotations

from datetime import datetime, time
from functools import lru_cache
from pathlib import Path

import pandas as pd

from utils.crowd_thresholds import LOW_MAX, MEDIUM_MAX
from utils.data_loader import load_stations, normalize_station_name
from utils.station_profiles import BUSINESS_STATIONS, INTERCHANGE_STATIONS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMAND_FILE = PROJECT_ROOT / "data" / "line_passenger_demand.csv"


def parse_travel_time(travel_time: str | time | datetime) -> time:
    if isinstance(travel_time, datetime):
        return travel_time.time()
    if isinstance(travel_time, time):
        return travel_time
    value = str(travel_time).strip()
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M%p"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    raise ValueError("Enter a valid travel time.")


def get_hour_from_time(travel_time: str | time | datetime) -> int:
    return parse_travel_time(travel_time).hour


def crowd_category(score: float) -> str:
    if score <= LOW_MAX:
        return "Low"
    if score <= MEDIUM_MAX:
        return "Medium"
    return "High"


def crowd_color(category: str) -> str:
    return {"Low": "#15803d", "Medium": "#b7791f", "High": "#c2410c"}.get(category, "#475569")


@lru_cache(maxsize=1)
def _load_line_demand() -> pd.DataFrame:
    if not DEMAND_FILE.exists():
        raise FileNotFoundError(f"Missing crowd-demand dataset: {DEMAND_FILE}")
    data = pd.read_csv(DEMAND_FILE)
    required = {"line_name", "total_passengers_per_day", "route_length_km", "pax_per_km"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Passenger-demand dataset is missing columns: {sorted(missing)}")
    data["line_name"] = data["line_name"].astype(str).str.strip()
    data["pax_per_km"] = pd.to_numeric(data["pax_per_km"], errors="coerce")
    return data.dropna(subset=["pax_per_km"]).copy()


def _canonical_line(line: str) -> str:
    value = str(line).strip()
    if value.lower() in {"blue line branch", "blue branch"}:
        return "Blue Line"
    if value.lower() in {"green line branch", "green branch"}:
        return "Green Line"
    return value


def _demand_score(line: str, demand: pd.DataFrame) -> tuple[float, float, str]:
    canonical = _canonical_line(line)
    available = demand.copy()
    available["canonical_line"] = available["line_name"].map(_canonical_line)
    match = available[available["canonical_line"].eq(canonical)]
    if match.empty:
        # The supplied spreadsheet has no passenger/km record for every Delhi Metro line.
        # For those lines we use the median of the supplied lines as a transparent fallback,
        # rather than inventing a station-level passenger count.
        pax_per_km = float(available["pax_per_km"].median())
        source = "Median of supplied line demand"
    else:
        pax_per_km = float(match.iloc[0]["pax_per_km"])
        source = "Supplied historical line demand"

    min_demand = float(available["pax_per_km"].min())
    max_demand = float(available["pax_per_km"].max())
    if max_demand == min_demand:
        base = 50.0
    else:
        base = 100.0 * (pax_per_km - min_demand) / (max_demand - min_demand)
    return max(0.0, min(100.0, base)), pax_per_km, source


def _time_adjustment(hour: int) -> tuple[float, str]:
    if 8 <= hour <= 10:
        return 1.15, "Morning peak adjustment"
    if 17 <= hour <= 20:
        return 1.20, "Evening peak adjustment"
    if hour in {7, 11, 16, 21}:
        return 1.07, "Peak shoulder adjustment"
    return 1.00, "Off-peak adjustment"


def predict_station_crowd(
    station_name: str,
    travel_time: str | time | datetime,
    station_metadata: pd.DataFrame | pd.Series | dict | None = None,
    ridership_data: pd.DataFrame | None = None,
) -> dict:
    station = normalize_station_name(station_name)
    hour = get_hour_from_time(travel_time)
    demand = _load_line_demand()
    station_row = _station_metadata_row(station, station_metadata)
    line = str(station_row.get("line", "Metro"))

    base_score, pax_per_km, demand_source = _demand_score(line, demand)
    time_factor, time_source = _time_adjustment(hour)
    is_interchange = bool(station_row.get("is_interchange", station in INTERCHANGE_STATIONS))
    is_business = station in BUSINESS_STATIONS

    score = base_score * time_factor
    if is_interchange:
        score += 5
    if is_business and (8 <= hour <= 11 or 17 <= hour <= 20):
        score += 5
    score = max(0.0, min(100.0, score))
    category = crowd_category(score)

    return {
        "station_name": station,
        "line": line,
        "pax_per_km": round(pax_per_km, 2),
        "demand_source": demand_source,
        "time_adjustment": time_source,
        "is_interchange": is_interchange,
        "crowd_score": int(round(score)),
        "crowd_category": category,
        "estimated_crowd_level": category,
        "color": crowd_color(category),
    }


def analyze_route_crowd(route: list[str], travel_time: str | time | datetime) -> pd.DataFrame:
    stations = load_stations()
    rows = []
    for station in route:
        station_name = normalize_station_name(station)
        metadata = stations[stations["station_name"].eq(station_name)]
        row = metadata.iloc[0] if not metadata.empty else None
        rows.append(predict_station_crowd(station_name, travel_time, row))
    return pd.DataFrame(rows)


def _station_metadata_row(station_name: str, station_metadata: pd.DataFrame | pd.Series | dict | None) -> dict:
    if station_metadata is None:
        stations = load_stations()
        match = stations[stations["station_name"].eq(station_name)]
        return match.iloc[0].to_dict() if not match.empty else {}
    if isinstance(station_metadata, pd.DataFrame):
        match = station_metadata[station_metadata["station_name"].eq(station_name)]
        return match.iloc[0].to_dict() if not match.empty else {}
    if isinstance(station_metadata, pd.Series):
        return station_metadata.to_dict()
    return dict(station_metadata)
