from __future__ import annotations

import pandas as pd

from utils.crowd_thresholds import LOW_MAX, MEDIUM_MAX


def detect_risk_stations(route_crowd_df: pd.DataFrame) -> pd.DataFrame:
    """Return every station on the route with its crowd-based risk category."""
    if route_crowd_df.empty:
        return pd.DataFrame(columns=["station_name", "risk_level", "congestion_severity"])

    risk = route_crowd_df[["station_name", "crowd_score", "crowd_category"]].copy()
    risk["risk_level"] = risk["crowd_category"]
    risk["congestion_severity"] = risk["crowd_score"].map(lambda score: f"{int(score)} / 100")
    return risk[["station_name", "risk_level", "congestion_severity"]].reset_index(drop=True)


def detect_high_risk_stations(route_crowd_df: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible helper: return only High/Severe stations."""
    all_risk = detect_risk_stations(route_crowd_df)
    if all_risk.empty:
        return all_risk
    return all_risk[all_risk["risk_level"].isin(["High", "Severe"])].reset_index(drop=True)


def calculate_route_crowd_score(route_crowd_df: pd.DataFrame) -> int:
    if route_crowd_df.empty:
        return 0
    return int(round(route_crowd_df["crowd_score"].mean()))


def get_route_crowd_category(score: int | float) -> str:
    if score <= LOW_MAX:
        return "Low"
    if score <= MEDIUM_MAX:
        return "Medium"
    return "High"
