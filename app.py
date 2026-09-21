from __future__ import annotations

from datetime import time

import streamlit as st

from ai_engine.recommendation_engine import generate_ai_recommendations
from crowd_engine.crowd_model import analyze_route_crowd
from crowd_engine.risk_scoring import (
    calculate_route_crowd_score,
    detect_risk_stations,
    get_route_crowd_category,
)
from route_engine.route_finder import get_route_segment_lines, get_route_summary
from utils.data_loader import load_stations, station_options
from utils.ui import configure_page, metric_card, top_nav
from visualizations.route_cards import (
    render_ai_recommendation_card,
    render_crowd_table,
    render_score_card,
    render_success_card,
)


configure_page("MetroFlow AI - Route Intelligence")
top_nav()

stations = load_stations()
options = station_options(stations)

st.markdown(
    """
    <div class="hero">
        <h1>AI-Powered Route Intelligence</h1>
        <p>Select your Delhi Metro journey and estimate route crowd using historical line-level passenger demand and transparent time/station adjustments.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    input_cols = st.columns([1.2, 1.2, 0.8, 0.65])
    with input_cols[0]:
        default_source = options.index("Rajiv Chowk") if "Rajiv Chowk" in options else 0
        source = st.selectbox("Source Station", options, index=default_source)
    with input_cols[1]:
        default_destination = options.index("Botanical Garden") if "Botanical Garden" in options else min(1, len(options) - 1)
        destination = st.selectbox("Destination Station", options, index=default_destination)
    with input_cols[2]:
        travel_time = st.time_input("Travel Time", value=time(9, 0), step=900)
    with input_cols[3]:
        st.write("")
        st.write("")
        analyze = st.button("Analyze Route", width="stretch")

st.caption("After analysis, the Network Explorer can open the same route automatically—no need to select the stations again.")

if analyze:
    if source == destination:
        st.warning("Choose two different stations to calculate a route.")
        st.stop()
    try:
        route_summary = get_route_summary(source, destination)
        route_crowd = analyze_route_crowd(route_summary["route"], travel_time)
        route_score = calculate_route_crowd_score(route_crowd)
        risk_stations = detect_risk_stations(route_crowd)
        ai_recommendations = generate_ai_recommendations(
            route_summary,
            route_crowd,
            risk_stations,
            route_score,
            travel_time,
        )
        st.session_state["route_summary"] = route_summary
        st.session_state["route_crowd"] = route_crowd
        st.session_state["risk_stations"] = risk_stations
        st.session_state["route_crowd_score"] = route_score
        st.session_state["route_crowd_category"] = get_route_crowd_category(route_score)
        st.session_state["ai_recommendations"] = ai_recommendations
        st.session_state["travel_time"] = travel_time

        st.session_state["network_route"] = route_summary["route"]
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

if "route_summary" in st.session_state:
    summary = st.session_state["route_summary"]
    selected_time = st.session_state["travel_time"]

    line_colors = {
        "Yellow Line": "#f2c200",
        "Blue Line": "#2563eb",
        "Blue Line Branch": "#2563eb",
        "Red Line": "#ef4444",
        "Violet Line": "#7c3aed",
        "Green Line": "#16a34a",
        "Green Line Branch": "#16a34a",
        "Pink Line": "#ec4899",
        "Magenta Line": "#d946ef",
        "Orange Line": "#f97316",
        "Grey Line": "#64748b",
    }
    segment_lines = get_route_segment_lines(summary["route"])
    route_parts = []
    for index, station in enumerate(summary["route"]):
        line = segment_lines[index] if index < len(segment_lines) else (segment_lines[-1] if segment_lines else "Metro")
        color = line_colors.get(line, "#0f766e")
        # Keep the original line colour as a slim left accent with a light tint.
        route_parts.append(
            f'<span class="route-step" style="--route-line:{color}; --route-line-bg:{color}1A;" title="{line}">{station}</span>'
        )
        if index < len(summary["route"]) - 1:
            route_parts.append('<span class="route-arrow">&rarr;</span>')
    route_sequence_html = "".join(route_parts)

    st.markdown('<div class="section-title">Journey Summary</div>', unsafe_allow_html=True)
    summary_cols = st.columns(5)
    with summary_cols[0]:
        metric_card("Source", summary["source"])
    with summary_cols[1]:
        metric_card("Destination", summary["destination"])
    with summary_cols[2]:
        metric_card("Travel Time", selected_time.strftime("%I:%M %p"))
    with summary_cols[3]:
        metric_card("Stations", str(summary["number_of_stations"]))
    with summary_cols[4]:
        metric_card("Estimated Time", f"{summary['estimated_travel_time_min']} min")

    st.markdown(
        f"""
        <div class="info-card" style="margin-top: 0.8rem;">
            <div class="metric-label">Suggested Route</div>
            <div class="route-sequence">{route_sequence_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    explore_col, _ = st.columns([0.32, 0.68])
    with explore_col:
        if st.button("🗺️ View Route in Network Explorer", type="primary", width="stretch"):
            st.session_state["network_route"] = summary["route"]
            st.switch_page("pages/network_explorer.py")

    st.markdown('<div class="section-title">Crowd Analysis Along Route</div>', unsafe_allow_html=True)
    render_crowd_table(st.session_state["route_crowd"])

    st.markdown('<div class="section-title">AI Recommendations</div>', unsafe_allow_html=True)
    render_ai_recommendation_card(st.session_state["ai_recommendations"])

    st.markdown('<div class="section-title">Route Crowd Score</div>', unsafe_allow_html=True)
    score_cols = st.columns([0.45, 0.55])
    with score_cols[0]:
        render_score_card(st.session_state["route_crowd_score"], st.session_state["route_crowd_category"])
    with score_cols[1]:
        st.markdown(
            """
            <div class="info-card">
                <div class="metric-label">Score Meaning</div>
                <div style="color:#5a6577; margin-top:0.45rem;">0-39 Low, 40-69 Medium, 70-100 High.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        """
        <div class="info-card" style="margin-top: 1rem;">
            <div class="metric-label">Journey Summary</div>
            <div style="color:#5a6577; margin-top:0.5rem;">Choose a source, destination, and travel time, then analyze the route.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
