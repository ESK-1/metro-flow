from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import networkx as nx
import streamlit as st
from pyvis.network import Network

from utils.crowd_thresholds import LINE_COLORS


def route_edges(route_stations: list[str]) -> set[tuple[str, str]]:
    return {tuple(sorted((start, end))) for start, end in zip(route_stations, route_stations[1:])}


def render_network(graph: nx.Graph, route_stations: list[str] | None = None, height: int = 680) -> None:
    """Render the metro network and emphasize only the selected route.

    The selected route is drawn as a layered edge: a wide dark-blue glow forms
    the outer highlight while a narrower edge keeps the original metro-line
    colour in the middle. Non-route lines remain visible but subdued.
    """
    selected_route = route_stations or []
    selected_nodes = set(selected_route)
    selected_edges = route_edges(selected_route)

    network = Network(
        height=f"{height}px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#1f2937",
        cdn_resources="in_line",
    )
    network.barnes_hut(gravity=-18500, central_gravity=0.35, spring_length=115, spring_strength=0.04)

    for node, data in graph.nodes(data=True):
        line = data.get("line", "Metro")
        is_selected = node in selected_nodes
        is_source = bool(selected_route) and node == selected_route[0]
        is_destination = bool(selected_route) and node == selected_route[-1]
        is_interchange = bool(data.get("is_interchange", False))
        line_color = LINE_COLORS.get(line, "#64748b")
        hover = (
            f"<strong>{node}</strong>"
            f"<br>Line: {line}"
            f"<br>Interchange: {'Yes' if is_interchange else 'No'}"
        )

        if is_source:
            background, border = "#2563eb", "#1d4ed8"
            size, border_width = 25, 5
        elif is_destination:
            background, border = "#dc2626", "#b91c1c"
            size, border_width = 25, 5
        elif is_selected:
            # Keep the station's original line colour in the centre.
            background, border = line_color, "#0b1f4a"
            size, border_width = 14, 4
        else:
            background, border = line_color, line_color
            size, border_width = 12 if is_interchange else 8, 2 if is_interchange else 1

        network.add_node(
            node,
            label=node if is_selected else "",
            title=hover,
            color={
                "background": background,
                "border": border,
                "highlight": {
                    "background": background,
                    "border": border,
                },
            },
            size=size,
            borderWidth=border_width,
            opacity=1.0 if is_selected else 0.55,
        )

    for start, end, data in graph.edges(data=True):
        line = data.get("line", "Metro")
        line_color = LINE_COLORS.get(line, "#94a3b8")
        is_selected = tuple(sorted((start, end))) in selected_edges

        if is_selected:
            # One edge with a thick dark-blue shadow keeps the original line colour
            # clearly visible in the centre. This is more reliable in PyVis than
            # drawing two identical edges on top of each other.
            network.add_edge(
                start, end,
                title=f"Selected route • {line}",
                color=line_color,
                width=6.5,
                shadow={
                    "enabled": True,
                    "color": "#071b4d",
                    "size": 13,
                    "x": 0,
                    "y": 0,
                },
                smooth=False,
            )
        else:
            network.add_edge(
                start, end,
                title=line,
                color=line_color,
                width=2.2,
                opacity=0.18 if selected_route else 0.75,
                shadow=False,
                smooth=False,
            )

    network.set_options(
        """
        {
          "nodes": {
            "font": { "size": 13, "face": "Inter" },
            "shape": "dot"
          },
          "edges": {
            "smooth": false,
            "selectionWidth": 1
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 80,
            "navigationButtons": true,
            "keyboard": true
          },
          "physics": {
            "minVelocity": 3.0,
            "stabilization": {
              "iterations": 30,
              "updateInterval": 30,
              "fit": true
            }
          }
        }
        """
    )

    html = network.generate_html(notebook=False)
    with NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
        tmp.write(html)
        html_path = Path(tmp.name)
    st.iframe(html_path, height=height + 20)
