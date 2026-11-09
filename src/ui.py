import streamlit as st


def apply_ui_theme():
    st.markdown(
        """
        <style>
            :root {
                --ink: #172b4d;
                --muted: #62748b;
                --line: #e3eaf3;
                --surface: #ffffff;
                --accent: #2563eb;
                --accent-dark: #1d4ed8;
                --canvas: #f4f7fb;
            }

            .stApp {
                background: var(--canvas);
                color: var(--ink);
            }
            .block-container {
                max-width: 1500px;
                padding: 2.25rem 3rem 3rem;
            }
            h1, h2, h3, h4, h5, h6 {
                color: var(--ink);
                letter-spacing: -0.025em;
            }
            p, li, label, [data-testid="stCaptionContainer"] {
                color: var(--muted);
            }
            a {
                color: var(--accent);
            }

            [data-testid="stSidebar"] {
                background: #fff;
                border-right: 1px solid var(--line);
            }
            [data-testid="stSidebar"] > div:first-child {
                padding-top: 1.5rem;
            }

            .enterprise-header, .op-header, .dash-header {
                color: var(--ink);
                font-size: clamp(1.7rem, 2.3vw, 2.25rem);
                font-weight: 750;
                letter-spacing: -0.045em;
                line-height: 1.2;
                margin-bottom: 0.45rem;
            }
            .enterprise-sub, .op-sub, .dash-sub {
                color: var(--muted);
                font-size: 0.98rem;
                line-height: 1.65;
                max-width: 900px;
                margin-bottom: 1.8rem;
            }
            .section-title {
                color: var(--ink);
                font-size: 1.22rem;
                font-weight: 700;
                letter-spacing: -0.025em;
                margin: 0.25rem 0 0.45rem;
            }
            .section-desc {
                color: var(--muted);
                font-size: 0.9rem;
                line-height: 1.55;
                margin-bottom: 1rem;
            }

            .kpi-container, .exec-card {
                height: 100%;
                min-height: 112px;
                background: var(--surface);
                border: 1px solid var(--line);
                border-top: 3px solid var(--accent);
                border-radius: 12px;
                box-shadow: 0 5px 16px rgba(23, 43, 77, 0.045);
                padding: 0.95rem 0.8rem;
                transition: transform 160ms ease, box-shadow 160ms ease;
            }
            .kpi-container:hover, .exec-card:hover, .portal-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 24px rgba(23, 43, 77, 0.09);
            }
            .kpi-num, .exec-val {
                color: var(--ink);
                font-size: clamp(1.15rem, 1.5vw, 1.75rem);
                font-weight: 750;
                letter-spacing: -0.04em;
                line-height: 1.2;
                font-feature-settings: "tnum";
                white-space: nowrap;
            }
            .kpi-title, .exec-lbl {
                color: var(--muted);
                font-size: 0.62rem;
                font-weight: 700;
                letter-spacing: 0.045em;
                line-height: 1.4;
                margin-top: 0.55rem;
                text-transform: uppercase;
                overflow-wrap: normal;
                word-break: normal;
            }

            .portal-card {
                height: 100%;
                background: var(--surface);
                border: 1px solid var(--line);
                border-radius: 14px;
                box-shadow: 0 5px 18px rgba(23, 43, 77, 0.05);
                padding: 1.5rem 1.6rem;
                transition: transform 160ms ease, box-shadow 160ms ease;
            }
            .portal-card h4 {
                color: var(--ink);
                font-size: 1.13rem;
                font-weight: 700;
                margin: 0 0 0.8rem;
            }
            .portal-card p, .portal-card li {
                color: var(--muted);
                font-size: 0.9rem;
                line-height: 1.65;
            }
            .portal-card ul {
                margin: 0.65rem 0 1.2rem;
                padding-left: 1.25rem;
            }
            .portal-card li {
                padding: 0.15rem 0;
            }
            .status-badge {
                display: inline-flex;
                align-items: center;
                padding: 0.38rem 0.75rem;
                border-radius: 999px;
                background: #ecfdf5;
                border: 1px solid #bbf7d0;
                color: #166534;
                font-size: 0.76rem;
                font-weight: 700;
            }
            .status-dot {
                width: 7px;
                height: 7px;
                border-radius: 50%;
                background: #16a34a;
                margin-right: 7px;
            }
            .callout-box {
                background: #eff6ff;
                border: 1px solid #dbeafe;
                border-left: 4px solid var(--accent);
                border-radius: 0 10px 10px 0;
                color: #334155;
                font-size: 0.91rem;
                line-height: 1.65;
                margin: 0.75rem 0 1.1rem;
                padding: 0.9rem 1.1rem;
            }

            [data-testid="stTabs"] [data-baseweb="tab-list"] {
                gap: 0.35rem;
                border-bottom: 1px solid var(--line);
            }
            [data-testid="stTabs"] [data-baseweb="tab"] {
                color: var(--muted);
                font-weight: 650;
                padding: 0.75rem 1rem;
            }
            [data-testid="stTabs"] [aria-selected="true"] {
                color: var(--accent-dark);
            }
            [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
                background-color: var(--accent);
                height: 3px;
                border-radius: 3px 3px 0 0;
            }

            .stButton > button, .stLinkButton > a, [data-testid="stPageLink"] a {
                border-radius: 9px;
                font-weight: 650;
                transition: background-color 140ms ease, border-color 140ms ease, transform 140ms ease;
            }
            .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
                background: var(--accent);
                border-color: var(--accent);
                color: #fff;
            }
            .stButton > button:hover, .stLinkButton > a:hover {
                transform: translateY(-1px);
                border-color: var(--accent);
            }
            input, textarea, [data-baseweb="select"] > div {
                border-radius: 8px !important;
            }
            [data-testid="stDataFrame"], [data-testid="stTable"], [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"] {
                border: 1px solid var(--line);
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 14px rgba(23, 43, 77, 0.035);
            }
            [data-testid="stDataFrame"] {
                background: var(--surface);
            }
            hr {
                border-color: var(--line);
            }
            div[data-testid="stAlert"] {
                border-radius: 10px;
            }
            :focus-visible {
                outline: 2px solid var(--accent);
                outline-offset: 2px;
            }

            @media (max-width: 900px) {
                .block-container {
                    padding: 1.5rem 1.25rem 2rem;
                }
                .portal-card {
                    padding: 1.2rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
