from __future__ import annotations

from functools import lru_cache

import networkx as nx

from route_engine.graph_builder import build_graph
from utils.data_loader import normalize_station_name


@lru_cache(maxsize=1)
def get_route_graph() -> nx.Graph:
    return build_graph()


def get_shortest_route(source: str, destination: str) -> list[str]:
    source = normalize_station_name(source)
    destination = normalize_station_name(destination)
    if source == destination:
        raise ValueError("Choose two different stations to calculate a route.")

    graph = get_route_graph()
    if source not in graph:
        raise ValueError(f"{source} is not available in the metro network.")
    if destination not in graph:
        raise ValueError(f"{destination} is not available in the metro network.")

    try:
        return nx.shortest_path(graph, source=source, target=destination, weight="weight")
    except nx.NetworkXNoPath as exc:
        raise ValueError("No connected metro route was found between these stations.") from exc


def calculate_route_time(route: list[str]) -> float:
    graph = get_route_graph()
    return round(sum(_edge_data(graph, start, end)["avg_travel_time_min"] for start, end in _route_pairs(route)), 1)


def calculate_route_distance(route: list[str]) -> float:
    graph = get_route_graph()
    return round(sum(_edge_data(graph, start, end)["distance_km"] for start, end in _route_pairs(route)), 2)


def count_interchanges(route: list[str]) -> int:
    lines = _edge_lines(route)
    return sum(1 for previous, current in zip(lines, lines[1:]) if previous != current)


def get_route_segment_lines(route: list[str]) -> list[str]:
    """Return the metro line used for each segment between consecutive stations."""
    return _edge_lines(route)


def get_route_lines(route: list[str]) -> list[str]:
    lines = []
    for line in _edge_lines(route):
        if line not in lines:
            lines.append(line)
    return lines


def get_route_summary(source: str, destination: str) -> dict:
    route = get_shortest_route(source, destination)
    return {
        "source": normalize_station_name(source),
        "destination": normalize_station_name(destination),
        "route": route,
        "suggested_route": " -> ".join(route),
        "number_of_stations": len(route),
        "estimated_travel_time_min": calculate_route_time(route),
        "total_distance_km": calculate_route_distance(route),
        "number_of_interchanges": count_interchanges(route),
        "lines_used": get_route_lines(route),
    }


def _route_pairs(route: list[str]) -> zip:
    return zip(route, route[1:])


def _edge_data(graph: nx.Graph, source: str, target: str) -> dict:
    return graph.edges[source, target]


def _edge_lines(route: list[str]) -> list[str]:
    graph = get_route_graph()
    return [_edge_data(graph, start, end).get("line", "Metro") for start, end in _route_pairs(route)]
