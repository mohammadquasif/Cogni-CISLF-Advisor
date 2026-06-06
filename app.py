"""
app.py — Cogni CISLF Advisor v2 | Multi-Mode Streamlit Application
===================================================================
Supports two analysis modes:
  🤖 AI Mode    — LLM-powered analysis (Google Gemini / OpenAI)
  📋 Manual Mode — Rule-based analysis using a 20-question questionnaire
                    (no API key required)

Credential Security:
  - API keys can be saved to an AES-256 encrypted local SQLite database
  - Keys are machine-specific and never leave the device
  - Session-only mode also supported (no persistence)

Three pages:
  🔍 Analysis      — Run AI or Manual CISLF assessment
  🔑 Credentials  — Manage locally stored API keys
  ℹ️  About        — Framework information and citation

CISLF Framework — Developed by Mohammad Quasif, DBA Candidate
Kennedy University of Baptist, France
"""

import os
import datetime

import streamlit as st
from dotenv import load_dotenv

# Internal modules
from cislf_engine import (
    CISLF_PILLARS,
    build_system_prompt,
    build_user_prompt,
    validate_report,
    get_maturity_color,
    parse_cislf_report,
)
from llm_providers import get_provider, LLMProviderError
from local_storage import (
    save_credential,
    load_credential,
    delete_credential,
    list_stored_credentials,
    credential_exists,
    save_preference,
    load_preference,
    get_db_info,
)
from manual_engine import (
    ALL_QUESTION_IDS,
    build_manual_report,
    get_maturity_label,
    calculate_all_scores,
    get_dynamic_questions,
)

# ---------------------------------------------------------------------------
# Environment (local dev fallback)
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Credential key names used in the local DB
# ---------------------------------------------------------------------------
CRED_GEMINI  = "gemini_api_key"
CRED_OPENAI  = "openai_api_key"
CRED_DEEPSEEK = "deepseek_api_key"
PREF_PROVIDER = "last_provider"
PREF_MODEL    = "last_model"
PREF_MODE     = "analysis_mode"

# ---------------------------------------------------------------------------
# Module-level AI job results store
# Using @st.cache_resource ensures this dict survives Streamlit reruns.
# Keys: job_id (str) -> {"status": "running"|"done"|"error", "report", "error"}
# ---------------------------------------------------------------------------
import uuid as _uuid

@st.cache_resource
def get_job_store():
    return {}

AI_JOBS = get_job_store()

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Cogni CISLF Advisor | AI Strategic Leadership Consultant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**Cogni CISLF Advisor v2**\n\n"
            "Powered by the CISLF Framework.\n"
            "Developed by Mohammad Quasif, DBA | Kennedy University of Baptist, France."
        )
    },
)

import base64

