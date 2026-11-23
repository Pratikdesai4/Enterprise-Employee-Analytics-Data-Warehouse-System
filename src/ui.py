import streamlit as st


def apply_ui_theme():
    st.markdown(
        """
        <style>
            :root {
                --ink: #102a43;
                --muted: #627d98;
                --line: #d9e2ec;
                --surface: #ffffff;
                --accent: #2563eb;
                --accent-dark: #1d4ed8;
                --teal: #0f9f9a;
                --canvas: #f5f8fc;
            }

            .stApp {
                background: var(--canvas);
                color: var(--ink);
            }
            .block-container {
                max-width: 1540px;
                padding: 2.6rem 3.2rem 3.5rem;
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
                background: linear-gradient(180deg, #102a43 0%, #163b5c 100%);
                border-right: 1px solid var(--line);
            }
            [data-testid="stSidebar"] > div:first-child {
                padding: 1.4rem 1rem 1.5rem;
            }
            [data-testid="stSidebar"] * {
                color: #d9e8f5;
            }
            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3 {
                color: #ffffff;
            }
            [data-testid="stSidebar"] hr {
                border-color: rgba(255,255,255,0.16);
            }
            [data-testid="stSidebar"] .stMarkdown p {
                line-height: 1.55;
            }
            [data-testid="stSidebar"] .sidebar-filter-label {
                color: #7dd3fc !important;
                font-size: 0.875rem;
                font-weight: 400;
                line-height: 1.5;
                margin: 0 0 0.2rem;
            }

            .enterprise-header, .op-header, .dash-header {
                color: var(--ink);
                font-size: clamp(1.7rem, 2.3vw, 2.25rem);
                font-weight: 750;
                letter-spacing: -0.045em;
                line-height: 1.2;
                margin-bottom: 0.5rem;
            }
            .enterprise-sub, .op-sub, .dash-sub {
                color: var(--muted);
                font-size: 0.98rem;
                line-height: 1.65;
                max-width: 900px;
                margin-bottom: 2rem;
            }
            .section-title {
                color: var(--ink);
                font-size: 1.22rem;
                font-weight: 700;
                letter-spacing: -0.025em;
                margin: 1.7rem 0 0.45rem;
            }
            .section-desc {
                color: var(--muted);
                font-size: 0.9rem;
                line-height: 1.55;
                margin-bottom: 1rem;
            }

            .kpi-container, .exec-card {
                height: 100%;
                min-height: 122px;
                background: var(--surface);
                border: 1px solid var(--line);
                border-top: 3px solid var(--accent);
                border-radius: 14px;
                box-shadow: 0 8px 24px rgba(16, 42, 67, 0.07);
                padding: 1.1rem 1rem;
                transition: transform 160ms ease, box-shadow 160ms ease;
            }
            .kpi-container:hover, .exec-card:hover, .portal-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 24px rgba(23, 43, 77, 0.09);
            }
            .kpi-num, .exec-val {
                color: var(--ink);
                font-size: clamp(1.2rem, 1.6vw, 1.85rem);
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
                padding: 1.6rem 1.7rem;
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
            .brand-lockup {
                padding: 0.35rem 0.4rem 1.1rem;
            }
            .brand-mark {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 36px;
                height: 36px;
                margin-bottom: 0.65rem;
                border-radius: 10px;
                background: #2dd4bf;
                color: #102a43;
                font-size: 1.1rem;
                font-weight: 800;
            }
            .brand-name {
                color: #ffffff;
                font-size: 1rem;
                font-weight: 750;
                letter-spacing: -0.02em;
            }
            .brand-caption {
                color: #a9c1d6;
                font-size: 0.72rem;
                margin-top: 0.2rem;
            }
            .page-eyebrow {
                color: var(--accent);
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.12em;
                margin-bottom: 0.4rem;
                text-transform: uppercase;
            }
            .hero-strip {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                background: linear-gradient(105deg, #eaf3ff 0%, #f8fbff 65%);
                border: 1px solid #d5e6fa;
                border-radius: 14px;
                margin: 0.6rem 0 1.5rem;
                padding: 1rem 1.2rem;
            }
            .hero-strip strong { color: var(--ink); }
            .hero-strip span { color: var(--muted); font-size: 0.85rem; }
            .mini-label {
                color: var(--muted);
                font-size: 0.72rem;
                font-weight: 750;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }
            .form-shell {
                background: rgba(255,255,255,0.72);
                border: 1px solid var(--line);
                border-radius: 14px;
                padding: 0.35rem 1rem 0.8rem;
            }
            .audit-badge {
                display: inline-block;
                padding: 0.25rem 0.55rem;
                border-radius: 999px;
                background: #e6fffa;
                color: #087f75;
                font-size: 0.72rem;
                font-weight: 750;
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
                .hero-strip {
                    align-items: flex-start;
                    flex-direction: column;
                }
                .portal-card {
                    padding: 1.2rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(eyebrow: str, title: str, description: str):
    """Keep the sidebar hook available without rendering a branding block."""
    return None


def render_page_header(eyebrow: str, title: str, description: str):
    """Render a consistent page title block."""
    st.markdown(f'<div class="page-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="enterprise-header">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="enterprise-sub">{description}</div>', unsafe_allow_html=True)


def style_plotly(fig, height: int = 390):
    """Apply the shared light chart treatment without changing chart data."""
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Arial, sans-serif", color="#486581", size=11),
        title_font=dict(color="#102a43", size=14),
        margin=dict(l=12, r=12, t=46, b=12),
        legend=dict(bgcolor="rgba(255,255,255,0.8)", borderwidth=0),
        hoverlabel=dict(bgcolor="#102a43", font_color="#ffffff"),
        xaxis=dict(showgrid=False, zeroline=False, linecolor="#d9e2ec"),
        yaxis=dict(gridcolor="#edf2f7", zeroline=False, linecolor="#d9e2ec"),
    )
    return fig
