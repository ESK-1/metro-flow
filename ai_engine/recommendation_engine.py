from __future__ import annotations

import logging
import os
from datetime import datetime, time

import pandas as pd

from utils.crowd_thresholds import LOW_MAX, MEDIUM_MAX

LOGGER = logging.getLogger(__name__)


def generate_ai_recommendations(
    route_summary: dict,
    route_crowd_df: pd.DataFrame,
    high_risk_df: pd.DataFrame,
    route_score: int | float,
    travel_time: str | time | datetime,
) -> str:
    context = _build_context(route_summary, route_crowd_df, high_risk_df, route_score, travel_time)
    # IBM Granite is the preferred optional AI backend for the internship project.
    # IBM Bob is the development partner used to build/test/refine this workflow;
    # Bob itself is not a runtime inference API embedded in the Streamlit app.
    if os.getenv("WATSONX_APIKEY") and os.getenv("WATSONX_PROJECT_ID"):
        try:
            granite_text = _generate_with_granite(context)
            if granite_text.strip():
                return granite_text.strip()
        except Exception as exc:
            LOGGER.warning("IBM Granite recommendation failed; falling back to next tier. Reason: %s", exc)

    # Keep OpenAI as a backwards-compatible optional backend.
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            llm_text = _generate_with_llm(context, api_key)
            if llm_text.strip():
                return llm_text.strip()
        except Exception as exc:
            LOGGER.warning("OpenAI recommendation failed; falling back to deterministic. Reason: %s", exc)
    return _generate_deterministic(context)


def _build_context(
    route_summary: dict,
    route_crowd_df: pd.DataFrame,
    high_risk_df: pd.DataFrame,
    route_score: int | float,
    travel_time: str | time | datetime,
) -> dict:
    route = route_summary.get("route", [])
    top_crowded = (
        route_crowd_df.sort_values("crowd_score", ascending=False)
        .head(3)[["station_name", "crowd_score", "crowd_category"]]
        .to_dict(orient="records")
        if not route_crowd_df.empty
        else []
    )
    high_risk_stations = (
        high_risk_df[high_risk_df["risk_level"].eq("High")]["station_name"].tolist()
        if not high_risk_df.empty
        else []
    )
    return {
        "source": route_summary.get("source", ""),
        "destination": route_summary.get("destination", ""),
        "travel_time": _format_time(travel_time),
        "route": route,
        "station_count": route_summary.get("number_of_stations", len(route)),
        "estimated_minutes": route_summary.get("estimated_travel_time_min", 0),
        "interchanges": route_summary.get("number_of_interchanges", 0),
        "lines_used": route_summary.get("lines_used", []),
        "route_score": int(round(route_score)),
        "route_category": _category(route_score),
        "top_crowded": top_crowded,
        "high_risk_stations": high_risk_stations,
    }


def _generate_with_granite(context: dict) -> str:
    """Generate commuter guidance with IBM Granite on watsonx.ai.

    Credentials are read from environment variables so secrets never live in source code.
    Required: WATSONX_APIKEY, WATSONX_PROJECT_ID.
    Optional: WATSONX_URL (defaults to IBM Cloud us-south), WATSONX_MODEL_ID.
    """
    import requests

    api_key = os.environ["WATSONX_APIKEY"]
    project_id = os.environ["WATSONX_PROJECT_ID"]
    base_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com").rstrip("/")
    model_id = os.getenv("WATSONX_MODEL_ID", "ibm/granite-4-h-small")

    token_response = requests.post(
        "https://iam.cloud.ibm.com/oidc/token",
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    token_response.raise_for_status()
    access_token = token_response.json()["access_token"]

    prompt = (
        "You are MetroFlow AI, a Delhi Metro sustainability and crowd-awareness assistant. "
        "Use ONLY the supplied route context. Do not invent passenger counts or real-time conditions. "
        "Give exactly five short labeled lines: Condition, Congestion, Recommendation, Timing, Transfer. "
        "Clearly call crowd values estimates based on historical line-level demand. "
        f"Route context: {context}"
    )

    response = requests.post(
        f"{base_url}/ml/v1/text/chat?version=2024-05-01",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "messages": [{"role": "user", "content": prompt}],
            "project_id": project_id,
            "model_id": model_id,
            "max_completion_tokens": 300,
            "temperature": 0.2,
        },
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        return " ".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    return str(content)


def _generate_with_llm(context: dict, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are MetroFlow AI, a concise Delhi Metro route assistant. "
                    "Give route-specific advice only. Do not repeat tables. "
                    "Use 4-5 short labeled lines: Condition, Congestion, Recommendation, Timing, Transfer."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Route context: {context}. Write human-readable commuter guidance. "
                    "If no high-risk stations exist, say the route looks favorable. "
                    "If the route score is High, suggest travelling earlier or later."
                ),
            },
        ],
        temperature=0.35,
        max_tokens=260,
    )
    return response.choices[0].message.content or ""