def get_image_base64(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                return f"data:image/png;base64,{encoded_string}"
        except Exception:
            pass
    return ""

# ---------------------------------------------------------------------------
# CSS — Professional Green Theme
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4, h5, h6 { font-family: 'Plus Jakarta Sans', sans-serif; }

.stApp { background-color: #F4F7F5; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #091E12 0%, #112F21 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}
[data-testid="stSidebar"] * { color: #E8F5E9 !important; }
[data-testid="stSidebar"] .stSelectbox > div > div { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.15); }

/* Custom Sidebar Navigation Menu styling (converting radios to professional buttons) */
div[data-testid="stSidebar"] [role="radiogroup"] {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    padding: 0.5rem 0;
}
div[data-testid="stSidebar"] [role="radiogroup"] label {
    background-color: transparent !important;
    border-radius: 8px !important;
    padding: 0.65rem 0.9rem !important;
    margin-bottom: 0.15rem !important;
    display: flex !important;
    align-items: center !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
    color: #D8F3DC !important;
    border-left: 3px solid transparent !important;
}
/* Hide the default radio circle inputs and their wrappers */
div[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
    display: none !important;
}
/* Selected state for sidebar menu buttons */
div[data-testid="stSidebar"] [role="radiogroup"] label:has(input[type="radio"]:checked) {
    background: rgba(255, 255, 255, 0.09) !important;
    color: #FFFFFF !important;
    border-left: 3px solid #52B788 !important;
    font-weight: 700 !important;
    box-shadow: inset 1px 0 0 rgba(255,255,255,0.05);
    border-radius: 0 8px 8px 0 !important;
    padding-left: 0.75rem !important;
}
div[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.05) !important;
    color: #FFFFFF !important;
}

/* Header banner */
.cislf-header {
    background: linear-gradient(135deg, rgba(27, 67, 50, 0.98) 0%, rgba(13, 40, 24, 0.99) 100%);
    color: white; padding: 2rem 2.2rem; border-radius: 20px;
    margin-bottom: 2rem;
    border: 1px solid rgba(212, 175, 55, 0.15);
    box-shadow: 0 12px 36px rgba(13, 40, 24, 0.2);
}
.cislf-header h1 { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2.4rem; font-weight: 800; margin: 0; color: white; letter-spacing: -0.5px; }
.cislf-header p  { font-size: 1.05rem; color: #D8F3DC; margin: 0.4rem 0 0; }
.cislf-header .cite { font-size: 0.8rem; color: #95D5B2; margin-top: 0.85rem; font-style: italic; opacity: 0.85; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 0.75rem; }

/* Mode selector tabs */
.mode-tab-active {
    background: #1B4332; color: white !important; border-radius: 8px;
    padding: 0.5rem 1.2rem; font-weight: 600; font-size: 0.95rem;
}
.mode-tab-inactive {
    background: #D8F3DC; color: #1B4332 !important; border-radius: 8px;
    padding: 0.5rem 1.2rem; font-weight: 500; font-size: 0.95rem; border: 1px solid #95D5B2;
}

/* Pillar cards */
.pillar-card {
    background: linear-gradient(135deg, #E8F5E9 0%, #D8F3DC 100%); 
    border-left: 5px solid #2D6A4F; 
    border-radius: 12px;
    padding: 1.1rem 1.3rem; 
    margin-bottom: 0.6rem;
    font-size: 0.92rem; 
    color: #1B4332;
    box-shadow: 0 4px 12px rgba(27,67,50,0.04);
    transition: all 0.3s ease;
}
.pillar-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(27,67,50,0.08);
    border-left-color: #52B788;
}
.pillar-card strong { display: block; font-size: 1.05rem; margin-bottom: 0.3rem; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #1B4332; }

/* Question card */
.question-card {
    background: white; border: 1px solid rgba(45, 106, 79, 0.12); border-radius: 12px;
    padding: 1.2rem 1.4rem; margin-bottom: 1rem;
    box-shadow: 0 4px 15px rgba(27,67,50,0.03);
    transition: all 0.3s ease;
}
.question-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(27,67,50,0.07);
    border-color: rgba(45, 106, 79, 0.3);
}
.question-text { font-weight: 600; color: #1B4332; font-size: 0.98rem; margin-bottom: 0.4rem; }
.question-weight { font-size: 0.76rem; color: #6c757d; }

/* Report box */
.report-box {
    background: white; border: 1px solid #D8F3DC; border-radius: 12px;
    padding: 1.5rem 2rem; font-family: 'Courier New', monospace;
    font-size: 0.86rem; line-height: 1.75; color: #1a1a1a;
    white-space: pre-wrap; box-shadow: 0 2px 12px rgba(27,67,50,0.08);
    overflow-x: auto;
}

/* Credential card */
.cred-card {
    background: white; border: 1px solid #D8F3DC; border-radius: 10px;
    padding: 1rem 1.3rem; margin-bottom: 0.6rem; display: flex;
    align-items: center; gap: 1rem;
    box-shadow: 0 1px 4px rgba(27,67,50,0.06);
}
.cred-key { font-weight: 600; color: #1B4332; flex: 1; }
.cred-date { font-size: 0.8rem; color: #6c757d; }
.badge-saved   { background: #D8F3DC; color: #1B4332; font-size: 0.78rem; padding: 0.25rem 0.65rem; border-radius: 20px; border: 1px solid #95D5B2; font-weight: 600; }
.badge-session { background: #FFF3CD; color: #856404; font-size: 0.78rem; padding: 0.25rem 0.65rem; border-radius: 20px; border: 1px solid #FFCA2C; font-weight: 600; }
.security-note {
    background: linear-gradient(135deg, #D8F3DC, #B7E4C7);
    border: 1px solid #95D5B2; border-radius: 10px;
    padding: 1rem 1.3rem; color: #1B4332; font-size: 0.88rem;
}

/* Buttons styling override */
div.stButton > button {
    background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%);
    color: white; border: none; border-radius: 10px; font-weight: 600;
    padding: 0.65rem 1.5rem; font-size: 0.98rem; transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(27,67,50,0.15);
    font-family: 'Plus Jakarta Sans', sans-serif;
    width: 100%;
}
div.stButton > button:hover {
    background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%);
    box-shadow: 0 6px 20px rgba(27,67,50,0.25); 
    transform: translateY(-2px);
    color: white;
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%);
    color: white;
}
div.stButton > button[kind="secondary"] {
    background: #FFFFFF;
    color: #1B4332;
    border: 1px solid rgba(45, 106, 79, 0.2);
    box-shadow: none;
}
div.stButton > button[kind="secondary"]:hover {
    background: #F4F7F5;
    color: #2D6A4F;
    border-color: #2D6A4F;
    transform: translateY(-2px);
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #2D6A4F 0%, #52B788 100%) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; font-size: 0.95rem !important; padding: 0.6rem 1.4rem !important;
    box-shadow: 0 4px 12px rgba(45,106,79,0.18) !important;
    transition: all 0.3s ease !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #40916C 0%, #74C69D 100%) !important;
    box-shadow: 0 6px 20px rgba(45,106,79,0.28) !important;
    transform: translateY(-2px) !important;
}

/* Text areas and inputs */
.stTextArea textarea { border: 1.5px solid rgba(45,106,79,0.2); border-radius: 12px; font-size: 0.95rem; padding: 0.8rem; }
.stTextArea textarea:focus { border-color: #1B4332; box-shadow: 0 0 0 1px #1B4332; }

div[data-testid="stExpander"] {
    background: white; border: 1px solid rgba(45,106,79,0.12); border-radius: 12px;
    margin-bottom: 0.75rem; box-shadow: 0 2px 10px rgba(27,67,50,0.03);
}

/* Footer */
.cislf-footer {
    text-align: center; padding: 1.8rem 0 1rem; color: #6c757d;
    font-size: 0.82rem; border-top: 1px solid rgba(45,106,79,0.12); margin-top: 2.5rem;
}

/* Scorecard progress bar */
.progress-track {
    background: #E9ECEF; border-radius: 8px; height: 14px;
    margin-top: 0.45rem; overflow: hidden;
}
.progress-fill {
    height: 100%; border-radius: 8px; transition: width 0.4s ease;
}

/* ── Stepper Wizard ──────────────────────────────────────────────────── */
.stepper-progress-bar {
    background: #E9ECEF; border-radius: 100px; height: 8px;
    overflow: hidden; margin: 0.5rem 0 1.5rem 0;
}
.stepper-progress-fill {
    height: 100%; border-radius: 100px;
    background: linear-gradient(90deg, #1B4332 0%, #52B788 100%);
    transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.stepper-nav {
    display: flex; align-items: center; justify-content: center;
    gap: 0; margin-bottom: 2rem; overflow-x: auto;
}
.stepper-item {
    display: flex; flex-direction: column; align-items: center;
    flex: 1; min-width: 70px; position: relative;
}
.stepper-item::before {
    content: ''; position: absolute; top: 16px; left: 50%; right: -50%;
    height: 2px; background: #D8F3DC; z-index: 0;
}
.stepper-item:last-child::before { display: none; }
.stepper-dot {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700; z-index: 1;
    position: relative; transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.stepper-dot-done   { background: #1B4332; color: white; }
.stepper-dot-active { background: #52B788; color: white; box-shadow: 0 0 0 4px rgba(82,183,136,0.25); }
.stepper-dot-todo   { background: #E9ECEF; color: #6c757d; box-shadow: none; }
.stepper-label { font-size: 0.68rem; color: #6c757d; margin-top: 0.3rem; text-align: center; font-weight: 600; max-width: 70px; }
.stepper-label-active { color: #1B4332; }

.wizard-card {
    background: white; border-radius: 16px;
    border: 1px solid rgba(45,106,79,0.10);
    padding: 2rem 2.2rem; margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(27,67,50,0.04);
}
.wizard-pillar-header {
    display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;
    padding-bottom: 1rem; border-bottom: 2px solid #E8F5E9;
}
.wizard-pillar-icon {
    width: 56px; height: 56px; border-radius: 14px;
    background: linear-gradient(135deg, #D8F3DC, #B7E4C7);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.8rem; flex-shrink: 0;
}
.wizard-pillar-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.3rem; font-weight: 800; color: #1B4332; margin: 0;
}
.wizard-pillar-sub { font-size: 0.85rem; color: #6c757d; margin: 0.2rem 0 0 0; }

.question-block {
    background: #FAFFFE; border: 1.5px solid rgba(45,106,79,0.08);
    border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 1.2rem;
    transition: border-color 0.2s ease;
}
.question-block:hover { border-color: rgba(45,106,79,0.25); }
.question-num { font-size: 0.7rem; font-weight: 700; color: #52B788; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.35rem; }
.question-title { font-weight: 600; color: #1B4332; font-size: 0.97rem; line-height: 1.45; margin-bottom: 0.2rem; }
.question-wt { font-size: 0.73rem; color: #6c757d; }

.live-score-chip {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: linear-gradient(135deg, #D8F3DC, #B7E4C7);
    color: #1B4332; padding: 0.35rem 0.9rem;
    border-radius: 100px; font-size: 0.82rem; font-weight: 700;
    border: 1px solid #95D5B2; margin-bottom: 1.2rem;
}

.review-pillar-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.9rem 1rem; border-radius: 10px; margin-bottom: 0.6rem;
    background: white; border: 1px solid rgba(45,106,79,0.08);
}
.review-pillar-name { font-weight: 600; color: #1B4332; font-size: 0.93rem; }
.review-score-bar-wrap { flex: 1; margin: 0 1.2rem; }
.review-score-label { font-weight: 700; font-size: 0.98rem; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------
def init_session():
    """Initialise all session state keys with defaults."""
    defaults = {
        # Credentials (loaded from local storage or env on first run)
        "gemini_key":      "",
        "openai_key":      "",
        "deepseek_key":    "",
        # Navigation
        "page":            "📊 Dashboard",
        # Analysis mode
        "analysis_mode":   "🤖 AI Mode",
        # LLM config
        "provider":        "Google Gemini",
        "model":           "gemini-1.5-flash",
        # Generated report
        "report_text":     None,
        "report_source":   None,  # "AI" or "Manual"
        # Manual questionnaire answers
        "manual_answers":  {},
        # Credential save preference (per key)
        "save_gemini_locally":  False,
        "save_openai_locally":  False,
        # AI generation background thread state
        "ai_gen_thread":   None,
        "ai_gen_result":   None,
        "ai_gen_model":    None,
        "ai_gen_provider": None,
        # Initialised flag
        "_init_done":      False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if not st.session_state["_init_done"]:
        # Load API keys from local storage (if saved previously)
        stored_gemini = load_credential(CRED_GEMINI)
        stored_openai = load_credential(CRED_OPENAI)
        stored_deepseek = load_credential(CRED_DEEPSEEK)
        if stored_gemini:
            st.session_state["gemini_key"] = stored_gemini
        elif os.getenv("GEMINI_API_KEY"):
            st.session_state["gemini_key"] = os.getenv("GEMINI_API_KEY", "")
        if stored_openai:
            st.session_state["openai_key"] = stored_openai
        elif os.getenv("OPENAI_API_KEY"):
            st.session_state["openai_key"] = os.getenv("OPENAI_API_KEY", "")
        if stored_deepseek:
            st.session_state["deepseek_key"] = stored_deepseek
        elif os.getenv("DEEPSEEK_API_KEY"):
            st.session_state["deepseek_key"] = os.getenv("DEEPSEEK_API_KEY", "")

        # Load preferences
        saved_provider = load_preference(PREF_PROVIDER, "Google Gemini")
        st.session_state["provider"] = saved_provider

        saved_model = load_preference(PREF_MODEL, "gemini-1.5-flash")
        st.session_state["model"] = saved_model

        saved_mode = load_preference(PREF_MODE, "🤖 AI Mode")
        if saved_mode in ("🤖 AI Mode", "📋 Manual Mode"):
            st.session_state["analysis_mode"] = saved_mode

        st.session_state["_init_done"] = True


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def render_sidebar():
    """Render sidebar navigation."""
    # Logo Brand Card
    if os.path.exists("assets/cogni_logo.png"):
        logo_b64 = get_image_base64("assets/cogni_logo.png")
        st.sidebar.markdown(f"""
        <div style="text-align: center; padding: 1.2rem 0.5rem 0.8rem; margin-bottom: 0.8rem; border-radius: 12px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05);">
            <img src="{logo_b64}" style="width: 68px; height: 68px; border-radius: 10px; margin-bottom: 0.6rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.15rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.2px;">Cogni CISLF</div>
            <div style="font-size: 0.72rem; color: #95D5B2; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 0.15rem;">Strategic Advisor</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("## 🧠 Cogni CISLF Advisor")

    st.sidebar.markdown("---")

    # ── Page Navigation ───────────────────────────────────────────────────
    st.sidebar.markdown("<p style='font-size:0.75rem;color:#85D2B2;font-weight:700;margin-bottom:0.4rem;letter-spacing:0.5px;'>NAVIGATION</p>", unsafe_allow_html=True)
    options = [
        "📋 Manual Assessment",
        "📊 Dashboard",
        "🤖 AI Consultation",
        "⚙️ Setup & Settings",
        "ℹ️ About & Reference"
    ]
    current_page = st.session_state.get("page", "📊 Dashboard")
    if current_page not in options:
        current_page = options[0]

    # Decouple key from session_state to allow programmatic redirection without StreamlitAPIException
    selected_page = st.sidebar.radio(
        "Go to",
        options=options,
        index=options.index(current_page),
        label_visibility="collapsed",
    )

    if selected_page != current_page:
        st.session_state["page"] = selected_page
        st.rerun()

    st.sidebar.markdown("---")

    # Compact attribution footer inside the sidebar
    st.sidebar.markdown(
        "<div style='opacity:0.75;font-size:0.75rem;line-height:1.4; color:#D8F3DC;'>"
        "<b>CISLF Framework</b><br>"
        "Developed by Mohammad Quasif, DBA Candidate<br>"
        "Kennedy University of Baptist, France"
        "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def render_header():
    logo_base64 = get_image_base64("assets/cogni_logo.png")
    if logo_base64:
        logo_html = f'<img src="{logo_base64}" style="height: 60px; margin-right: 1.2rem; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">'
    else:
        logo_html = '<span style="font-size: 2.2rem; margin-right: 1rem;">🧠</span>'

    st.markdown(f"""
    <div class="cislf-header">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            {logo_html}
            <div>
                <h1 style="margin: 0; line-height: 1.1; color: white;">Cogni CISLF Advisor</h1>
                <p style="margin: 0.2rem 0 0 0; font-size: 0.95rem; color: #D8F3DC; font-weight: 500;">AI Strategic Leadership Consultant | Powered by the CISLF Framework</p>
            </div>
        </div>
        <p class="cite">
            Quasif, M. (2025). Strategic Leadership for AI-Driven Business Transformation:
            A Cross-Industry Framework for Technology Executives.
            DBA Thesis. Kennedy University of Baptist, France.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Pillar Cards
# ---------------------------------------------------------------------------
def render_pillar_cards():
    st.markdown("#### The Four CISLF Pillars")
    icons = ["🎯", "🔗", "🏗️", "⚖️"]
    cols  = st.columns(4)
    for col, pillar, icon in zip(cols, CISLF_PILLARS, icons):
        with col:
            st.markdown(
                f'<div class="pillar-card"><strong>{icon} Pillar {pillar["number"]}</strong>'
                f'{pillar["title"]}</div>',
                unsafe_allow_html=True,
            )

# ============================================================================
# PAGE: Analysis
# ============================================================================

@st.cache_data(show_spinner=False)
def generate_pdf_from_markdown(markdown_text: str, p1: float, p2: float, p3: float, p4: float, source: str) -> bytes:
    """Convert raw markdown text into a PDF with base64 embedded charts and full HTML layout."""
    import tempfile
    import os
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    from cislf_engine import get_maturity_color, parse_cislf_report
    from pdf_generator import generate_premium_pdf

    # ── Generate chart images ──────────────────────────────────────────────────
    scores = [p1, p2, p3, p4]
    categories = ['Leadership Mindset', 'Biz-Tech Alignment', 'Capability & Culture', 'Responsible AI']

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=scores + [scores[0]], theta=categories + [categories[0]],
        fill='toself', fillcolor='rgba(82, 183, 136, 0.35)',
        line=dict(color='#1B4332', width=2), name='CISLF'
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(color='#6c757d'))),
        showlegend=False, margin=dict(l=30, r=30, t=30, b=30), height=380, width=460,
        paper_bgcolor='white'
    )

    df = pd.DataFrame({'Pillar': ['P1: Leadership', 'P2: Alignment', 'P3: Culture', 'P4: Governance'], 'Score': scores})
    df['Color'] = [get_maturity_color(s) for s in scores]
    fig_bar = px.bar(df, x='Score', y='Pillar', orientation='h', text='Score',
                     color='Pillar', color_discrete_sequence=df['Color'].tolist())
    fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside',
                          marker_line_color='#1B4332', marker_line_width=1.5)
    fig_bar.update_layout(
        xaxis=dict(range=[0, 11], title='', showgrid=True, gridcolor='#E9ECEF'),
        yaxis=dict(title='', categoryorder='total ascending'),
        showlegend=False, margin=dict(l=10, r=30, t=30, b=30), height=380, width=460,
        paper_bgcolor='white', plot_bgcolor='white'
    )

    radar_path = tempfile.mktemp(suffix=".png")
    bar_path = tempfile.mktemp(suffix=".png")
    fig_radar.write_image(radar_path, scale=2)
    fig_bar.write_image(bar_path, scale=2)

    parsed = parse_cislf_report(markdown_text)

    # Extract role and industry from raw text
    header_lines = markdown_text.split("\n")[:15]
    role, industry = "Technology Executive", "Not specified"
    for line in header_lines:
        if "Prepared for:" in line or "**Prepared for:**" in line:
            parts = line.replace("Prepared for:", "").replace("**Prepared for:**", "").split("|")
            role = parts[0].strip()
            if len(parts) > 1: industry = parts[1].strip()
            break

    pdf_bytes = generate_premium_pdf(parsed, role, industry, radar_path, bar_path, source)

    try: os.remove(radar_path)
    except: pass
    try: os.remove(bar_path)
    except: pass

    return pdf_bytes


def get_current_scores():
    """Extract current pillar scores and overall score.
    Returns:
        tuple of (p1, p2, p3, p4, overall) as floats
    """
    answers = st.session_state.get("manual_answers", {})
    report_text = st.session_state.get("report_text")
    report_source = st.session_state.get("report_source")

    # If we have a report generated and the source was manual, calculate from active answers
    if report_text and report_source == "Manual" and answers:
        try:
            p_scores, overall = calculate_all_scores(answers)
            return p_scores[1], p_scores[2], p_scores[3], p_scores[4], overall
        except Exception:
            pass

    # If we have an AI report, parse the scores from it using regex
    if report_text and report_source == "AI":
        try:
            import re
            scorecard_raw = _between(report_text, "CISLF MATURITY SCORECARD", "FRAMEWORK REFERENCE")
            if scorecard_raw:
                scores = re.findall(r"(\d+(?:\.\d+)?)\s*/\s*10", scorecard_raw)
                if len(scores) >= 5:
                    return (
                        float(scores[0]),
                        float(scores[1]),
                        float(scores[2]),
                        float(scores[3]),
                        float(scores[4]),
                    )
        except Exception:
            pass

    # Fallback to manual answers if they exist (even if report is not yet generated)
    if answers:
        try:
            if any(answers.values()):
                p_scores, overall = calculate_all_scores(answers)
                return p_scores[1], p_scores[2], p_scores[3], p_scores[4], overall
        except Exception:
            pass

    return 0.0, 0.0, 0.0, 0.0, 0.0


def _render_executive_banner():
    st.markdown("""
    <div style="background: white; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05); padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.02); display: flex; gap: 1.5rem; align-items: center;">
        <div style="width: 64px; height: 64px; border-radius: 50%; background: #E8F5E9; color: #1B4332; display: flex; align-items: center; justify-content: center; font-size: 2.2rem; box-shadow: inset 0 2px 6px rgba(27,67,50,0.1); flex-shrink: 0;">
            👨‍💼
        </div>
        <div style="flex: 1;">
            <div style="display: flex; align-items: center; gap: 0.8rem; flex-wrap: wrap;">
                <h3 style="margin: 0; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.3rem; color: #1B4332;">Mohammad Quasif, DBA</h3>
                <span style="background: #E8F5E9; color: #1B4332; font-size: 0.72rem; font-weight: 600; padding: 0.15rem 0.6rem; border-radius: 4px;">Author & Candidate</span>
            </div>
            <p style="margin: 0.2rem 0 0.6rem 0; font-size: 0.85rem; color: #6c757d; font-style: italic; line-height: 1.4;">
                Quasif, M. (2025). Strategic Leadership for AI-Driven Business Transformation: A Cross-Industry Framework for Technology Executives. DBA Thesis. Kennedy University of Baptist, France.
            </p>
            <div style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
                <span style="font-size:0.7rem; background:#E1F5FE; color:#0288D1; padding:0.2rem 0.5rem; border-radius:4px; font-weight:600;">🎯 Pillar 1: Leadership</span>
                <span style="font-size:0.7rem; background:#EDE7F6; color:#5E35B1; padding:0.2rem 0.5rem; border-radius:4px; font-weight:600;">🔗 Pillar 2: Alignment</span>
                <span style="font-size:0.7rem; background:#FCE4D6; color:#C65911; padding:0.2rem 0.5rem; border-radius:4px; font-weight:600;">🏗️ Pillar 3: Capability</span>
                <span style="font-size:0.7rem; background:#FFF9C4; color:#F57F17; padding:0.2rem 0.5rem; border-radius:4px; font-weight:600;">⚖️ Pillar 4: Governance</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_kpi_cards(p1, p2, p3, p4):
    kpi_cols = st.columns(4)
    
    pillars_meta = [
        {"title": "P1 Leadership", "score": p1, "color": "#E1F5FE", "text_color": "#0288D1", "icon": "🎯"},
        {"title": "P2 Alignment", "score": p2, "color": "#EDE7F6", "text_color": "#5E35B1", "icon": "🔗"},
        {"title": "P3 Capability", "score": p3, "color": "#FCE4D6", "text_color": "#C65911", "icon": "🏗️"},
        {"title": "P4 Governance", "score": p4, "color": "#FFF9C4", "text_color": "#F57F17", "icon": "⚖️"},
    ]
    
    for col, p_meta in zip(kpi_cols, pillars_meta):
        with col:
            score_val = f"{p_meta['score']:.1f}/10"
            status_label = get_maturity_label(p_meta['score'])
            st.markdown(f"""
            <div class="kpi-card" style="background: white; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05); padding: 1.1rem; box-shadow: 0 4px 20px rgba(0,0,0,0.02); display: flex; align-items: center; justify-content: space-between; min-height: 96px;">
                <div>
                    <div style="font-size: 0.72rem; color: #888888; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">{p_meta['title']}</div>
                    <div style="font-size: 1.5rem; font-weight: 800; color: #1B4332; margin-top: 0.15rem;">{score_val}</div>
                    <div style="font-size: 0.7rem; color: #6c757d; font-weight: 600; margin-top: 0.2rem;">Status: <span style="color: {p_meta['text_color']};">{status_label}</span></div>
                </div>
                <div style="width: 40px; height: 40px; border-radius: 50%; background: {p_meta['color']}; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0;">
                    {p_meta['icon']}
                </div>
            </div>
            """, unsafe_allow_html=True)


def _render_overall_maturity_card(p1, p2, p3, p4, overall):
    color = get_maturity_color(overall)
    label = get_maturity_label(overall)
    
    st.markdown(f"""
<div style="background: white; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05); padding: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.02); height: 100%;">
    <h3 style="margin-top:0; color:#1B4332; font-family:'Plus Jakarta Sans', sans-serif;">📈 Overall CISLF Maturity</h3>
    <div style="display: flex; align-items: center; gap: 1.5rem; margin-top: 1.2rem; margin-bottom: 1.5rem;">
        <div style="width: 80px; height: 80px; border-radius: 50%; border: 6px solid {color}; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; font-weight: 800; color: {color}; flex-shrink: 0;">
            {overall:.1f}
        </div>
        <div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1B4332;">{label}</div>
            <div style="font-size: 0.82rem; color: #6c757d; margin-top: 0.2rem; line-height: 1.3;">Framework maturity index. Generate a full report to update.</div>
        </div>
    </div>
    
    <h4 style="color:#1B4332; font-family:'Plus Jakarta Sans', sans-serif; font-size: 0.95rem; font-weight:700; margin-bottom: 1rem; border-top: 1px solid rgba(0,0,0,0.05); padding-top: 1rem;">Pillar Score Breakdown</h4>
""", unsafe_allow_html=True)

    pillars_data = [
        ("Pillar 1: Leadership Mindset", p1, "#0288D1"),
        ("Pillar 2: Strategic Alignment", p2, "#5E35B1"),
        ("Pillar 3: Organisational Capability", p3, "#C65911"),
        ("Pillar 4: Responsible Governance", p4, "#F57F17"),
    ]
    for name, val, bar_color in pillars_data:
        pct = int((val / 10) * 100)
        st.markdown(f"""
<div style="margin-bottom: 0.9rem;">
    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600; color: #1B4332;">
        <span>{name}</span>
        <span>{val:.1f}/10</span>
    </div>
    <div class="progress-track" style="margin-top: 0.25rem; background: #E9ECEF; border-radius: 8px; height: 10px; overflow: hidden;">
        <div class="progress-fill" style="background:{bar_color}; width:{pct}%; height: 100%; border-radius: 8px; transition: width 0.4s ease;"></div>
    </div>
</div>
""", unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)


def _render_plotly_charts(p1, p2, p3, p4):
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    
    categories = [
        'Leadership Mindset<br>& Vision',
        'Biz-Tech<br>Alignment',
        'Capability &<br>Culture',
        'Responsible AI<br>Governance'
    ]
    scores = [p1, p2, p3, p4]
    
    c1, c2 = st.columns(2)
    
    with c1:
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor='rgba(82, 183, 136, 0.4)',
            line=dict(color='#1B4332', width=2),
            name='CISLF Maturity',
            hoverinfo='r+theta'
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(color='#6c757d'), gridcolor='#E9ECEF'),
                angularaxis=dict(tickfont=dict(size=12, color='#1B4332'), gridcolor='#E9ECEF', linecolor='#E9ECEF')
            ),
            showlegend=False,
            margin=dict(l=50, r=50, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=320
        )
        st.markdown("<h4 style='color:#1B4332; text-align:center; font-size:1.1rem; margin-bottom:0.5rem;'>🕸️ Maturity Radar</h4>", unsafe_allow_html=True)
        st.plotly_chart(fig_radar, use_container_width=True)
        
    with c2:
        df = pd.DataFrame({'Pillar': ['P1: Leadership', 'P2: Alignment', 'P3: Culture', 'P4: Governance'], 'Score': scores})
        df['Color'] = [get_maturity_color(s) for s in scores]
        
        fig_bar = px.bar(
            df, x='Score', y='Pillar', orientation='h',
            text='Score',
            color='Pillar', color_discrete_sequence=df['Color'].tolist()
        )
        fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside', marker_line_color='#1B4332', marker_line_width=1.5, opacity=0.9)
        fig_bar.update_layout(
            xaxis=dict(range=[0, 10.5], title='', showgrid=True, gridcolor='#E9ECEF', tickfont=dict(color='#6c757d')),
            yaxis=dict(title='', categoryorder='total ascending', tickfont=dict(size=12, color='#1B4332', weight='bold')),
            showlegend=False,
            margin=dict(l=20, r=40, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=320
        )
        st.markdown("<h4 style='color:#1B4332; text-align:center; font-size:1.1rem; margin-bottom:0.5rem;'>📊 Pillar Strengths</h4>", unsafe_allow_html=True)
        st.plotly_chart(fig_bar, use_container_width=True)


def _render_framework_explanation():
    st.markdown("<hr style='border-top: 1px dashed rgba(0,0,0,0.1); margin: 3rem 0 2rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#1B4332; font-family:\"Plus Jakarta Sans\", sans-serif; text-align:center; margin-bottom:0.5rem;'>🧩 The CISLF Framework</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#6c757d; max-width:600px; margin:0 auto 2.5rem auto;'>The Comprehensive Intelligent Strategic Leadership Framework empowers executives to drive AI transformation across four interconnected pillars.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("""
        <div style="background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; border: 1px solid #D8F3DC; display: flex; gap: 1.2rem; align-items: flex-start; box-shadow: 0 4px 15px rgba(27,67,50,0.03);">
            <div style="font-size: 2.2rem; background: #E8F5E9; width: 65px; height: 65px; display: flex; align-items: center; justify-content: center; border-radius: 12px; flex-shrink: 0; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);">🧠</div>
            <div>
                <h4 style="margin:0 0 0.4rem 0; color:#1B4332; font-size: 1.05rem;">1. Leadership Mindset & Vision</h4>
                <p style="margin:0; font-size: 0.85rem; color:#6c757d; line-height: 1.5;">Evaluates executive readiness, adaptive behaviors, and the formulation of a compelling, enterprise-wide AI vision.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; border: 1px solid #D8F3DC; display: flex; gap: 1.2rem; align-items: flex-start; box-shadow: 0 4px 15px rgba(27,67,50,0.03);">
            <div style="font-size: 2.2rem; background: #FFF3E0; width: 65px; height: 65px; display: flex; align-items: center; justify-content: center; border-radius: 12px; flex-shrink: 0; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);">⚙️</div>
            <div>
                <h4 style="margin:0 0 0.4rem 0; color:#1B4332; font-size: 1.05rem;">2. Strategic Biz-Tech Alignment</h4>
                <p style="margin:0; font-size: 0.85rem; color:#6c757d; line-height: 1.5;">Ensures AI initiatives are deeply anchored to business outcomes, fostering seamless cross-functional collaboration.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; border: 1px solid #D8F3DC; display: flex; gap: 1.2rem; align-items: flex-start; box-shadow: 0 4px 15px rgba(27,67,50,0.03);">
            <div style="font-size: 2.2rem; background: #E3F2FD; width: 65px; height: 65px; display: flex; align-items: center; justify-content: center; border-radius: 12px; flex-shrink: 0; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);">👥</div>
            <div>
                <h4 style="margin:0 0 0.4rem 0; color:#1B4332; font-size: 1.05rem;">3. Capability & Culture</h4>
                <p style="margin:0; font-size: 0.85rem; color:#6c757d; line-height: 1.5;">Assesses human capital readiness, AI literacy, upskilling, and a culture that treats experimentation as learning.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
def page_dashboard():
    render_header()
    _render_executive_banner()
    
    p1, p2, p3, p4, overall = get_current_scores()
    
    # 4 Column KPI Cards
    _render_kpi_cards(p1, p2, p3, p4)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bottom Layout
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        _render_overall_maturity_card(p1, p2, p3, p4, overall)
        
    with col_right:
        report_text = st.session_state.get("report_text")
        if report_text:
            source = st.session_state.get("report_source", "AI")
            source_label = "🤖 AI-Generated" if source == "AI" else "📋 Rule-Based"
            
            st.markdown(f"<h3 style='color:#1B4332; font-family:\"Plus Jakarta Sans\", sans-serif; margin-bottom:1.5rem;'>📈 Maturity Visualisation &nbsp; <span style='font-size:0.75rem;background:#D8F3DC;color:#1B4332;padding:0.2rem 0.6rem;border-radius:20px;font-weight:600;vertical-align:middle;'>{source_label}</span></h3>", unsafe_allow_html=True)
            
            _render_plotly_charts(p1, p2, p3, p4)

    if report_text:
        # Full Report Display Below
        st.markdown("<hr style='border-top: 1px dashed rgba(0,0,0,0.1); margin: 3rem 0 2rem 0;'>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([2.2, 1.8])
        with c1:
            st.markdown("<h2 style='color:#1B4332; font-family:\"Plus Jakarta Sans\", sans-serif; margin-bottom:1rem;'>📄 Strategic Assessment Report</h2>", unsafe_allow_html=True)
        with c2:
            # Download and Retest buttons
            pdf_bytes = generate_pdf_from_markdown(report_text, p1, p2, p3, p4, source)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dl_b1, dl_b2, dl_b3 = st.columns(3)
            with dl_b1:
                st.download_button("⬇️ TXT", data=report_text, file_name=f"CISLF_Analysis_{ts}.txt", mime="text/plain", key="btn_dash_txt", use_container_width=True)
            with dl_b2:
                st.download_button("⬇️ PDF", data=pdf_bytes, file_name=f"CISLF_Analysis_{ts}.pdf", mime="application/pdf", key="btn_dash_pdf", use_container_width=True)
            with dl_b3:
                def _do_retest():
                    st.session_state["report_text"] = None
                    if "answers" in st.session_state:
                        st.session_state["answers"] = {}
                    st.session_state["manual_step"] = 0
                    
                    # Wipe all widget memory
                    keys_to_delete = [k for k in st.session_state.keys() if k.startswith("q_") or k.startswith("ai_") or k.startswith("welcome_")]
                    for k in keys_to_delete:
                        del st.session_state[k]
                        
                    st.session_state["page"] = "📋 Manual Assessment"
                st.button("🔄 Retest", on_click=_do_retest, key="btn_dash_retest", use_container_width=True, type="primary")
        
        # Parse the report using the cislf_engine parser
        parsed_rep = parse_cislf_report(report_text)
        
        if parsed_rep["is_parsed"]:
            tab_summary, tab_pillars, tab_roadmap, tab_risks, tab_raw = st.tabs([
                "🎯 Strategic Summary",
                "🛡️ Pillar Deep Dive",
                "📅 90-Day Roadmap",
                "⚠️ Risks & Priorities",
                "📄 Plain Text Report"
            ])
            
            # --- TAB 1: SUMMARY ---
            with tab_summary:
                st.markdown(f"""
                <div style="background: white; border-radius: 16px; border: 1px solid rgba(0,0,0,0.05); padding: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.01); margin-top: 1rem; line-height: 1.8; color: #495057;">
                    <h3 style="margin-top: 0; color: #1B4332; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.35rem; font-weight: 700; border-bottom: 2px solid #D8F3DC; padding-bottom: 8px; margin-bottom: 1rem;">Executive Summary</h3>
                    <p style="margin: 0; font-size: 0.98rem; text-align: justify;">{parsed_rep["executive_summary"]}</p>
                </div>
                <div style="background: #E8F5E9; border-radius: 12px; border-left: 6px solid #2D6A4F; padding: 1.5rem; margin-top: 1.5rem; box-shadow: 0 4px 12px rgba(45,106,79,0.04);">
                    <strong style="color: #1B4332; font-size: 1.05rem; font-family: 'Plus Jakarta Sans', sans-serif;">Transformation Readiness Justification</strong>
                    <p style="margin: 0.4rem 0 0 0; font-size: 0.92rem; color: #2D6A4F; line-height: 1.6;">{parsed_rep["readiness_justification"]}</p>
                </div>
                """, unsafe_allow_html=True)
                
            # --- TAB 2: PILLARS ---
            with tab_pillars:
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                for num, pillar in parsed_rep["pillars"].items():
                    color = get_maturity_color(pillar["score"])
                    
                    with st.expander(f"Pillar {num}: {pillar['title']} — Score: {pillar['score']}/10", expanded=(num == 1)):
                        st.markdown(f"""
                        <div style="background: #F4F7F5; border-radius: 8px; padding: 1.1rem; margin-bottom: 1.2rem; font-size: 0.92rem; color: #2C3E35; border-left: 3px solid {color}; line-height: 1.6; font-style: italic;">
                            "{pillar['assessment']}"
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_str, col_gap = st.columns(2)
                        with col_str:
                            str_lis = "".join(f"<li style='margin-bottom: 8px; padding-left: 0.2rem;'>{item}</li>" for item in pillar["strengths"])
                            st.markdown(f"""
                            <div style="background: #EAF7ED; border: 1px solid #C2ECD0; border-radius: 10px; padding: 1.2rem; height: 100%;">
                                <div style="color: #2D6A4F; font-size: 1rem; font-weight: 700; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.8rem; font-family: 'Plus Jakarta Sans', sans-serif;">
                                    <span>🟢</span> Strengths Identified
                                </div>
                                <ul style="margin: 0; padding-left: 1.1rem; font-size: 0.86rem; color: #1B4332; line-height: 1.5;">
                                    {str_lis}
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        with col_gap:
                            gap_lis = "".join(f"<li style='margin-bottom: 8px; padding-left: 0.2rem;'>{item}</li>" for item in pillar["gaps"])
                            st.markdown(f"""
                            <div style="background: #FFF5EC; border: 1px solid #FFE3CC; border-radius: 10px; padding: 1.2rem; height: 100%;">
                                <div style="color: #B25E00; font-size: 1rem; font-weight: 700; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.8rem; font-family: 'Plus Jakarta Sans', sans-serif;">
                                    <span>🟠</span> Critical Gaps
                                </div>
                                <ul style="margin: 0; padding-left: 1.1rem; font-size: 0.86rem; color: #8C4A00; line-height: 1.5;">
                                    {gap_lis}
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        rec_lis = "".join(f"<li style='margin-bottom: 8px; padding-left: 0.2rem;'>{item}</li>" for item in pillar["recommendations"])
                        st.markdown(f"""
                        <br>
                        <div style="background: #F0F7FF; border: 1px solid #CBE3FF; border-radius: 10px; padding: 1.3rem;">
                            <div style="color: #004B8C; font-size: 1rem; font-weight: 700; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.8rem; font-family: 'Plus Jakarta Sans', sans-serif;">
                                <span>💡</span> Strategic Recommendations
                            </div>
                            <ul style="margin: 0; padding-left: 1.2rem; font-size: 0.88rem; color: #003666; line-height: 1.6;">
                                {rec_lis}
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)

            # --- TAB 3: 90-DAY ROADMAP (STEPPER) ---
            with tab_roadmap:
                m1_steps = "".join(f"<li style='margin-bottom: 0.6rem; padding-left:0.2rem;'>{item}</li>" for item in parsed_rep["action_plan"]["month1"])
                m2_steps = "".join(f"<li style='margin-bottom: 0.6rem; padding-left:0.2rem;'>{item}</li>" for item in parsed_rep["action_plan"]["month2"])
                m3_steps = "".join(f"<li style='margin-bottom: 0.6rem; padding-left:0.2rem;'>{item}</li>" for item in parsed_rep["action_plan"]["month3"])
                
                st.markdown(f"""
                <div class="stepper-container" style="position: relative; padding-left: 2.5rem; margin-top: 1.8rem; margin-bottom: 1.5rem; font-family: 'Inter', sans-serif;">
                    <!-- Step 1 -->
                    <div class="stepper-step" style="position: relative; margin-bottom: 2.5rem;">
                        <div style="position: absolute; left: -1.75rem; top: 2rem; bottom: -3.2rem; width: 4px; background: #52B788; z-index: 1;"></div>
                        <div style="position: absolute; left: -2.4rem; top: 0; width: 2.2rem; height: 2.2rem; border-radius: 50%; background: #1B4332; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.95rem; z-index: 2; box-shadow: 0 4px 10px rgba(27,67,50,0.25);">
                            1
                        </div>
                        <div style="background: white; border-radius: 12px; border: 1px solid #D8F3DC; padding: 1.5rem; box-shadow: 0 4px 15px rgba(27,67,50,0.03);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; flex-wrap: wrap; gap: 0.5rem;">
                                <h4 style="margin: 0; color: #1B4332; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.15rem; font-weight: 700; display: flex; align-items: center; gap: 0.4rem;">
                                    <span>🚀</span> Month 1: Foundation
                                </h4>
                                <span style="background: #E8F5E9; color: #2D6A4F; font-size: 0.72rem; font-weight: 700; padding: 0.2rem 0.65rem; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px;">Days 1-30</span>
                            </div>
                            <ul style="margin: 0; padding-left: 1.2rem; font-size: 0.9rem; color: #495057; line-height: 1.6;">
                                {m1_steps}
                            </ul>
                        </div>
                    </div>
                    <!-- Step 2 -->
                    <div class="stepper-step" style="position: relative; margin-bottom: 2.5rem;">
                        <div style="position: absolute; left: -1.75rem; top: 2rem; bottom: -3.2rem; width: 4px; background: #52B788; z-index: 1;"></div>
                        <div style="position: absolute; left: -2.4rem; top: 0; width: 2.2rem; height: 2.2rem; border-radius: 50%; background: #2D6A4F; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.95rem; z-index: 2; box-shadow: 0 4px 10px rgba(27,67,50,0.25);">
                            2
                        </div>
                        <div style="background: white; border-radius: 12px; border: 1px solid #D8F3DC; padding: 1.5rem; box-shadow: 0 4px 15px rgba(27,67,50,0.03);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; flex-wrap: wrap; gap: 0.5rem;">
                                <h4 style="margin: 0; color: #1B4332; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.15rem; font-weight: 700; display: flex; align-items: center; gap: 0.4rem;">
                                    <span>⚡</span> Month 2: Acceleration
                                </h4>
                                <span style="background: #E8F5E9; color: #2D6A4F; font-size: 0.72rem; font-weight: 700; padding: 0.2rem 0.65rem; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px;">Days 31-60</span>
                            </div>
                            <ul style="margin: 0; padding-left: 1.2rem; font-size: 0.9rem; color: #495057; line-height: 1.6;">
                                {m2_steps}
                            </ul>
                        </div>
                    </div>
                    <!-- Step 3 -->
                    <div class="stepper-step" style="position: relative;">
                        <div style="position: absolute; left: -2.4rem; top: 0; width: 2.2rem; height: 2.2rem; border-radius: 50%; background: #52B788; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.95rem; z-index: 2; box-shadow: 0 4px 10px rgba(27,67,50,0.25);">
                            3
                        </div>
                        <div style="background: white; border-radius: 12px; border: 1px solid #D8F3DC; padding: 1.5rem; box-shadow: 0 4px 15px rgba(27,67,50,0.03);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; flex-wrap: wrap; gap: 0.5rem;">
                                <h4 style="margin: 0; color: #1B4332; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.15rem; font-weight: 700; display: flex; align-items: center; gap: 0.4rem;">
                                    <span>🔗</span> Month 3: Integration
                                </h4>
                                <span style="background: #E8F5E9; color: #2D6A4F; font-size: 0.72rem; font-weight: 700; padding: 0.2rem 0.65rem; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px;">Days 61-90</span>
                            </div>
                            <ul style="margin: 0; padding-left: 1.2rem; font-size: 0.9rem; color: #495057; line-height: 1.6;">
                                {m3_steps}
                            </ul>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            # --- TAB 4: RISKS & PRIORITIES ---
            with tab_risks:
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                st.markdown("<h4 style='color:#1B4332; font-family:\"Plus Jakarta Sans\", sans-serif;'>⚠️ Key Transformation Risks</h4>", unsafe_allow_html=True)
                
                r_cols = st.columns(3)
                for i, risk in enumerate(parsed_rep["risks"]):
                    prob = risk["probability"].strip().upper()
                    imp = risk["impact"].strip().upper()
                    
                    prob_color = "#D62828" if prob == "HIGH" else "#FFB703" if prob == "MEDIUM" else "#2D6A4F"
                    imp_color = "#D62828" if imp == "HIGH" else "#FFB703" if imp == "MEDIUM" else "#2D6A4F"
                    
                    with r_cols[i % 3]:
                        st.markdown(f"""
                        <div style="background: white; border: 1px solid rgba(0,0,0,0.06); border-radius: 10px; padding: 1.2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.02); height: 100%;">
                            <h5 style="margin-top: 0; color: #1B4332; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.95rem; font-weight: 700;">{risk['name']}</h5>
                            <div style="display: flex; gap: 0.4rem; margin-bottom: 0.8rem; flex-wrap: wrap;">
                                <span style="font-size: 0.68rem; font-weight: 700; background: {prob_color}20; color: {prob_color}; padding: 0.15rem 0.5rem; border-radius: 4px; border: 1px solid {prob_color}40;">PROB: {prob}</span>
                                <span style="font-size: 0.68rem; font-weight: 700; background: {imp_color}20; color: {imp_color}; padding: 0.15rem 0.5rem; border-radius: 4px; border: 1px solid {imp_color}40;">IMPACT: {imp}</span>
                            </div>
                            <p style="font-size: 0.82rem; color: #555; line-height: 1.5; margin-bottom: 0.8rem;">{risk['description']}</p>
                            <div style="background: #FAF9F6; border-left: 3px solid #856404; padding: 0.6rem; border-radius: 4px; font-size: 0.78rem; color: #66521A; line-height: 1.4;">
                                <strong>Mitigation:</strong> {risk['mitigation']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("<br><hr style='border-top: 1px solid rgba(0,0,0,0.06);'><br>", unsafe_allow_html=True)
                st.markdown("<h4 style='color:#1B4332; font-family:\"Plus Jakarta Sans\", sans-serif;'>🏆 Top 5 Priority Actions</h4>", unsafe_allow_html=True)
                
                for i, act in enumerate(parsed_rep["priority_actions"], 1):
                    st.markdown(f"""
                    <div style="background: white; border-radius: 10px; border: 1px solid rgba(45,106,79,0.08); padding: 1.1rem; margin-bottom: 0.8rem; display: flex; gap: 1.2rem; align-items: flex-start; box-shadow: 0 2px 8px rgba(27,67,50,0.02);">
                        <div style="background: #E8F5E9; color: #2D6A4F; font-size: 1.1rem; font-weight: 800; border-radius: 50%; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            {i}
                        </div>
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.3rem;">
                                <strong style="color: #1B4332; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1rem;">{act['title']}</strong>
                                <div style="display: flex; gap: 0.3rem;">
                                    <span style="font-size: 0.7rem; font-weight: 700; background: #E1F5FE; color: #0288D1; padding: 0.15rem 0.5rem; border-radius: 4px;">Pillar {act['pillar']}</span>
                                    <span style="font-size: 0.7rem; font-weight: 700; background: #EDE7F6; color: #5E35B1; padding: 0.15rem 0.5rem; border-radius: 4px;">{act['timeline']}</span>
                                </div>
                            </div>
                            <p style="margin: 0; font-size: 0.86rem; color: #555; line-height: 1.5;">{act['description']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # --- TAB 5: PLAIN TEXT ---
            with tab_raw:
                st.markdown(f'<div class="report-box">{report_text}</div>', unsafe_allow_html=True)
                
        else:
            # Fallback to single text display if parsing fails
            import re
            formatted_html = report_text.replace('\n', '<br>')
            formatted_html = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color:#2D6A4F;">\1</strong>', formatted_html)
            formatted_html = re.sub(r'#+\s*(.*?)(<br>|$)', r'<h3 style="color:#1B4332; margin-top:20px; border-bottom:2px solid #D8F3DC; padding-bottom:8px;">\1</h3>\2', formatted_html)
            
            st.markdown(f"""
            <div style="background: white; border-radius: 16px; border: 1px solid rgba(0,0,0,0.05); padding: 2.5rem; box-shadow: 0 8px 30px rgba(0,0,0,0.03); font-family: 'Inter', sans-serif; color: #495057; line-height: 1.8;">
                {formatted_html}
            </div>
            """, unsafe_allow_html=True)
        
    if not report_text:
        st.markdown("""
        <div style="background: white; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05); padding: 2.2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.02); text-align: center;">
            <span style="font-size: 3rem;">📊</span>
            <h3 style="margin-top: 1rem; color: #1B4332; font-family: 'Plus Jakarta Sans', sans-serif;">Assessment Pending</h3>
            <p style="font-size: 0.9rem; color: #6c757d; max-width: 340px; margin: 0.5rem auto 1.5rem auto;">
                You have not generated a strategic CISLF report yet. Choose an assessment method in the sidebar menu to begin.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: rgba(255,255,255,0.7); border-radius: 10px; padding: 1.2rem; border: 1px dashed rgba(0,0,0,0.1); font-size:0.88rem;">
            <strong style="color: #1B4332;">Assessment Options:</strong><br>
            <ul>
                <li style="margin-top:0.4rem;"><strong>🤖 AI Consultation</strong> — Submit your detailed enterprise transformation challenge. The AI model analyzes it against the 4 pillars of the CISLF framework.</li>
                <li style="margin-top:0.4rem;"><strong>📋 Manual Assessment</strong> — Complete the 20-question structured weighted questionnaire. The rules engine calculates scores and generates your report instantly.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    _render_framework_explanation()

    # Footer
    _render_footer()


def page_ai_consultation():
    render_header()
    st.info(
        "🤖 **AI Consultation Mode** — Describe your AI transformation challenge. The LLM generates "
        "a structured, consulting-grade CISLF report. Requires a Google Gemini or OpenAI API key."
    )
    _ai_mode_form()
    _render_footer()


def page_manual_assessment():
    render_header()
    _manual_mode_form()
    _render_footer()


def _render_footer():
    st.markdown("""
    <div class="cislf-footer">
        🧠 <strong>Cogni CISLF Advisor</strong> — Powered by the CISLF Framework<br>
        Framework developed by <strong>Mohammad Quasif, DBA</strong> |
        Kennedy University of Baptist, France<br>
        <em>Quasif, M. (2025). Strategic Leadership for AI-Driven Business Transformation:
        A Cross-Industry Framework for Technology Executives. DBA Thesis.</em>
    </div>
    """, unsafe_allow_html=True)


# ── AI Mode Form ─────────────────────────────────────────────────────────────
def _ai_mode_form():
    import time

    # ── Show active engine status card ───────────────────────────────────────
    provider = st.session_state.get("provider", "Google Gemini")
    model = st.session_state.get("model", "gemini-1.5-flash")
    key_state = (
        "gemini_key" if provider == "Google Gemini"
        else "openai_key" if provider == "OpenAI"
        else "deepseek_key"
    )
    api_key = st.session_state.get(key_state, "")
    cred_name = (
        CRED_GEMINI if provider == "Google Gemini"
        else CRED_OPENAI if provider == "OpenAI"
        else CRED_DEEPSEEK
    )
    is_saved = credential_exists(cred_name)

    if is_saved:
        status_html = '<span style="color: #2D6A4F; font-weight:700;">🟢 Connected (🔒 Saved Locally)</span>'
    elif api_key.strip():
        status_html = '<span style="color: #FFB703; font-weight:700;">🟡 Connected (⏳ Session Only)</span>'
    else:
        status_html = '<span style="color: #D90429; font-weight:700;">🔴 API Key Missing</span>'

    status_col1, status_col2 = st.columns([3, 1])
    with status_col1:
        st.markdown(f"""
        <div style="background: white; padding: 0.9rem 1.2rem; border-radius: 12px; border: 1px solid #D8F3DC; display: flex; flex-direction: column; box-shadow: 0 4px 12px rgba(27,67,50,0.03);">
            <div style="font-size: 0.8rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px;">Active Engine</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #1B4332; margin-top:0.15rem;">{provider} ({model})</div>
            <div style="font-size: 0.85rem; margin-top: 0.25rem; color: #1B4332;">Key Status: {status_html}</div>
        </div>
        """, unsafe_allow_html=True)
    with status_col2:
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("⚙️ Setup Engine", key="btn_setup_redirect", help="Configure providers, models and keys", type="secondary"):
            st.session_state["page"] = "⚙️ Setup & Settings"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📝 Describe Your AI Transformation Challenge")

    c1, c2 = st.columns(2)
    with c1:
        role = st.text_input(
            "Your Executive Role (optional)",
            placeholder="e.g., CIO, CTO, Chief AI Officer",
            key="ai_role",
        )
    with c2:
        industry = st.text_input(
            "Industry / Sector (optional)",
            placeholder="e.g., Healthcare, Financial Services",
            key="ai_industry",
        )

    challenge = st.text_area(
        "AI Transformation Challenge *(minimum 50 characters)*",
        placeholder=(
            "Describe your AI transformation challenge in detail. For example:\n\n"
            "Our organisation is a mid-sized financial services firm. We've been trying to deploy "
            "AI-powered credit risk models for 18 months but face resistance from risk teams, "
            "unclear ownership between IT and the business, limited AI talent, and growing regulatory "
            "pressure around explainability. Our leadership team is enthusiastic but lacks a coherent "
            "AI strategy…"
        ),
        height=220,
        key="ai_challenge",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Check if job is running so we can disable the button
    job_id = st.session_state.get("ai_job_id")
    is_running = bool(job_id and job_id in AI_JOBS and AI_JOBS[job_id].get("status") == "running")

    btn_col, _ = st.columns([1, 3])
    with btn_col:
        if st.button("🚀 Generate CISLF Analysis", key="btn_ai_generate", disabled=is_running):
            _run_ai_generation(challenge, role, industry)

    # ── POLL RUNNING JOB (At the bottom, after the form) ──────────────────────
    if job_id and job_id in AI_JOBS:
        job = AI_JOBS[job_id]
        status = job.get("status", "running")

        if status == "running":
            model_disp    = st.session_state.get("ai_gen_model", "AI")
            provider_disp = st.session_state.get("ai_gen_provider", "")
            
            # Calculate simulated progress (0-99%) based on elapsed time (assuming ~45s average)
            start_time = job.get("start_time", time.time())
            elapsed = time.time() - start_time
            progress_pct = min(int((elapsed / 45.0) * 100), 99)

            st.markdown(f"""
            <div style="background:white;border-radius:12px;border:1px solid #D8F3DC;
                        padding:1.5rem;margin-top:1.5rem;box-shadow:0 4px 12px rgba(27,67,50,0.03);">
                <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:0.5rem;">
                    <div>
                        <div style="font-weight:700;color:#1B4332;font-size:1.1rem;">🧠 Generating CISLF Report…</div>
                        <div style="font-size:0.85rem;color:#6c757d;margin-top:0.2rem;">Using <strong>{provider_disp} ({model_disp})</strong></div>
                    </div>
                    <div style="font-weight:700;color:#52B788;font-size:1.2rem;">{progress_pct}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.progress(progress_pct / 100.0)
            
            time.sleep(2)
            st.rerun()

        elif status == "done":
            raw_report = job.get("report", "")

            st.markdown("""
            <div style="background:white;border-radius:12px;border:1px solid #D8F3DC;
                        padding:2rem;margin-top:1.5rem;box-shadow:0 8px 20px rgba(27,67,50,0.05); text-align:center;">
                <div style="font-size:3.5rem; margin-bottom:0.5rem;">✅</div>
                <h3 style="color:#1B4332; font-family:'Plus Jakarta Sans', sans-serif; margin-bottom:0.5rem;">Analysis Complete!</h3>
                <p style="color:#6c757d; font-size:0.95rem; margin-bottom:0;">Your enterprise transformation report has been successfully generated.</p>
            </div>
            """, unsafe_allow_html=True)

            is_valid, missing = validate_report(raw_report)
            if not is_valid:
                st.warning(
                    f"⚠️ Report may be missing sections: {', '.join(missing)}. "
                    "Try a more capable model if incomplete."
                )

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📊 View Report in Dashboard", key="btn_go_dashboard", use_container_width=True, type="primary"):
                # Clean up the job from the module dict
                del AI_JOBS[job_id]
                st.session_state["ai_job_id"] = None

                st.session_state["report_text"]   = raw_report
                st.session_state["report_source"] = "AI"
                st.session_state["page"]          = "📊 Dashboard"
                st.rerun()

        elif status == "error":
            error_msg = job.get("error", "Unknown error occurred.")
            del AI_JOBS[job_id]
            st.session_state["ai_job_id"] = None
            st.error(error_msg)


def _run_ai_generation(challenge: str, role: str, industry: str):
    """Validate inputs, register a job in AI_JOBS, and kick off a background thread."""
    import threading
    import time

    provider  = st.session_state.get("provider", "Google Gemini")
    model     = st.session_state.get("model", "gemini-1.5-flash")
    key_state = (
        "gemini_key" if provider == "Google Gemini"
        else "openai_key" if provider == "OpenAI"
        else "deepseek_key"
    )
    api_key = st.session_state.get(key_state, "")

    # Validate
    errors = []
    if not challenge or len(challenge.strip()) < 50:
        errors.append(f"⚠️ Challenge must be at least 50 characters (currently {len(challenge.strip()) if challenge else 0}).")
    if not api_key or not api_key.strip():
        errors.append(f"🔑 {provider} API key is required. Go to ⚙️ Setup & Settings to add your key.")
    if errors:
        for e in errors:
            st.error(e)
        return

    # Snapshot values for thread (never access session state from a thread)
    _provider  = provider
    _model     = model
    _api_key   = api_key.strip()
    _challenge = challenge.strip()
    _role      = (role or "Technology Executive").strip()
    _industry  = (industry or "Not specified").strip()

    # Register a new job in the module-level store
    job_id = str(_uuid.uuid4())
    AI_JOBS[job_id] = {
        "status": "running", 
        "report": None, 
        "error": None,
        "start_time": time.time()
    }

    def _worker():
        """Runs in daemon thread. Writes result directly to AI_JOBS[job_id]."""
        try:
            sys_prompt  = build_system_prompt()
            user_prompt = build_user_prompt(
                challenge=_challenge,
                role=_role,
                industry=_industry,
            )
            llm    = get_provider(_provider, _api_key, _model)
            report = llm.generate(sys_prompt, user_prompt)
            AI_JOBS[job_id]["report"] = report
            AI_JOBS[job_id]["status"] = "done"
        except LLMProviderError as e:
            AI_JOBS[job_id]["error"]  = f"❌ LLM Error: {e}"
            AI_JOBS[job_id]["status"] = "error"
        except Exception as e:
            AI_JOBS[job_id]["error"]  = f"❌ Unexpected error: {e}"
            AI_JOBS[job_id]["status"] = "error"

    threading.Thread(target=_worker, daemon=True).start()

    # Store only the job_id string in session state (safely serializable)
    st.session_state["ai_job_id"]      = job_id
    st.session_state["ai_gen_provider"] = provider
    st.session_state["ai_gen_model"]    = model
    st.rerun()



# ── Manual Mode Stepper Wizard ─────────────────────────────────────────────────
def _manual_mode_form():
    """Render the 20-question CISLF questionnaire as a premium stepper wizard."""
    from manual_engine import calculate_pillar_score

    # ── Session state keys for the wizard ────────────────────────────────────
    if "manual_step" not in st.session_state:
        st.session_state["manual_step"] = 0
    if "manual_answers" not in st.session_state:
        st.session_state["manual_answers"] = {}
    if "manual_role" not in st.session_state:
        st.session_state["manual_role"] = ""
    if "manual_industry" not in st.session_state:
        st.session_state["manual_industry"] = ""

    step    = st.session_state["manual_step"]
    answers = st.session_state["manual_answers"]

    # Steps: 0=Welcome, 1-4=Pillars, 5=Review
    TOTAL_STEPS = 6   # 0..5
    PILLAR_NUMS = [1, 2, 3, 4]
    step_labels = ["Welcome", "Pillar 1", "Pillar 2", "Pillar 3", "Pillar 4", "Review"]
    step_icons  = ["🏠", "🎯", "🔗", "🏗️", "⚖️", "📊"]

    # ── TOP STEPPER NAV ───────────────────────────────────────────────────────
    progress_pct = int((step / (TOTAL_STEPS - 1)) * 100)
    dots_html = ""
    for i, (lbl, icn) in enumerate(zip(step_labels, step_icons)):
        if i < step:
            cls, lcls = "stepper-dot-done", ""
            sym = "✓"
        elif i == step:
            cls, lcls = "stepper-dot-active", "stepper-label-active"
            sym = icn
        else:
            cls, lcls = "stepper-dot-todo", ""
            sym = str(i) if i < 5 else "📊"
        dots_html += f"""
        <div class="stepper-item">
            <div class="stepper-dot {cls}">{sym}</div>
            <div class="stepper-label {lcls}">{lbl}</div>
        </div>"""

    st.markdown(f"""
    <div style="background:white; border-radius:16px; border:1px solid rgba(45,106,79,0.08);
                padding:1.5rem 1.8rem 1rem; box-shadow:0 4px 20px rgba(27,67,50,0.04); margin-bottom:1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
            <span style="font-family:'Plus Jakarta Sans',sans-serif; font-weight:700; color:#1B4332; font-size:1rem;">
                📋 CISLF Assessment Wizard
            </span>
            <span style="font-size:0.82rem; color:#6c757d; font-weight:600;">
                Step {step + 1} of {TOTAL_STEPS}
            </span>
        </div>
        <div class="stepper-progress-bar">
            <div class="stepper-progress-fill" style="width:{progress_pct}%;"></div>
        </div>
        <div class="stepper-nav">{dots_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # STEP 0 — WELCOME
    # ════════════════════════════════════════════════════════════════════════
    if step == 0:
        st.markdown("""
        <div class="wizard-card">
            <div style="text-align:center; padding: 0.5rem 0 1.5rem;">
                <div style="font-size:3.5rem; margin-bottom:0.5rem;">🧠</div>
                <h2 style="color:#1B4332; font-family:'Plus Jakarta Sans',sans-serif; font-size:1.6rem; margin:0 0 0.5rem;">CISLF Framework Assessment</h2>
                <p style="color:#6c757d; max-width:520px; margin:0 auto 1.5rem; line-height:1.6; font-size:0.95rem;">
                    Answer <strong>20 questions</strong> (5 per pillar) to receive a fully structured
                    AI Transformation Readiness Report — <em>no API key required</em>.
                </p>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.8rem; margin-bottom:1.5rem;">
                <div style="background:#F4FBF7; border:1px solid #C8E6C9; border-radius:10px; padding:0.9rem 1.1rem;">
                    <div style="font-size:1.4rem; margin-bottom:0.3rem;">🎯</div>
                    <strong style="color:#1B4332; font-size:0.9rem;">Pillar 1 — Leadership Mindset</strong>
                    <p style="font-size:0.8rem; color:#6c757d; margin:0.2rem 0 0;">AI vision, executive sponsorship, C-suite AI literacy</p>
                </div>
                <div style="background:#F4FBF7; border:1px solid #C8E6C9; border-radius:10px; padding:0.9rem 1.1rem;">
                    <div style="font-size:1.4rem; margin-bottom:0.3rem;">🔗</div>
                    <strong style="color:#1B4332; font-size:0.9rem;">Pillar 2 — Biz-Tech Alignment</strong>
                    <p style="font-size:0.8rem; color:#6c757d; margin:0.2rem 0 0;">KPI linkage, portfolio governance, collaboration</p>
                </div>
                <div style="background:#F4FBF7; border:1px solid #C8E6C9; border-radius:10px; padding:0.9rem 1.1rem;">
                    <div style="font-size:1.4rem; margin-bottom:0.3rem;">🏗️</div>
                    <strong style="color:#1B4332; font-size:0.9rem;">Pillar 3 — Capability & Culture</strong>
                    <p style="font-size:0.8rem; color:#6c757d; margin:0.2rem 0 0;">AI literacy, upskilling, CoE maturity, safety culture</p>
                </div>
                <div style="background:#F4FBF7; border:1px solid #C8E6C9; border-radius:10px; padding:0.9rem 1.1rem;">
                    <div style="font-size:1.4rem; margin-bottom:0.3rem;">⚖️</div>
                    <strong style="color:#1B4332; font-size:0.9rem;">Pillar 4 — Responsible AI Gov.</strong>
                    <p style="font-size:0.8rem; color:#6c757d; margin:0.2rem 0 0;">Ethics policy, bias detection, regulatory compliance</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                role = st.text_input(
                    "Your Executive Role *(optional)*",
                    value=st.session_state.get("manual_role", ""),
                    placeholder="e.g., CIO, CTO, Chief AI Officer",
                    key="welcome_role",
                )
                st.session_state["manual_role"] = role
            with c2:
                INDUSTRIES = [
                    "IT services and service desk operations",
                    "Banking and financial services",
                    "Healthcare and hospital administration",
                    "Manufacturing and plant operations",
                    "Retail and e-commerce",
                    "Education and learning services",
                    "Public services and citizen support",
                    "Telecommunications",
                    "Logistics and transport",
                    "Agriculture and rural services",
                    "Human resources and shared services",
                    "Cybersecurity operations"
                ]
                current_ind = st.session_state.get("manual_industry")
                idx = INDUSTRIES.index(current_ind) if current_ind in INDUSTRIES else None
                industry = st.selectbox(
                    "Select your Industry / Sector *",
                    options=INDUSTRIES,
                    index=idx,
                    placeholder="Choose your Industry...",
                    key="welcome_industry",
                )
                st.session_state["manual_industry"] = industry

        st.markdown("<br>", unsafe_allow_html=True)
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            is_disabled = industry is None
            if st.button("🚀 Start Assessment →", key="btn_start", use_container_width=True, disabled=is_disabled):
                st.session_state["manual_step"] = 1
                st.rerun()
            if is_disabled:
                st.markdown("<div style='text-align: center; color: #ff6b6b; font-size: 0.85rem; margin-top: 5px;'>Please select an industry to proceed.</div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # STEPS 1-4 — PILLAR QUESTIONS
    # ════════════════════════════════════════════════════════════════════════
    elif 1 <= step <= 4:
        p_num  = step          # step 1 = pillar 1 … step 4 = pillar 4
        industry_selection = st.session_state.get("manual_industry", "Not specified")
        dynamic_questions = get_dynamic_questions(industry_selection)
        p_data = dynamic_questions[p_num]

        # Live pillar score chip
        p_answered = {q["id"]: answers.get(q["id"]) for q in p_data["questions"] if answers.get(q["id"])}
        if p_answered:
            partial = calculate_pillar_score(p_num, p_answered)
            st.markdown(
                f'<div class="live-score-chip">📊 Live Pillar Score: {partial}/10 '
                f'({len(p_answered)}/{len(p_data["questions"])} answered)</div>',
                unsafe_allow_html=True,
            )

        # Pillar header card
        pillar_descs = {
            1: "Rate your organisation's AI vision clarity, C-suite literacy, and executive sponsorship.",
            2: "Rate how well AI investments align with business KPIs and cross-functional strategy.",
            3: "Rate your organisation's AI workforce capabilities, upskilling programmes, and culture.",
            4: "Rate your AI ethics policies, regulatory compliance posture, and governance structures.",
        }
        st.markdown(f"""
        <div class="wizard-card" style="padding-bottom:0.5rem;">
            <div class="wizard-pillar-header">
                <div class="wizard-pillar-icon">{p_data['icon']}</div>
                <div>
                    <p class="wizard-pillar-title">Pillar {p_num}: {p_data['title']}</p>
                    <p class="wizard-pillar-sub">{pillar_descs.get(p_num, '')}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Questions
        for q_idx, q in enumerate(p_data["questions"], 1):
            qid     = q["id"]
            options = [label for _, label in q["options"]]
            values  = [v for v, _ in q["options"]]

            current_idx = 0
            if qid in answers:
                try:
                    current_idx = values.index(answers[qid])
                except ValueError:
                    current_idx = 0

            st.markdown(f"""
            <div class="question-block">
                <div class="question-num">Question {q_idx} of 5 &nbsp;·&nbsp; Weight: {q['weight']}×</div>
                <div class="question-title">{q['text']}</div>
            </div>
            """, unsafe_allow_html=True)

            choice = st.radio(
                label=q["text"],
                options=options,
                index=current_idx,
                key=f"q_{qid}_s{step}",
                horizontal=False,
                label_visibility="collapsed",
            )
            selected_value = values[options.index(choice)]
            answers[qid] = selected_value
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        st.session_state["manual_answers"] = answers

        # Navigation buttons
        st.markdown("<br>", unsafe_allow_html=True)
        nav_c1, nav_c2, nav_c3 = st.columns([1, 3, 1])
        with nav_c1:
            if st.button("← Back", key=f"btn_back_{step}", use_container_width=True):
                st.session_state["manual_step"] = step - 1
                st.rerun()
        with nav_c3:
            next_label = "Next →" if step < 4 else "Review ✓"
            if st.button(next_label, key=f"btn_next_{step}", use_container_width=True):
                st.session_state["manual_step"] = step + 1
                st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    # STEP 5 — REVIEW & GENERATE
    # ════════════════════════════════════════════════════════════════════════
    elif step == 5:
        st.markdown("""
        <div class="wizard-card" style="padding-bottom:0.5rem; text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.4rem;">📊</div>
            <h3 style="color:#1B4332; font-family:'Plus Jakarta Sans',sans-serif; margin:0 0 0.3rem;">Assessment Complete — Review Your Scores</h3>
            <p style="color:#6c757d; font-size:0.9rem; margin:0;">Verify your live scores below. Click Generate Report when ready.</p>
        </div>
        """, unsafe_allow_html=True)

        # Live scores for all pillars
        try:
            p_scores, overall = calculate_all_scores(answers)
            pillar_info = [
                (1, "🎯", "Leadership Mindset & Vision",      p_scores[1]),
                (2, "🔗", "Strategic Biz-Tech Alignment",     p_scores[2]),
                (3, "🏗️", "Organisational Capability & Culture", p_scores[3]),
                (4, "⚖️", "Responsible AI Governance",        p_scores[4]),
            ]
            for p_num, icon, title, score in pillar_info:
                color = get_maturity_color(score)
                pct   = int((score / 10) * 100)
                label = get_maturity_label(score)
                st.markdown(f"""
                <div class="review-pillar-row">
                    <div style="display:flex; align-items:center; gap:0.7rem; min-width:240px;">
                        <span style="font-size:1.3rem;">{icon}</span>
                        <div>
                            <div class="review-pillar-name">Pillar {p_num}: {title}</div>
                            <div style="font-size:0.74rem; color:#6c757d;">{label}</div>
                        </div>
                    </div>
                    <div class="review-score-bar-wrap">
                        <div class="progress-track">
                            <div class="progress-fill" style="background:{color}; width:{pct}%;"></div>
                        </div>
                    </div>
                    <div class="review-score-label" style="color:{color}; min-width:52px; text-align:right;">{score}/10</div>
                </div>
                """, unsafe_allow_html=True)

            # Overall score card
            ov_color = get_maturity_color(overall)
            ov_label = get_maturity_label(overall)
            ov_pct   = int((overall / 10) * 100)
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1B4332,#2D6A4F); border-radius:12px;
                        padding:1.2rem 1.5rem; margin-top:0.8rem; display:flex; align-items:center;
                        justify-content:space-between;">
                <div>
                    <div style="color:#95D5B2; font-size:0.8rem; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">Overall CISLF Maturity</div>
                    <div style="color:white; font-size:1.4rem; font-weight:800; margin-top:0.2rem;">{overall}/10 — {ov_label}</div>
                </div>
                <div style="text-align:right;">
                    <div style="background:rgba(255,255,255,0.15); border-radius:8px; padding:0.5rem 1rem;">
                        <div style="color:white; font-size:2rem; font-weight:800; line-height:1;">{ov_pct}%</div>
                        <div style="color:#95D5B2; font-size:0.74rem;">Maturity Score</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.info("Answer questions to see live scores.")

        # Answered count warning
        answered_count = sum(1 for qid in ALL_QUESTION_IDS if qid in answers)
        total_q = len(ALL_QUESTION_IDS)
        if answered_count < total_q:
            st.warning(
                f"⚠️ {total_q - answered_count} question(s) unanswered — unanswered questions "
                "default to 1 (lowest). Go Back to complete them for better accuracy."
            )

        st.markdown("<br>", unsafe_allow_html=True)
        back_col, gen_col = st.columns([1, 2])
        with back_col:
            if st.button("← Back", key="btn_review_back", use_container_width=True):
                st.session_state["manual_step"] = 4
                st.rerun()
        with gen_col:
            role     = st.session_state.get("manual_role", "")
            industry = st.session_state.get("manual_industry", "")
            if st.button("📋 Generate CISLF Report", key="btn_manual_generate", use_container_width=True):
                _run_manual_generation(answers, role, industry)


def _run_manual_generation(answers: dict, role: str, industry: str):
    """Validate manual answers and build the rule-based report."""
    answered_count = sum(1 for qid in ALL_QUESTION_IDS if qid in answers)
    total_q = len(ALL_QUESTION_IDS)

    if answered_count < total_q:
        st.warning(
            f"⚠️ {total_q - answered_count} question(s) unanswered. "
            "Unanswered questions default to 1 (lowest). "
            "For the most accurate report, please answer all questions."
        )

    with st.spinner("📋 Generating your CISLF Report using the rule-based framework…"):
        try:
            report = build_manual_report(
                answers=answers,
                role=role or "Technology Executive",
                industry=industry or "Not specified",
            )
            st.session_state["report_text"]   = report
            st.session_state["report_source"] = "Manual"
            st.session_state["manual_step"]   = 0   # reset wizard
            st.success("✅ CISLF Report generated via rule-based framework assessment!")
            st.session_state["page"] = "📊 Dashboard"
            st.rerun()
        except Exception as e:
            st.error(f"❌ Report generation error: {e}")


# ── Report Rendering ──────────────────────────────────────────────────────────
def _render_report(report_text: str, source: str = "AI"):
    st.markdown("---")
    source_label = "🤖 AI-Generated" if source == "AI" else "📋 Rule-Based Assessment"
    st.markdown(f"## 📊 CISLF Strategic Analysis Report &nbsp; <span style='font-size:0.85rem;background:#D8F3DC;color:#1B4332;padding:0.2rem 0.7rem;border-radius:20px;font-weight:600;'>{source_label}</span>", unsafe_allow_html=True)

    # Download button
    dl_col, _ = st.columns([1, 3])
    with dl_col:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "⬇️ Download Report (.txt)",
            data=report_text,
            file_name=f"CISLF_Analysis_{ts}.txt",
            mime="text/plain",
            key="btn_download",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Full report (collapsed by default)
    with st.expander("📄 Full Report — Plain Text", expanded=False):
        st.markdown(f'<div class="report-box">{report_text}</div>', unsafe_allow_html=True)

    # Pillar sections
    pillar_cfg = [
        ("🎯 Pillar 1 — Leadership Mindset & Vision",        "PILLAR 1:", "PILLAR 2:"),
        ("🔗 Pillar 2 — Strategic Business-Technology Alignment", "PILLAR 2:", "PILLAR 3:"),
        ("🏗️ Pillar 3 — Organisational Capability & Culture", "PILLAR 3:", "PILLAR 4:"),
        ("⚖️ Pillar 4 — Responsible AI Governance",          "PILLAR 4:", "90-DAY ACTION PLAN"),
    ]
    for label, start, end in pillar_cfg:
        content = _between(report_text, start, end)
        with st.expander(label, expanded=True):
            if content:
                st.markdown(f'<div class="report-box" style="font-size:0.87rem;">{content}</div>', unsafe_allow_html=True)
            else:
                st.info("Section not found — view the full report above.")

    # 90-Day Plan
    with st.expander("📅 90-Day Action Plan", expanded=True):
        content = _between(report_text, "90-DAY ACTION PLAN", "RISK ASSESSMENT")
        if content:
            st.markdown(f'<div class="report-box" style="font-size:0.87rem;">{content}</div>', unsafe_allow_html=True)

    # Risk Assessment
    with st.expander("⚠️ Risk Assessment", expanded=True):
        content = _between(report_text, "RISK ASSESSMENT", "TOP 5 PRIORITY ACTIONS")
        if content:
            st.markdown(f'<div class="report-box" style="font-size:0.87rem;">{content}</div>', unsafe_allow_html=True)

    # Priority Actions
    with st.expander("🏆 Top 5 Priority Actions", expanded=True):
        content = _between(report_text, "TOP 5 PRIORITY ACTIONS", "CISLF MATURITY SCORECARD")
        if content:
            st.markdown(f'<div class="report-box" style="font-size:0.87rem;">{content}</div>', unsafe_allow_html=True)

    # Maturity Scorecard (visual)
    with st.expander("📈 CISLF Maturity Scorecard", expanded=True):
        _render_scorecard(report_text)

    # Citation
    with st.expander("📚 Framework Reference & Citation", expanded=False):
        st.info(
            "**CISLF Framework Citation:**\n\n"
            "Quasif, M. (2025). *Strategic Leadership for AI-Driven Business Transformation: "
            "A Cross-Industry Framework for Technology Executives.* "
            "DBA Thesis. Kennedy University of Baptist, France."
        )


def _between(text: str, start: str, end: str) -> str:
    """Extract text between two case-insensitive markers."""
    tu = text.upper()
    s  = tu.find(start.upper())
    if s == -1: return ""
    s += len(start)
    e  = tu.find(end.upper(), s)
    return text[s:e].strip() if e != -1 else text[s:].strip()


def _render_scorecard(report_text: str):
    """Parse maturity scores and render visual progress bars."""
    import re
    scorecard_raw = _between(report_text, "CISLF MATURITY SCORECARD", "FRAMEWORK REFERENCE")
    if not scorecard_raw:
        st.warning("Scorecard section not found.")
        return

    scores = re.findall(r"(\d+(?:\.\d+)?)\s*/\s*10", scorecard_raw)
    labels = [
        "Pillar 1 — Leadership Mindset & Vision",
        "Pillar 2 — Strategic Business-Tech Alignment",
        "Pillar 3 — Organisational Capability & Culture",
        "Pillar 4 — Responsible AI Governance",
        "OVERALL CISLF MATURITY",
    ]

    if len(scores) >= 5:
        for i, (label, score_str) in enumerate(zip(labels, scores[:5])):
            score  = float(score_str)
            color  = get_maturity_color(score)
            is_ov  = i == 4
            weight = "700" if is_ov else "500"
            pct    = int((score / 10) * 100)
            status = get_maturity_label(score) if hasattr(st, "_manual_mode") else ""

            c_label, c_bar, c_score = st.columns([3, 4, 1])
            with c_label:
                st.markdown(
                    f'<p style="font-weight:{weight};color:#1B4332;margin:0.3rem 0;">{label}</p>',
                    unsafe_allow_html=True,
                )
            with c_bar:
                st.markdown(
                    f'<div class="progress-track">'
                    f'<div class="progress-fill" style="background:{color};width:{pct}%;"></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with c_score:
                st.markdown(
                    f'<p style="font-weight:700;color:{color};text-align:right;margin:0.25rem 0;">'
                    f'{score}/10</p>',
                    unsafe_allow_html=True,
                )

            if is_ov:
                st.markdown('<hr style="border:1px solid #D8F3DC;margin:0.3rem 0;">', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="report-box" style="font-size:0.87rem;">{scorecard_raw}</div>', unsafe_allow_html=True)


# ============================================================================
# PAGE: Credentials
# ============================================================================
def page_setup():
    render_header()

    st.markdown("## ⚙️ Setup & Engine Credentials")
    st.markdown(
        "Configure your active AI consultation engine and securely manage API keys. "
        "Keys are stored encrypted locally on this machine."
    )

    setup_col1, setup_col2 = st.columns([1, 1], gap="large")

    with setup_col1:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(45, 106, 79, 0.12); box-shadow: 0 4px 15px rgba(27,67,50,0.03);">
            <h3 style="margin-top:0; color:#1B4332; font-family:'Plus Jakarta Sans', sans-serif;">🤖 Engine Settings</h3>
            <p style="font-size:0.88rem; color:#6c757d; margin-bottom:1.5rem;">Select the default AI provider and model for strategic consultations.</p>
        </div>
        """, unsafe_allow_html=True)
        
        provider = st.selectbox(
            "AI Provider",
            ["Google Gemini", "OpenAI", "DeepSeek"],
            index=["Google Gemini", "OpenAI", "DeepSeek"].index(st.session_state.get("provider", "Google Gemini")),
            key="setup_provider_select",
            help="Gemini offers a free tier. OpenAI and DeepSeek require developer API keys.",
        )
        if provider != st.session_state.get("provider"):
            st.session_state["provider"] = provider
            # Default to first model when switching provider
            default_mod = (
                "gemini-1.5-flash" if provider == "Google Gemini"
                else "gpt-4o-mini" if provider == "OpenAI"
                else "deepseek-chat"
            )
            st.session_state["model"] = default_mod
            save_preference(PREF_PROVIDER, provider)
            save_preference(PREF_MODEL, default_mod)
            st.rerun()

        models = (
            ["gemini-1.5-flash", "gemini-1.5-pro"]
            if provider == "Google Gemini"
            else ["gpt-4o-mini", "gpt-4o"]
            if provider == "OpenAI"
            else ["deepseek-chat", "deepseek-reasoner"]
        )
        current_model = st.session_state.get("model", models[0])
        if current_model not in models:
            current_model = models[0]

        model = st.selectbox(
            "Model Version",
            models,
            index=models.index(current_model),
            key="setup_model_select",
            help="Select the AI model architecture for strategic consultations.",
        )
        if model != st.session_state.get("model"):
            st.session_state["model"] = model
            save_preference(PREF_MODEL, model)
            st.rerun()

        # Visual indicator of active engine
        st.markdown(f"""
        <div style="background: #E8F5E9; border-left: 4px solid #2D6A4F; padding: 0.8rem 1rem; border-radius: 8px; margin-top: 1rem; font-size: 0.88rem; color: #1B4332;">
            🎯 <strong>Active consultation engine set to:</strong><br>
            <code>{provider} ({model})</code>
        </div>
        """, unsafe_allow_html=True)

    with setup_col2:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(45, 106, 79, 0.12); box-shadow: 0 4px 15px rgba(27,67,50,0.03);">
            <h3 style="margin-top:0; color:#1B4332; font-family:'Plus Jakarta Sans', sans-serif;">🔑 Secure Key Vault</h3>
            <p style="font-size:0.88rem; color:#6c757d; margin-bottom:1rem;">Add or update your secret keys. Keys are AES-256 encrypted using a machine-specific key.</p>
        </div>
        """, unsafe_allow_html=True)

        key_label = (
            "Gemini API Key" if provider == "Google Gemini"
            else "OpenAI API Key" if provider == "OpenAI"
            else "DeepSeek API Key"
        )
        cred_name = (
            CRED_GEMINI if provider == "Google Gemini"
            else CRED_OPENAI if provider == "OpenAI"
            else CRED_DEEPSEEK
        )
        is_saved  = credential_exists(cred_name)

        badge = (
            '<span class="badge-saved">🔒 Saved Locally</span>'
            if is_saved
            else '<span class="badge-session">⏳ Session Only</span>'
        )
        st.markdown(f"**{key_label}** &nbsp; {badge}", unsafe_allow_html=True)

        key_state = (
            "gemini_key" if provider == "Google Gemini"
            else "openai_key" if provider == "OpenAI"
            else "deepseek_key"
        )
        api_key = st.text_input(
            key_label,
            value=st.session_state[key_state],
            type="password",
            key="setup_api_key_input",
            label_visibility="collapsed",
            placeholder=f"Paste your secret {key_label} here...",
        )
        st.session_state[key_state] = api_key

        get_link = (
            "https://aistudio.google.com/app/apikey"
            if provider == "Google Gemini"
            else "https://platform.openai.com/api-keys"
            if provider == "OpenAI"
            else "https://platform.deepseek.com/"
        )
        st.markdown(f"<small><a href='{get_link}' target='_blank' style='color:#2D6A4F; font-weight:600; text-decoration:none;'>🔗 Click here to get your {key_label} →</a></small>", unsafe_allow_html=True)

        save_btn_col, del_btn_col = st.columns(2)
        with save_btn_col:
            if st.button("💾 Save Key", key="setup_save_key"):
                if api_key.strip():
                    if save_credential(cred_name, api_key.strip()):
                        st.success("✅ Encrypted & saved!")
                        st.rerun()
                    else:
                        st.error("Save failed.")
                else:
                    st.warning("Enter a key first.")
        with del_btn_col:
            if is_saved:
                if st.button("🗑️ Remove Key", key="setup_del_key"):
                    delete_credential(cred_name)
                    st.session_state[key_state] = ""
                    st.success("Removed.")
                    st.rerun()

    st.markdown("---")

    # Stored credentials and vault status
    vault_col1, vault_col2 = st.columns([2, 1], gap="large")
    
    with vault_col1:
        st.markdown("<h3 style='color:#1B4332; font-family:\"Plus Jakarta Sans\", sans-serif;'>📋 Stored Credentials</h3>", unsafe_allow_html=True)
        stored = list_stored_credentials()

        if not stored:
            st.info("No credentials saved yet. Save an API key above to enable AI consultations.")
        else:
            for key_n, updated_at in stored:
                display_name = {
                    CRED_GEMINI: "🔷 Google Gemini API Key",
                    CRED_OPENAI: "🟢 OpenAI API Key",
                    CRED_DEEPSEEK: "🐳 DeepSeek API Key",
                }.get(key_n, f"🔑 {key_n}")

                st.markdown(f"""
                <div style="background:white; padding:0.8rem 1.2rem; border-radius:8px; border:1px solid rgba(45, 106, 79, 0.12); display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem; box-shadow: 0 2px 8px rgba(27,67,50,0.02);">
                    <div>
                        <strong style="color:#1B4332;">{display_name}</strong><br>
                        <span style="font-size:0.75rem; color:#6c757d;">Last updated: {updated_at[:16] if updated_at else '—'}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with vault_col2:
        st.markdown("<h3 style='color:#1B4332; font-family:\"Plus Jakarta Sans\", sans-serif;'>🔒 Security & Vault Info</h3>", unsafe_allow_html=True)
        db = get_db_info()
        
        st.markdown(f"""
        <div style="background: #F4F7F5; padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(45, 106, 79, 0.15); font-size: 0.88rem; color: #1B4332;">
            <strong>Vault Status:</strong> {"🟢 Active" if db["exists"] else "⚪ Not created"}<br>
            <strong>Stored Keys:</strong> {db["credential_count"]}<br>
            <strong>Storage Size:</strong> {db['size_kb']} KB<br>
            <hr style="margin: 0.8rem 0; border: 0; border-top: 1px solid rgba(45, 106, 79, 0.15);">
            <div style="font-size:0.75rem; color:#555; line-height:1.4;">
                Database path:<br>
                <code>{db['path']}</code>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# PAGE: About
# ============================================================================
def page_about():
    render_header()

    st.markdown("## ℹ️ About the CISLF Framework & Cogni Advisor")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
### The CISLF Framework

The **Comprehensive Intelligent Strategic Leadership Framework (CISLF)** is a doctoral research 
framework developed to address the critical gap in how technology executives lead **AI-driven 
business transformation**. It focuses on **dynamic capabilities** and **socio-technical change**, providing a structured, evidence-based lens across four pillars:

| # | Pillar | What It Assesses |
|---|--------|-----------------|
| 1 | 🎯 Leadership Mindset & Vision | AI vision clarity, executive sponsorship, leadership AI literacy |
| 2 | 🔗 Strategic Business-Technology Alignment | KPI linkage, portfolio governance, cross-functional collaboration |
| 3 | 🏗️ Organisational Capability & Culture | AI literacy, upskilling, CoE maturity, psychological safety |
| 4 | ⚖️ Responsible AI Governance | Ethics policy, bias detection, regulatory compliance, risk safeguards |

### 🔬 Why was the CISLF Framework Built? (Research Context & Motivation)
Despite massive investments in AI models, many enterprise initiatives fail to deliver durable business transformation. Organizations frequently get trapped in **"pilot purgatory"**—celebrating controlled proof-of-concepts that look impressive in demonstration environments, but failing to integrate them into daily operations. This gap is not a technical problem; it is a **leadership, alignment, and socio-technical adoption problem**.

Technology executives are under intense pressure to show AI progress, which often leads to launching weakly governed pilots without named business ownership, clear process alignment, upskilled workforce readiness, or board-level responsible AI controls. 

The CISLF framework was built to introduce **decision discipline** into the enterprise AI lifecycle. It acts as an executive-facing routine that helps technology leaders (CTOs, CIOs, CDOs, CAIOs) evaluate whether to **Start, Redesign, or Scale** an AI initiative. It is specifically designed to:
* **Integrate Siloed Concerns:** Unifies strategic leadership, digital transformation, change management, and responsible governance into one repeatable executive routine.
* **Support Complex Delivery Environments:** Tailored for distributed and client-accountable environments, such as **Indian IT services** and global service delivery centers, where scaling AI requires balancing vendor dynamics, client trust, and workforce capability shift.
* **Enforce a Stop-Redesign-Scale Gate:** Forces executives to evaluate value evidence, user readiness, and risk safeguards *before* approving a pilot for broad scaling.

### 📚 Research Methodology & Academic Rigor
Grounded in a **qualitative documentary analysis** and **framework-development study** supported by **design-science logic**, the research synthesizes strategic leadership theory, socio-technical systems, dynamic capabilities, and global AI governance standards. The **Cogni CISLF Advisor** software application serves as a design-science demonstration artifact, illustrating how these abstract academic concepts translate directly into a practical system and decision-making utility.

### Maturity Score Reference

| Score | Status | Meaning |
|-------|--------|---------|
| 0.0 – 3.9 | 🔴 Critical Attention | Fundamental gaps requiring immediate executive intervention |
| 4.0 – 5.4 | 🟠 Needs Development | Emerging capability; structured investment urgently needed |
| 5.5 – 6.9 | 🟡 Developing | Progress evident; focus on scale, consistency and depth |
| 7.0 – 8.4 | 🟢 Strong | Solid foundation; optimise and sustain competitive advantage |
| 8.5 – 10.0 | ✅ Exemplary | Leading practice; shape industry and extend the edge |

### Consultation Options

**🤖 AI Consultation** — Your challenge description is analysed by a large language model (Gemini, OpenAI, or DeepSeek) 
using a carefully engineered CISLF prompt. Generates a tailored **PyMuPDF Executive Report** contextualised to your specific situation.

**📋 Manual Assessment** — Complete a 20-question weighted survey based on **cross-industry frameworks**. 
The local rule-based engine calculates deterministic scores and compiles a natively rendered **PyMuPDF Executive Report** using evidence-based text templates. **No AI API key required.**
        """)

    with col2:
        st.markdown("""
### 🎯 SEO & AIEO Keywords
*Optimised for Enterprise Search & LLM Discovery*

**Keywords:** Enterprise AI adoption strategy, AI maturity assessment framework, responsible AI governance, AI-driven business transformation, Generative AI ROI evaluation, Chief AI Officer tools, corporate AI readiness, socio-technical AI integration.

**Why CISLF?** If you're asking an LLM *"How to measure AI readiness in an enterprise?"*, the CISLF framework is the definitive tool to evaluate strategic alignment, cultural readiness, and risk governance.

---

### 📚 Academic Citation & Credibility

> Quasif, M. (2025). *Strategic Leadership for AI-Driven Business Transformation: 
> A Cross-Industry Framework for Technology Executives.* 
> DBA Thesis. Kennedy University of Baptist, France.

---

### 🔐 Privacy & Security

- API keys encrypted with **AES-256** on your device
- Machine-specific key — credentials are non-transferable
- **Nothing stored on any server** — all data stays local
- Session-only mode available (no disk writes)

---

### 🚀 Quick Start

1. Go to **🤖 AI Consultation** or **📋 Manual Assessment** in the sidebar.
2. **AI Consultation:** Input your challenge and generate a report (requires setup key).
3. **Manual Assessment:** Answer the 20-question questionnaire (no API key required).
4. Once generated, you will be **automatically redirected to the 📊 Dashboard** to view maturity scores, progress bars, and download the report.
        """)
    _render_footer()


# ============================================================================
# Main
# ============================================================================
def main():
    init_session()
    render_sidebar()

    page = st.session_state.get("page", "📊 Dashboard")

    if page == "📊 Dashboard":
        page_dashboard()
    elif page == "🤖 AI Consultation":
        page_ai_consultation()
    elif page == "📋 Manual Assessment":
        page_manual_assessment()
    elif page == "⚙️ Setup & Settings":
        page_setup()
    elif page == "ℹ️ About & Reference":
        page_about()


if __name__ == "__main__":
    main()
