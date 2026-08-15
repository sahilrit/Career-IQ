"""Dashboard visual theme.

Design language adapted from the Raycast DESIGN.md analysis (see
``awesome-design-md/design-md/raycast/DESIGN.md``): a single dark surface
mode, a canvas -> surface -> surface-elevated -> surface-card ladder for
elevation instead of drop shadows, hairline 1px borders, Inter with the
ss03 stylistic set, and a white pill as the only primary action color.
"""

from __future__ import annotations

import streamlit as st

CANVAS = "#07080a"
SURFACE = "#0d0d0d"
SURFACE_ELEVATED = "#101111"
SURFACE_CARD = "#121212"
HAIRLINE = "#242728"
HAIRLINE_STRONG = "rgba(255,255,255,0.16)"
INK = "#f4f4f6"
BODY = "#cdcdcd"
MUTE = "#9c9c9d"
ASH = "#6a6b6c"

_BADGE_TONES = {
    "mute": ("rgba(156,156,157,0.15)", MUTE),
    "blue": ("rgba(87,193,255,0.15)", "#57c1ff"),
    "red": ("rgba(255,97,97,0.15)", "#ff6161"),
    "green": ("rgba(89,212,153,0.15)", "#59d499"),
    "yellow": ("rgba(255,197,51,0.15)", "#ffc533"),
}

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-feature-settings: "calt", "kern", "liga", "ss03";
}}

.stApp {{
    background-color: {CANVAS};
}}

[data-testid="stHeader"] {{
    background-color: {CANVAS};
}}

[data-testid="stSidebar"] {{
    background-color: {SURFACE};
    border-right: 1px solid {HAIRLINE};
}}

h1, h2, h3, h4 {{
    color: {INK} !important;
    font-weight: 500 !important;
    letter-spacing: 0.2px;
}}
h1 {{ font-size: 32px !important; }}

p, li, label, .stMarkdown, [data-testid="stMarkdownContainer"] {{
    color: {BODY};
}}

[data-testid="stCaptionContainer"] {{
    color: {MUTE} !important;
}}

/* metric cards: canvas -> surface elevation, hairline border, no shadow */
[data-testid="stMetric"] {{
    background: {SURFACE};
    border: 1px solid {HAIRLINE};
    border-radius: 10px;
    padding: 16px 20px;
}}
[data-testid="stMetricValue"] {{ color: {INK} !important; font-weight: 600 !important; }}
[data-testid="stMetricLabel"] {{ color: {MUTE} !important; font-size: 13px !important; }}

/* primary CTA: the one white pill */
.stButton > button, .stFormSubmitButton > button {{
    background: #ffffff !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
}}
.stButton > button:hover, .stFormSubmitButton > button:hover {{
    background: #e8e8e8 !important;
    color: #000000 !important;
}}

/* inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
[data-baseweb="select"] > div, [data-baseweb="input"] {{
    background: {SURFACE_ELEVATED} !important;
    border: 1px solid {HAIRLINE} !important;
    border-radius: 8px !important;
    color: {INK} !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: {HAIRLINE_STRONG} !important;
    box-shadow: none !important;
}}

/* expanders and forms read as surface cards */
[data-testid="stExpander"], [data-testid="stForm"] {{
    background: {SURFACE};
    border: 1px solid {HAIRLINE} !important;
    border-radius: 10px !important;
}}

/* tabs -> pill-tab / pill-tab-active */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 1px solid {HAIRLINE};
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    border-radius: 9999px 9999px 0 0;
    color: {BODY};
    padding: 6px 16px;
}}
.stTabs [aria-selected="true"] {{
    background: {SURFACE_ELEVATED} !important;
    color: {INK} !important;
}}

hr {{ border-color: {HAIRLINE} !important; }}
</style>
"""


def inject_theme() -> None:
    """Apply the dashboard's dark theme CSS to the current page."""
    st.markdown(_CSS, unsafe_allow_html=True)


def badge(text: str, tone: str = "mute") -> str:
    """Small pill-badge HTML. ``tone`` in {mute, blue, red, green, yellow}."""
    bg, fg = _BADGE_TONES.get(tone, _BADGE_TONES["mute"])
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f"border-radius:4px;font-size:12px;font-weight:500;"
        f'font-family:Inter,sans-serif;">{text}</span>'
    )
