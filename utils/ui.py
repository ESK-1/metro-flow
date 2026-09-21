from __future__ import annotations

import streamlit as st


def configure_page(title: str = "MetroFlow AI") -> None:
    st.set_page_config(
        page_title=title,
        page_icon="M",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_styles()


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --metro-bg: #f7f9fb;
            --metro-ink: #172033;
            --metro-muted: #5a6577;
            --metro-line: #dde4ee;
            --metro-card: #ffffff;
            --metro-teal: #0f766e;
            --metro-red: #c2410c;
            --metro-yellow: #b7791f;
            --metro-green: #15803d;
        }

        .stApp {
            background: linear-gradient(180deg, #f8fbff 0%, #eef4f8 100%);
            color: var(--metro-ink);
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }

        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2.5rem;
            max-width: 1240px;
        }

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.85rem 0 1.3rem;
            border-bottom: 1px solid var(--metro-line);
            margin-bottom: 1.4rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 800;
            font-size: 1.35rem;
            color: var(--metro-ink);
        }

        .brand-mark {
            width: 42px;
            height: 42px;
            border-radius: 8px;
            display: grid;
            place-items: center;
            background: #0f766e;
            color: #fff;
            font-weight: 900;
        }

        .navlinks a {
            color: var(--metro-muted);
            text-decoration: none;
            margin-left: 1rem;
            font-weight: 650;
        }

        .hero {
            padding: 1.45rem 0 1rem;
        }

        .hero h1 {
            font-size: clamp(2.1rem, 5vw, 4.3rem);
            line-height: 1.02;
            letter-spacing: 0;
            margin: 0 0 0.7rem;
            color: #111827;
        }

        .hero p {
            color: var(--metro-muted);
            font-size: 1.08rem;
            line-height: 1.55;
            max-width: 760px;
            margin: 0;
        }

        .section-title {
            font-size: 1.08rem;
            font-weight: 800;
            color: #111827;
            margin: 1.35rem 0 0.7rem;
        }

        .metric-card, .info-card, .ai-card {
            background: var(--metro-card);
            border: 1px solid var(--metro-line);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
            height: 100%;
        }

        .info-card {
            line-height: 1.55;
        }

        .metric-label {
            color: var(--metro-muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-weight: 800;
        }

        .metric-value {
            color: #111827;
            font-size: 1.55rem;
            line-height: 1.15;
            font-weight: 850;
            margin-top: 0.3rem;
        }

        .route-pill {
            display: inline-block;
            background: #e6f4f1;
            color: #115e59;
            padding: 0.45rem 0.65rem;
            border-radius: 8px;
            font-weight: 750;
            margin: 0.2rem 0.3rem 0.2rem 0;
        }

        .route-sequence {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.42rem;
            margin-top: 0.55rem;
        }

        .route-step {
            background: var(--route-line-bg, #e6f4f1);
            color: #17324d;
            border-left: 5px solid var(--route-line, #0f766e);
            padding: 0.45rem 0.7rem;
            border-radius: 8px;
            font-weight: 800;
            box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.14);
        }

        .route-arrow {
            width: 1.75rem;
            height: 1.75rem;
            display: inline-grid;
            place-items: center;
            flex: 0 0 auto;
            background: #f1f5f9;
            border: 1px solid #d8e1ec;
            border-radius: 999px;
            color: #0f766e;
            font-weight: 900;
            font-size: 1.05rem;
            line-height: 1;
        }

        .soft-note {
            color: #5a6577;
            margin-top: 0.45rem;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--metro-line);
            border-radius: 8px;
            overflow: hidden;
        }

        .stButton > button {
            border-radius: 8px;
            border: 0;
            background: #0f766e;
            color: white;
            font-weight: 800;
            height: 2.85rem;
        }

        .stButton > button:hover {
            border: 0;
            background: #115e59;
            color: white;
        }

        .ai-card {
            border-left: 5px solid #0f766e;
            white-space: pre-line;
            color: #243145;
            line-height: 1.58;
        }

        .ai-rec-card {
            white-space: normal;
            display: grid;
            gap: 0.75rem;
        }

        .ai-rec-row {
            display: grid;
            grid-template-columns: 3.2rem minmax(0, 1fr);
            gap: 0.75rem;
            align-items: start;
        }

        .ai-rec-icon {
            background: #e6f4f1;
            color: #115e59;
            border: 1px solid #b7e1d8;
            border-radius: 8px;
            font-size: 0.72rem;
            font-weight: 900;
            min-height: 2rem;
            display: grid;
            place-items: center;
        }

        @media (max-width: 760px) {
            .topbar {
                align-items: flex-start;
                flex-direction: column;
            }

            .navlinks a {
                margin-left: 0;
                margin-right: 0.9rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def top_nav() -> None:
    st.markdown(
        """
        <div class="topbar">
            <div class="brand"><div class="brand-mark">M</div><div>MetroFlow AI</div></div>
            <div class="navlinks">
                <a href="/" target="_self">Home</a>
                <a href="/network_explorer" target="_self">Metro Network Explorer</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