def _generate_deterministic(context: dict) -> str:
    source = context["source"]
    destination = context["destination"]
    time_label = context["travel_time"]
    score = context["route_score"]
    category = context["route_category"]
    risk_names = context["high_risk_stations"]
    top_crowded = [item["station_name"] for item in context["top_crowded"]]
    interchanges = int(context["interchanges"] or 0)
    lines = context["lines_used"]

    if category == "Low":
        condition = (
            f"Condition: {source} to {destination} looks favorable around {time_label}, "
            f"with a low route crowd score of {score}/100."
        )
    elif category == "Medium":
        condition = (
            f"Condition: {source} to {destination} is workable around {time_label}, "
            f"with a medium route crowd score of {score}/100."
        )
    else:
        condition = (
            f"Condition: {source} to {destination} is likely to feel crowded around {time_label}, "
            f"with a high route crowd score of {score}/100."
        )

    if risk_names:
        congestion = (
            "Congestion: Crowd buildup is expected near "
            f"{_join_names(risk_names[:3])}; these are the stations most likely to slow boarding."
        )
    else:
        congestion = "Congestion: No high-risk stations are flagged on this route, so the journey looks favorable."

    if risk_names:
        recommendation = (
            "Recommendation: Keep movement brisk through "
            f"{_join_names(risk_names[:2])} and avoid waiting at the busiest platform entry points."
        )
    elif top_crowded:
        recommendation = (
            "Recommendation: The route is comfortable overall; stay alert near "
            f"{_join_names(top_crowded[:2])}, which may still be busier than the rest."
        )
    else:
        recommendation = "Recommendation: The route is currently comfortable with low congestion risk."

    if category == "High":
        timing = "Timing: Leaving 15-20 minutes earlier should improve boarding comfort."
    elif category == "Medium":
        timing = "Timing: Your selected time is acceptable, but a 10-15 minute shift may make the ride smoother."
    else:
        timing = "Timing: No timing change is needed for this route based on the selected travel window."

    if interchanges:
        transfer = (
            f"Transfer: This route uses {interchanges} interchange"
            f"{'s' if interchanges != 1 else ''} across {_join_names(lines)}; keep extra attention at transfer platforms."
        )
    else:
        transfer = "Transfer: No interchange is needed, so the route should be simpler to follow."

    return "\n".join([condition, congestion, recommendation, timing, transfer])


def _format_time(value: str | time | datetime) -> str:
    if isinstance(value, datetime):
        return value.strftime("%I:%M %p")
    if isinstance(value, time):
        return value.strftime("%I:%M %p")
    return str(value)


def _category(score: int | float) -> str:
    if score <= LOW_MAX:
        return "Low"
    if score <= MEDIUM_MAX:
        return "Medium"
    return "High"


def _join_names(names: list[str]) -> str:
    clean = [str(name) for name in names if str(name)]
    if not clean:
        return "the route"
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} and {clean[1]}"
    return f"{', '.join(clean[:-1])}, and {clean[-1]}"
