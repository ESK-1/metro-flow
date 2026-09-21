from __future__ import annotations

# Single source of truth for crowd classification thresholds.
# Low: 0–39  |  Medium: 40–69  |  High: 70–100
LOW_MAX: int = 39
MEDIUM_MAX: int = 69

# Single source of truth for metro line colours.
# Used by both the Suggested Route pills (app.py) and the Network Explorer
# (visualizations/network_graph.py).  Blue Line Branch uses the same blue as
# Blue Line so the two segments read as one continuous line in the route strip.
LINE_COLORS: dict[str, str] = {
    "Yellow Line": "#eab308",
    "Blue Line": "#2563eb",
    "Blue Line Branch": "#2563eb",
    "Red Line": "#dc2626",
    "Violet Line": "#7c3aed",
    "Green Line": "#16a34a",
    "Green Line Branch": "#22c55e",
    "Pink Line": "#ec4899",
    "Magenta Line": "#d946ef",
    "Orange Line": "#f97316",
    "Grey Line": "#64748b",
    "Metro": "#475569",
}
