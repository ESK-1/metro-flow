from __future__ import annotations

import networkx as nx
import pandas as pd

from utils.data_loader import load_connections, load_stations, normalize_station_name


def build_graph(
    stations: pd.DataFrame | None = None,
    connections: pd.DataFrame | None = None,
) -> nx.Graph:
    stations = stations if stations is not None else load_stations()
    connections = connections if connections is not None else stations.attrs.get("connections")
    if connections is None:
        connections = load_connections()

    graph = nx.Graph()

    for _, station in stations.iterrows():
        station_name = normalize_station_name(station["station_name"])
        graph.add_node(
            station_name,
            station_id=station.get("station_id"),
            line=station.get("line", "Metro"),
            latitude=station.get("latitude"),
            longitude=station.get("longitude"),
            is_interchange=bool(station.get("is_interchange", False)),
        )

    for _, connection in connections.iterrows():
        source = normalize_station_name(connection["source"])
        target = normalize_station_name(connection["target"])
        avg_time = float(connection.get("avg_travel_time_min", 2.2))
        distance = float(connection.get("distance_km", 1.25))
        line = connection.get("line", "Metro")

        graph.add_edge(
            source,
            target,
            weight=avg_time,
            line=line,
            distance_km=distance,
            avg_travel_time_min=avg_time,
        )

    return graph
