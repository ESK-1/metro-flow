from __future__ import annotations

import streamlit as st

from route_engine.graph_builder import build_graph
from route_engine.route_finder import get_route_summary
from utils.data_loader import load_stations, station_options
from utils.ui import configure_page, metric_card, top_nav
from visualizations.network_graph import render_network


configure_page("MetroFlow AI - Network Explorer")
top_nav()

st.markdown(
    """
    <div class="hero">
        <h1>Metro Network Explorer</h1>
        <p>Select a source and destination here, then the exact calculated route is highlighted on the metro network.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

stations = load_stations()
graph = build_graph(stations)
options = station_options(stations)

previous = st.session_state.get("route_summary", {})
prev_source = previous.get("source")
prev_destination = previous.get("destination")

c1, c2, c3 = st.columns([1.2, 1.2, 0.7])
with c1:
    source_index = options.index(prev_source) if prev_source in options else (options.index("Rajiv Chowk") if "Rajiv Chowk" in options else 0)
    source = st.selectbox("Source Station", options, index=source_index, key="network_source")
with c2:
    destination_index = options.index(prev_destination) if prev_destination in options else (options.index("Botanical Garden") if "Botanical Garden" in options else min(1, len(options)-1))
    destination = st.selectbox("Destination Station", options, index=destination_index, key="network_destination")
with c3:
    st.write("")
    st.write("")
    show_route = st.button("Highlight Route", type="primary", width="stretch")

if show_route:
    if source == destination:
        st.warning("Choose two different stations.")
    else:
        try:
            summary = get_route_summary(source, destination)
            st.session_state["route_summary"] = summary
            st.session_state["network_route"] = summary["route"]
        except ValueError as exc:
            st.error(str(exc))

route_summary = st.session_state.get("route_summary", {})
route = st.session_state.get("network_route", route_summary.get("route", []))

# If the user arrived from Home, the selected route is already available.
# Do not make them enter source/destination again just to see the same route.
if route and not show_route:
    st.session_state["network_route"] = route

if route:
    st.markdown('<div class="section-title">Selected Route</div>', unsafe_allow_html=True)
    summary_cols = st.columns(4)
    with summary_cols[0]:
        metric_card("Source", route_summary.get("source", route[0]))
    with summary_cols[1]:
        metric_card("Destination", route_summary.get("destination", route[-1]))
    with summary_cols[2]:
        metric_card("Stations", str(route_summary.get("number_of_stations", len(route))))
    with summary_cols[3]:
        metric_card("Interchanges", str(route_summary.get("number_of_interchanges", 0)))

    st.info("🔵 Source  •  🔴 Destination  •  The selected route has a dark-blue outer highlight/glow with its original metro-line colour visible in the centre. Other lines remain in their original colours and are faded. This route was loaded from your Home-page selection, so you do not need to enter it again.")
else:
    st.info("Choose a source and destination, then click **Highlight Route**. Only that route will receive the dark-blue outer highlight.")

st.markdown('<div class="section-title">Interactive Metro Network</div>', unsafe_allow_html=True)
render_network(graph, route, height=720)
