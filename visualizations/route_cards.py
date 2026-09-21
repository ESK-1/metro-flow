from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st


def crowd_indicator_style(value: str) -> str:
    if value == "High":
        return "background-color: #fee2e2; color: #991b1b; font-weight: 800;"
    if value == "Medium":
        return "background-color: #fef3c7; color: #92400e; font-weight: 800;"
    if value == "Low":
        return "background-color: #dcfce7; color: #166534; font-weight: 800;"
    return ""


def risk_indicator_style(value: str) -> str:
    if value == "Severe":
        return "background-color: #7f1d1d; color: #ffffff; font-weight: 800;"
    if value == "High":
        return "background-color: #fee2e2; color: #991b1b; font-weight: 800;"
    if value == "Medium":
        return "background-color: #fef3c7; color: #92400e; font-weight: 800;"
    if value == "Low":
        return "background-color: #dcfce7; color: #166534; font-weight: 800;"
    return ""


def render_crowd_table(route_crowd_df: pd.DataFrame) -> None:
    """Show only commuter-facing crowd information; keep demand inputs internal."""
    display_df = route_crowd_df.rename(
        columns={
            "station_name": "Station",
            "line": "Line",
            "estimated_crowd_level": "Crowd Level",
            "crowd_score": "Crowd Score",
            "crowd_category": "Risk",
        }
    )

    preferred = ["Station", "Line", "Crowd Level", "Crowd Score", "Risk"]
    columns = [column for column in preferred if column in display_df.columns]
    if not columns:
        st.dataframe(display_df, hide_index=True, width="stretch")
        return

    display_df = display_df[columns].copy()
    if "Crowd Score" in display_df.columns:
        display_df["Crowd Score"] = display_df["Crowd Score"].round().astype(int).astype(str) + " / 100"

    style_columns = [column for column in ["Crowd Level", "Risk"] if column in display_df.columns]
    styled = display_df.style.map(crowd_indicator_style, subset=style_columns)
    st.dataframe(styled, hide_index=True, width="stretch")


def render_risk_table(risk_df: pd.DataFrame) -> None:
    display_df = risk_df.rename(
        columns={
            "station_name": "Station",
            "risk_level": "Risk Level",
            "congestion_severity": "Congestion Severity",
        }
    )
    styled = display_df.style.map(risk_indicator_style, subset=["Risk Level"])
    st.dataframe(styled, hide_index=True, width="stretch")


def render_success_card(message: str) -> None:
    st.markdown(
        f"""
        <div class="info-card" style="border-left:5px solid #15803d;">
            <div class="metric-label">Route Status</div>
            <div style="color:#166534; font-weight:750; margin-top:0.45rem;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_card(score: int, category: str) -> None:
    color = "#15803d" if category == "Low" else "#b7791f" if category == "Medium" else "#c2410c"
    st.markdown(
        f"""
        <div class="metric-card" style="border-left:5px solid {color};">
            <div class="metric-label">Overall Crowd Score</div>
            <div class="metric-value">{score}/100</div>
            <div style="color:{color}; font-weight:850; margin-top:0.45rem;">{category}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_recommendation_card(recommendations: str) -> None:
    lines = [line.strip() for line in recommendations.splitlines() if line.strip()]
    icon_map = {
        "Condition": "AI",
        "Congestion": "Risk",
        "Recommendation": "Go",
        "Timing": "Time",
        "Transfer": "Line",
    }
    rendered_lines = []
    for line in lines:
        label, sep, body = line.partition(":")
        if sep:
            icon = icon_map.get(label.strip(), "AI")
            rendered_lines.append(
                (
                    '<div class="ai-rec-row">'
                    f'<div class="ai-rec-icon">{escape(icon)}</div>'
                    f'<div><strong>{escape(label.strip())}</strong>: {escape(body.strip())}</div>'
                    "</div>"
                )
            )
        else:
            rendered_lines.append(
                (
                    '<div class="ai-rec-row">'
                    '<div class="ai-rec-icon">AI</div>'
                    f"<div>{escape(line)}</div>"
                    "</div>"
                )
            )

    st.markdown(
        f'<div class="ai-card ai-rec-card">{"".join(rendered_lines)}</div>',
        unsafe_allow_html=True,
    )
