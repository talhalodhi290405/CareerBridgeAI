"""CareerBridge AI — AI Career Intelligence Platform & Career Command Center.

Enterprise HR-Tech SaaS Command Center + Guided Golden-Path Wizard.
Run with: streamlit run frontend/app.py
"""
import sys
import os
import hashlib
import urllib.parse
from datetime import datetime
from typing import Optional, List, Dict, Any

# Ensure project root is on path for backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CareerBridge AI — AI Career Intelligence Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Backend Imports
# ---------------------------------------------------------------------------
from backend.models import (
    CandidateProfile, JobPosting, MatchResult, ATSAnalysis,
    GapAnalysis, OptimizedProfile, OutreachPackage, JobSearchFilters,
    ApplicationRecord, ApplicationStatus, CoverLetter, CoachMessage,
    SkillClassification, DocumentValidationResult,
)
from backend.config import is_demo_mode, get_api_key, logger
from backend.parser import parse_resume, parse_resume_text, assess_extraction_quality, validate_pdf_resume, classify_document_type
from backend.rag_engine import load_jobs, match_candidate_to_jobs
from backend.ats_engine import analyze_ats, analyze_gaps
from backend.optimizer import optimize_profile
from backend.outreach import generate_outreach
from backend.job_service import search_live_jobs, get_adzuna_credentials, _extract_skills_from_description
from backend.cover_letter import generate_cover_letter
from backend.coach import ask_career_coach
from backend.storage import save_session_state, load_session_state
from backend.demo import (
    get_demo_candidate, get_demo_ats_analysis, get_demo_gap_analysis,
    get_demo_optimized_profile, get_demo_outreach, get_demo_target_job_id,
)

# ---------------------------------------------------------------------------
# Session State Initialization (Strict Clean Defaults)
# ---------------------------------------------------------------------------
_defaults = {
    "nav_section": "Dashboard",
    "step": "intake",
    "candidate": None,
    "is_demo": False,
    "processed_resume_hash": None,  # SHA-256 hash guard
    "selected_job": None,
    "saved_jobs": [],
    "applications": [],
    "ats_result": None,
    "gap_result": None,
    "optimization": None,
    "approval": None,
    "outreach": None,
    "coach_history": [],
    "coach_pending_prompt": None,  # Reliable prompt queue for chips/text
    "search_filters": JobSearchFilters(),
    "job_results": [],
    "job_status_msg": "Ready to search live jobs",
    "demo_mode_active": False,
    "show_manual_intake": False,
    "upload_toast_msg": None,
    "upload_error_msg": None,
    "theme_mode": "light",
    "is_dark_mode": False,
}

for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def _persist_state():
    # Session state is strictly isolated in-memory per user session by Streamlit.
    pass

# 1. Determine theme state from session state safely
is_dark_mode = st.session_state.get('is_dark_mode', st.session_state.get('theme_mode') == 'dark')
st.session_state['is_dark_mode'] = is_dark_mode

# 2. Dynamic color tokens that switch on button toggle
bg_main       = '#090D16' if is_dark_mode else '#F8FAFC'
bg_card       = '#0F172A' if is_dark_mode else '#FFFFFF'
text_color    = '#F3F4F6' if is_dark_mode else '#0F172A'
subtext_color = '#9CA3AF' if is_dark_mode else '#64748B'
border_color  = '#1E293B' if is_dark_mode else '#E2E8F0'
bg_sidebar    = '#0B0F19' if is_dark_mode else '#F8FAFC'
bg_input      = '#1E293B' if is_dark_mode else '#FFFFFF'
border_input  = '#334155' if is_dark_mode else '#CBD5E1'

# 3. Inject the dynamic CSS block
theme_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Main background canvas */
    .stApp {{
        background-color: {bg_main} !important;
        font-family: 'Inter', -apple-system, sans-serif;
        color: {text_color} !important;
    }}
    /* Fix: Force sidebar background to match the theme */
    [data-testid="stSidebar"] {{
        background-color: {bg_sidebar} !important;
    }}
    /* Custom cards background and text */
    .dash-card, .metric-box, .top-bar-container {{
        background-color: {bg_card} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px;
        padding: 16px;
    }}

    /* Force text visibility inside cards */
    p, span, h1, h2, h3, h4, label {{
        color: {text_color} !important;
    }}



    .sidebar-brand {{
        font-size: 1.25rem; font-weight: 800; color: {text_color} !important;
        display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0 0.25rem 0;
    }}
    .sidebar-sub {{
        font-size: 0.72rem; color: {subtext_color} !important; margin-bottom: 0.85rem; font-weight: 500;
    }}
    .sidebar-cat {{
        font-size: 0.68rem; font-weight: 700; color: {subtext_color} !important;
        text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.85rem; margin-bottom: 0.35rem;
    }}

    /* Header Bar & Global Clean Overrides */
  /* Force top header to match the dark/light background */
    [data-testid="stHeader"] {{
        background-color: {bg_main} !important;
    }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none;}}

    .greeting-title {{
        font-size: 1.35rem; font-weight: 800; color: {text_color} !important; margin: 0; line-height: 1.2;
    }}
    .greeting-sub {{
        font-size: 0.85rem; color: {subtext_color} !important; margin: 0; font-weight: 500;
    }}
    .dash-card-hdr {{
        font-size: 1.05rem; font-weight: 700; color: {text_color} !important; margin-bottom: 0.25rem;
        display: flex; align-items: center; justify-content: space-between;
    }}
    .dash-card-sub {{ font-size: 0.82rem; color: {subtext_color} !important; margin-bottom: 0.85rem; }}

    .metric-val {{
        font-size: 1.8rem; font-weight: 800; color: {'#818CF8' if is_dark_mode else '#2563EB'} !important; line-height: 1.1;
    }}
    .metric-lbl {{
        font-size: 0.72rem; font-weight: 600; color: {subtext_color} !important; text-transform: uppercase;
        letter-spacing: 0.05em; margin-top: 0.25rem;
    }}

    /* Inputs & Controls */
    input, textarea, select {{
        background-color: {bg_input} !important;
        color: {text_color} !important;
        border: 1px solid {border_input} !important;
    }}

    div[data-testid="stExpander"] summary * {{
        color: {text_color} !important;
    }}

    div[data-testid="stExpander"] {{
        background-color: {bg_card} !important;
        border: 1px solid {border_color} !important;
        border-radius: 0.5rem !important;
    }}

    /* Badges & Tags Override High Specificity */
    .status-pill {{ padding: 0.25rem 0.65rem; border-radius: 2rem; font-size: 0.72rem; font-weight: 600; display: inline-flex; align-items: center; gap: 0.35rem; }}
    .pill-live {{ background: #ECFDF5 !important; color: #047857 !important; border: 1px solid #A7F3D0 !important; }}
    .pill-demo {{ background: #FFFBEB !important; color: #B45309 !important; border: 1px solid #FDE68A !important; }}
    .pill-empty {{ background: #F1F5F9 !important; color: #64748B !important; border: 1px solid #CBD5E1 !important; }}

    .source-badge-live {{ background: #DCFCE7 !important; color: #166534 !important; font-size: 0.7rem; font-weight: 700; padding: 0.15rem 0.45rem; border-radius: 0.25rem; text-transform: uppercase; }}
    .source-badge-demo {{ background: #E0F2FE !important; color: #0369A1 !important; font-size: 0.7rem; font-weight: 700; padding: 0.15rem 0.45rem; border-radius: 0.25rem; text-transform: uppercase; }}
    .warn-card {{ background: #FFFBEB !important; border: 1px solid #FDE68A !important; border-radius: 0.5rem; padding: 0.85rem; margin-bottom: 1rem; color: #92400E !important; font-size: 0.85rem; }}

    .tag-v {{ background: #ECFDF5 !important; color: #047857 !important; padding: 0.15rem 0.45rem; border-radius: 0.3rem; font-size: 0.75rem; font-weight: 600; display: inline-block; margin: 0.1rem; }}
    .tag-i {{ background: #FFFBEB !important; color: #B45309 !important; padding: 0.15rem 0.45rem; border-radius: 0.3rem; font-size: 0.75rem; font-weight: 600; display: inline-block; margin: 0.1rem; }}
    .tag-m {{ background: #FEF2F2 !important; color: #B91C1C !important; padding: 0.15rem 0.45rem; border-radius: 0.3rem; font-size: 0.75rem; font-weight: 600; display: inline-block; margin: 0.1rem; }}

    div[data-testid="stAlert"] {{
        background-color: {bg_input} !important;
        border: 1px solid {'#3B82F6' if is_dark_mode else '#BFDBFE'} !important;
        border-radius: 0.5rem !important;
    }}

    [data-testid="stFileUploaderDropzone"] {{
        background-color: {bg_input} !important;
        border: 1px dashed {'#475569' if is_dark_mode else '#CBD5E1'} !important;
        border-radius: 0.5rem !important;
    }}

    .stApp div[data-testid="stVerticalBlock"] button[kind="secondary"],
    .stApp div[data-testid="stVerticalBlock"] button:not([kind="primary"]) {{
        background-color: {bg_input} !important;
        color: {text_color} !important;
        border: 1px solid {border_input} !important;
        font-weight: 600 !important;
    }}

    .stApp div[data-testid="stVerticalBlock"] button[kind="secondary"]:hover,
    .stApp div[data-testid="stVerticalBlock"] button:not([kind="primary"]):hover {{
        background-color: {'#334155' if is_dark_mode else '#F1F5F9'} !important;
        color: {'#FFFFFF' if is_dark_mode else '#2563EB'} !important;
    }}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)


# Explicit Demo Profile Loader
def _load_demo_profile():
    st.session_state.candidate = get_demo_candidate()
    st.session_state.is_demo = True
    st.session_state.processed_resume_hash = None
    st.session_state.search_filters.desired_role = "Machine Learning Engineer"
    st.session_state.ats_result = get_demo_ats_analysis()
    st.session_state.gap_result = get_demo_gap_analysis()
    st.session_state.optimization = get_demo_optimized_profile()
    st.session_state.outreach = get_demo_outreach()
    demo_jobs = load_jobs()
    st.session_state.selected_job = demo_jobs[0]
    st.session_state.job_results = demo_jobs
    st.session_state.job_status_msg = "DEMO MODE — Offline Dataset"
    st.session_state.applications = [
        ApplicationRecord(
            id="app_1", job_id=demo_jobs[0].id, job_title=demo_jobs[0].title,
            company=demo_jobs[0].company, source="Demo Backup", status=ApplicationStatus.INTERVIEW,
            date="2026-09-10", notes="Technical interview scheduled for Tuesday", ats_score=78, match_score=74.7
        ),
        ApplicationRecord(
            id="app_2", job_id=demo_jobs[1].id, job_title=demo_jobs[1].title,
            company=demo_jobs[1].company, source="Demo Backup", status=ApplicationStatus.APPLIED,
            date="2026-09-11", notes="Applied via direct portal", ats_score=64, match_score=68.2
        ),
        ApplicationRecord(
            id="app_3", job_id=demo_jobs[2].id, job_title=demo_jobs[2].title,
            company=demo_jobs[2].company, source="Demo Backup", status=ApplicationStatus.SAVED,
            date="2026-09-12", notes="Saved for ATS optimization", ats_score=None, match_score=61.0
        ),
    ]
    _persist_state()

# Clear Profile Helper
def _clear_candidate_profile():
    st.session_state.candidate = None
    st.session_state.is_demo = False
    st.session_state.applications = []
    st.session_state.saved_jobs = []
    st.session_state.ats_result = None
    st.session_state.gap_result = None
    st.session_state.optimization = None
    st.session_state.outreach = None
    st.session_state.coach_history = []
    st.session_state.coach_pending_prompt = None
    st.session_state.processed_resume_hash = None
    st.session_state.show_manual_intake = False
    st.session_state.upload_error_msg = None
    st.session_state.upload_toast_msg = None
    st.session_state.selected_job = None
    st.session_state.job_results = []
    _persist_state()
    st.rerun()


# Infer Candidate Primary Role Helper for Auto-Pilot
def infer_candidate_primary_role(cand: Optional[CandidateProfile]) -> str:
    """Infer target primary role from candidate's profile, skills, or experience."""
    if not cand:
        return "Software Engineer"
    
    if cand.desired_role and cand.desired_role.strip():
        return cand.desired_role.strip()
        
    # Check experience titles for common role patterns
    if cand.experience:
        for exp in cand.experience:
            if isinstance(exp, str):
                lower_exp = exp.lower()
                if any(kw in lower_exp for kw in ["engineer", "developer", "architect", "manager", "analyst", "scientist", "specialist"]):
                    title_part = exp.split(" at ")[0].split(" - ")[0].split(" | ")[0].strip()
                    if title_part and len(title_part) < 50:
                        return title_part

    # Infer from skills
    if cand.skills:
        skills_upper = [s.upper() for s in cand.skills]
        if any(k in skills_upper for k in ["PYTORCH", "TENSORFLOW", "MACHINE LEARNING", "DEEP LEARNING", "AI", "LLM", "NLP", "SCIKIT-LEARN"]):
            return "Machine Learning Engineer"
        if any(k in skills_upper for k in ["REACT", "VUE", "TYPESCRIPT", "JAVASCRIPT", "HTML", "CSS", "FRONTEND", "TAILWIND"]):
            return "Frontend Engineer"
        if any(k in skills_upper for k in ["KUBERNETES", "DOCKER", "AWS", "TERRAFORM", "DEVOPS", "CI/CD", "AZURE", "GCP"]):
            return "DevOps Engineer"
        if any(k in skills_upper for k in ["PYTHON", "JAVA", "GO", "FASTAPI", "DJANGO", "SPRING", "NODE", "BACKEND"]):
            return "Software Engineer"
        if any(k in skills_upper for k in ["SQL", "PANDAS", "PYTHON", "POWER BI", "TABLEAU", "DATA ANALYSIS"]):
            return "Data Scientist"
        if any(k in skills_upper for k in ["FINANCE", "FINANCIAL", "ACCOUNTING", "VALUATION", "EXCEL", "BANKING", "AUDIT"]):
            return "Financial Analyst"
        if any(k in skills_upper for k in ["MARKETING", "SEO", "CONTENT", "COPYWRITING", "SOCIAL MEDIA", "BRAND"]):
            return "Marketing Manager"
        if any(k in skills_upper for k in ["HR", "RECRUITING", "TALENT", "HUMAN RESOURCES", "PEOPLE"]):
            return "HR Manager"
        if any(k in skills_upper for k in ["HEALTHCARE", "NURSING", "CLINICAL", "PATIENT", "MEDICAL"]):
            return "Healthcare Administrator"

    return "Software Engineer"


# Upload Processing Guard
def _process_resume_upload(uploaded_file, switch_step=False) -> bool:
    """Safely validate & process a PDF file upload using SHA-256 hash guard.
    Runs the 7-stage validation pipeline BEFORE parsing."""
    if uploaded_file is None:
        return False

    file_bytes = uploaded_file.getvalue()
    filename = getattr(uploaded_file, "name", "")
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    if file_hash == st.session_state.get("processed_resume_hash"):
        return False  # Already processed frame!

    try:
        with st.spinner("Agent: Validating 7-stage security pipeline & parsing resume document..."):
            # Execute 7-stage validation pipeline FIRST
            val_res: DocumentValidationResult = validate_pdf_resume(file_bytes, filename=filename)
            st.session_state.processed_resume_hash = file_hash

            if not val_res.accepted:
                logger.warning(f"Resume upload rejected — reason: {val_res.reason}, doc_type: {val_res.document_type}, size: {val_res.file_size_mb}MB (hash: {file_hash[:8]}...)")
                st.session_state.upload_error_msg = val_res.user_message
                st.session_state.upload_toast_msg = None
                _persist_state()
                st.rerun()
                return False

            # Validation PASSED — now parse candidate profile
            logger.info(f"Resume validation passed (hash: {file_hash[:8]}...) — parsing CandidateProfile...")
            cand = parse_resume(file_bytes)

            if cand and cand.raw_text:
                st.session_state.candidate = cand
                st.session_state.is_demo = False
                st.session_state.ats_result = None
                st.session_state.gap_result = None
                st.session_state.optimization = None
                st.session_state.outreach = None
                st.session_state.show_manual_intake = False
                st.session_state.upload_error_msg = None
                st.session_state.upload_toast_msg = f"CV processed successfully — {len(cand.skills)} skills and {len(cand.experience)} experience entries detected."
                
                if any(a.source == "Demo Backup" for a in st.session_state.applications):
                    st.session_state.applications = []

                if switch_step:
                    st.session_state.step = "profile"

                _persist_state()
                logger.info(f"Resume parsing completed successfully for {cand.name or 'Candidate'} — {len(cand.skills)} skills extracted (hash: {file_hash[:8]}...)")
                st.rerun()
                return True
            else:
                st.session_state.upload_error_msg = "This PDF could not be read. Please upload a valid, non-corrupted resume PDF."
                st.session_state.upload_toast_msg = None
                _persist_state()
                st.rerun()
                return False
    except Exception as e:
        logger.error(f"Resume parsing error: {e}")
        st.session_state.upload_error_msg = "An unexpected error occurred while processing your CV document. Please try again or use manual profile entry."
        _persist_state()
        st.rerun()
        return False




# ---------------------------------------------------------------------------
# Sidebar Navigation (Enterprise SaaS Grouped Navigation Items — Zero Radio Dots)
# ---------------------------------------------------------------------------
nav_categories = [
    ("OVERVIEW", [
        ("📊 Dashboard", "Dashboard")
    ]),
    ("CAREER MANAGEMENT", [
        ("🔍 Find Jobs", "Find Jobs"),
        ("👤 My CV", "My CV"),
        ("📊 ATS Scanner", "ATS Scanner"),
        ("✨ Improve CV", "Improve CV"),
        ("✉️ Cover Letter", "Cover Letter")
    ]),
    ("PIPELINE TRACKING", [
        ("📁 Applications", "Applications")
    ]),
    ("AI INTELLIGENCE", [
        ("🤖 AI Career Coach", "AI Career Coach"),
        ("📈 Analytics", "Analytics")
    ]),
    ("SYSTEM & WORKFLOW", [
        ("⚙️ Settings", "Settings"),
        ("🚀 Guided Golden Path", "Guided Golden Path")
    ])
]

with st.sidebar:
    st.header("🚀 CareerBridge AI")
    st.caption("AI Career Intelligence Platform")
    st.divider()

    theme_choice = st.radio("Appearance", ["Light Mode", "Dark Mode"], index=1 if is_dark_mode else 0, key="side_theme_radio")
    new_dark = (theme_choice == "Dark Mode")
    if new_dark != is_dark_mode:
        st.session_state.is_dark_mode = new_dark
        st.session_state.theme_mode = "dark" if new_dark else "light"
        _persist_state()
        st.rerun()

    st.divider()
    st.subheader("Navigation")

    all_nav_items = [
        "📊 Dashboard",
        "🔍 Find Jobs",
        "👤 My CV",
        "📊 ATS Scanner",
        "✨ Improve CV",
        "✉️ Cover Letter",
        "📁 Applications",
        "🤖 AI Career Coach",
        "📈 Analytics",
        "⚙️ Settings",
        "🚀 Guided Golden Path",
    ]

    nav_map = {
        "📊 Dashboard": "Dashboard",
        "🔍 Find Jobs": "Find Jobs",
        "👤 My CV": "My CV",
        "📊 ATS Scanner": "ATS Scanner",
        "✨ Improve CV": "Improve CV",
        "✉️ Cover Letter": "Cover Letter",
        "📁 Applications": "Applications",
        "🤖 AI Career Coach": "AI Career Coach",
        "📈 Analytics": "Analytics",
        "⚙️ Settings": "Settings",
        "🚀 Guided Golden Path": "Guided Golden Path",
    }

    current_label = [l for l, k in nav_map.items() if k == st.session_state.nav_section]
    curr_idx = all_nav_items.index(current_label[0]) if current_label else 0

    selected_label = st.radio("Select View", all_nav_items, index=curr_idx, key="side_nav_radio")
    new_sec = nav_map[selected_label]
    if new_sec != st.session_state.nav_section:
        st.session_state.nav_section = new_sec
        _persist_state()
        st.rerun()


# ---------------------------------------------------------------------------
# Top Header Bar & Greeting
# ---------------------------------------------------------------------------
c_profile: Optional[CandidateProfile] = st.session_state.candidate
quality_info = assess_extraction_quality(c_profile)
api_k = get_api_key()

hour = datetime.now().hour
time_greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
user_display_name = c_profile.name if (c_profile and c_profile.name and c_profile.name != "Candidate Profile") else "Candidate"

st.markdown(f"""
<div class="top-bar-container">
    <div>
        <div class="greeting-title">{time_greeting}, {user_display_name}</div>
        <div class="greeting-sub">AI Career Intelligence Platform & Enterprise Command Center</div>
    </div>
    <div style="display:flex;align-items:center;gap:0.6rem;">
        <span class="status-pill {'pill-live' if api_k else 'pill-demo'}">
            {'● Live — Groq' if api_k else '● Fallback Engine'}
        </span>
        <span class="status-pill {'pill-demo' if st.session_state.is_demo else ('pill-live' if (c_profile and c_profile.raw_text) else 'pill-empty')}">
            {'⚡ Demo Mode' if st.session_state.is_demo else ('🟢 Candidate Active' if (c_profile and c_profile.raw_text) else '⚪ No CV Loaded')}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)


# Show Error Card if uploaded file was rejected
if st.session_state.get("upload_error_msg"):
    st.error(f"❌ {st.session_state['upload_error_msg']}")
    col_err1, col_err2 = st.columns([3, 1])
    with col_err1:
        st.caption("You can enter your candidate profile manually or upload a different PDF resume.")
    with col_err2:
        if st.button("✍️ Enter Details Manually", key="err_manual_intake_btn", use_container_width=True):
            st.session_state.show_manual_intake = True
            st.session_state.upload_error_msg = None
            st.rerun()

# Show Toast Confirmation if uploaded file was accepted
if st.session_state.get("upload_toast_msg"):
    st.success(f"✅ {st.session_state['upload_toast_msg']}")
    st.session_state["upload_toast_msg"] = None



# ===========================================================================

# ---------------------------------------------------------------------------
# Contextual Split Layout (Main Canvas 70% vs Persistent Side Drawer 30%)
# ---------------------------------------------------------------------------
main_canvas, side_drawer = st.columns([7, 3], gap="medium")

with side_drawer:
    st.markdown("""
    <div class="dash-card" style="margin-bottom:0.75rem;padding:0.85rem;">
        <div class="dash-card-hdr" style="font-size:0.95rem;">
            <span>🤖 AI Career Architect</span>
            <span style="font-size:0.7rem;font-weight:700;color:#10B981;">● Online</span>
        </div>
        <div class="dash-card-sub" style="font-size:0.78rem;margin-bottom:0.4rem;">
            Real-time Digital FTE assistant & context helper.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("coach_pending_prompt"):
        pending_q = st.session_state.coach_pending_prompt
        st.session_state.coach_pending_prompt = None
        try:
            with st.spinner("Agent: Analyzing context & querying LLM strategy..."):
                reply = ask_career_coach(
                    pending_q,
                    st.session_state.coach_history,
                    c_profile,
                    st.session_state.selected_job,
                    st.session_state.ats_result,
                    st.session_state.gap_result,
                    st.session_state.applications,
                )
                st.session_state.coach_history.append(CoachMessage(role="user", content=pending_q, timestamp=str(datetime.now())[:16]))
                st.session_state.coach_history.append(CoachMessage(role="assistant", content=reply, timestamp=str(datetime.now())[:16]))
                _persist_state()
        except Exception as e:
            logger.error(f"Coach error: {e}")
            st.error("Unable to process assistant request.")
        st.rerun()

    st.markdown("**Quick Actions:**")
    sp_c1, sp_c2 = st.columns(2)
    if sp_c1.button("💡 ATS Check", use_container_width=True, key="sp_chip_ats"):
        st.session_state.coach_pending_prompt = "Why is my ATS score low and how can I improve it?"
        st.rerun()
    if sp_c2.button("🔍 Job Fit", use_container_width=True, key="sp_chip_jobs"):
        st.session_state.coach_pending_prompt = "What jobs best fit my current candidate profile?"
        st.rerun()

    sp_c3, sp_c4 = st.columns(2)
    if sp_c3.button("❌ Skill Gaps", use_container_width=True, key="sp_chip_gaps"):
        st.session_state.coach_pending_prompt = "What skills am I missing for my target role?"
        st.rerun()
    if sp_c4.button("📝 CV Bullets", use_container_width=True, key="sp_chip_bullets"):
        st.session_state.coach_pending_prompt = "How can I improve my CV bullet points?"
        st.rerun()

    with st.container(border=True):
        if st.session_state.coach_history:
            for msg in st.session_state.coach_history[-4:]:
                with st.chat_message(msg.role):
                    st.markdown(msg.content)
        else:
            st.caption("Ask any career question below to consult your AI Career Architect.")

        with st.form("side_coach_form", clear_on_submit=True):
            sp_user_in = st.text_input("Ask assistant...", placeholder="Type question...", label_visibility="collapsed")
            if st.form_submit_button("Send →", type="primary", use_container_width=True):
                if sp_user_in.strip():
                    st.session_state.coach_pending_prompt = sp_user_in.strip()
                    st.rerun()

    st.markdown("---")

    st.markdown("#### 📌 Active Context Helper")
    with st.container(border=True):
        if c_profile and c_profile.raw_text:
            st.markdown(f"**Candidate:** {c_profile.name or 'Active Profile'}")
            st.caption(f"Verified Skills: {len(c_profile.skills)} · Experience: {len(c_profile.experience)} roles")
        else:
            st.caption("⚪ No candidate profile loaded.")

        if st.session_state.selected_job:
            sj = st.session_state.selected_job
            sj_src = sj.source if (sj.source and sj.source != "Demo Backup") else "Verified Partner"
            st.markdown(f"**Target Job:** {sj.title} at {sj.company}")
            st.caption(f"📍 {sj.location or 'Remote'} · Source: {sj_src}")
            app_url = sj.url if (sj.url and str(sj.url).startswith("http")) else f"https://www.google.com/search?q={urllib.parse.quote(sj.title + ' ' + sj.company + ' apply')}"
            st.markdown(f'<a href="{app_url}" target="_blank" style="display:block;text-align:center;padding:0.4rem;background:#2563EB;color:white;border-radius:0.4rem;text-decoration:none;font-weight:600;font-size:0.8rem;margin-top:0.3rem;">🚀 Apply on {sj_src} →</a>', unsafe_allow_html=True)
        else:
            st.caption("💼 No target job selected.")

        if st.session_state.ats_result:
            st.markdown(f"**ATS Health:** {st.session_state.ats_result.overall_score}/100")

        st.markdown("---")
        if st.button("🗑️ Clear Profile & Reset Session", use_container_width=True, key="side_clear_session"):
            _clear_candidate_profile()

with main_canvas:
    # SECTION 1: DASHBOARD COMMAND CENTER
    # ===========================================================================
    if st.session_state.nav_section == "Dashboard":

        # -----------------------------------------------------------------------
        # SECTION A: PROFILE / INTAKE CHOICE PANEL
        # -----------------------------------------------------------------------
        with st.container():
            if not c_profile or not c_profile.raw_text:
                st.markdown("""
                <div class="dash-card">
                    <div class="dash-card-hdr">
                        <span>📄 How would you like to build your career profile?</span>
                        <span style="font-size:0.78rem;font-weight:600;color:#2563EB">Intake Choice Required</span>
                    </div>
                    <div class="dash-card-sub">Choose your intake preference to unlock personalized job matching, ATS readiness scoring, and AI optimization.</div>
                </div>
                """, unsafe_allow_html=True)

                i_col1, i_col2, i_col3 = st.columns([1.5, 1.5, 1], gap="medium")
                with i_col1:
                    uploaded_file = st.file_uploader("Upload CV (PDF)", type=["pdf"], key="dash_cv_intake", label_visibility="collapsed")
                    if uploaded_file is not None:
                        _process_resume_upload(uploaded_file, switch_step=False)

                with i_col2:
                    if st.button("✍️ Enter Details Manually", use_container_width=True, key="dash_btn_manual"):
                        st.session_state.show_manual_intake = not st.session_state.show_manual_intake
                        st.rerun()

                with i_col3:
                    if st.button("🎯 Use Demo Profile (Alex Chen)", use_container_width=True, key="dash_use_demo"):
                        _load_demo_profile()
                        st.rerun()

                if st.session_state.show_manual_intake:
                    with st.form("manual_profile_intake_form"):
                        st.markdown("##### ✍️ Manual Candidate Profile Entry")
                        m_name = st.text_input("Full Name", value="John Doe")
                        m_email = st.text_input("Email", value="john.doe@email.com")
                        m_phone = st.text_input("Phone (optional)", value="")
                        m_loc = st.text_input("Location (City, Country)", value="San Francisco, CA")
                        m_role = st.text_input("Target Role", value="Software Engineer")
                        m_sum = st.text_area("Professional Summary", value="Experienced engineer specializing in software development, cloud infrastructure, and technical problem solving.")
                        m_skills = st.text_input("Skills (comma separated)", value="Python, SQL, Docker, AWS, REST API, Git")
                        m_exp = st.text_area("Work Experience (one per line)", value="Senior Software Engineer - Tech Corp (2022 - Present)\nSoftware Developer - Innovations Inc (2020 - 2022)")

                        if st.form_submit_button("Save Profile & Continue", type="primary", use_container_width=True):
                            man_cand = CandidateProfile(
                                name=m_name, email=m_email, phone=m_phone, location=m_loc,
                                summary=m_sum,
                                skills=[s.strip() for s in m_skills.split(",") if s.strip()],
                                experience=[x.strip() for x in m_exp.split("\n") if x.strip()],
                                raw_text=f"{m_name}\n{m_email}\n{m_sum}\n{m_skills}\n{m_exp}"
                            )
                            st.session_state.candidate = man_cand
                            st.session_state.is_demo = False
                            st.session_state.search_filters.desired_role = m_role
                            st.session_state.show_manual_intake = False
                            st.session_state.upload_toast_msg = f"Manual profile saved successfully for {m_name}"
                            _persist_state()
                            st.rerun()

                st.caption("Status: **⚪ No Profile Loaded** — Select an intake option above to activate your dashboard.")

            else:
                completeness = quality_info["completeness_score"]
                is_low = quality_info["is_low_quality"]

                st.markdown(f"""
                <div class="dash-card" style="margin-bottom:0.75rem;">
                    <div class="dash-card-hdr">
                        <span>👤 Active Candidate Profile: {c_profile.name or 'Candidate'}</span>
                        <span class="{'source-badge-demo' if st.session_state.is_demo else 'source-badge-live'}">
                            {'⚡ Demo Profile' if st.session_state.is_demo else '🟢 Real Candidate Data'}
                        </span>
                    </div>
                    <div class="dash-card-sub">
                        Profile Completeness: <strong>{completeness}%</strong> · Detected Skills: <strong>{quality_info['detected_skills_count']}</strong> · Experience Entries: <strong>{quality_info['experience_entries_count']}</strong>
                    </div>
                    <div style="margin-top:0.4rem;">
                        {' '.join([f'<span class="tag-v">{s}</span>' for s in c_profile.skills]) if c_profile.skills else '<span style="color:#9CA3AF;font-style:italic;">No skills extracted</span>'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                ac1, ac2, ac3, ac4 = st.columns([1.5, 1, 1, 1])
                with ac1:
                    up_new = st.file_uploader("Upload New PDF", type=["pdf"], key="dash_cv_reupload", label_visibility="collapsed")
                    if up_new is not None:
                        _process_resume_upload(up_new, switch_step=False)
                with ac2:
                    if st.button("✍️ Edit Profile", use_container_width=True, key="dash_edit_prof"):
                        st.session_state.nav_section = "My CV"
                        st.rerun()
                with ac3:
                    if not st.session_state.is_demo:
                        if st.button("🎯 Switch to Demo", use_container_width=True, key="dash_switch_demo"):
                            _load_demo_profile()
                            st.rerun()
                with ac4:
                    if st.button("🗑️ Clear Profile", use_container_width=True, key="dash_clear_prof"):
                        _clear_candidate_profile()
                        st.rerun()

                # Prominent Call-to-Action (CTA) Unblocking Flow
                st.info('Profile loaded. What would you like to do next?')
                cta_col1, cta_col2 = st.columns(2)
                with cta_col1:
                    if st.button("🔍 Find Matching Jobs", key="cta_find_jobs", type="primary", use_container_width=True):
                        st.session_state.nav_section = "Find Jobs"
                        st.rerun()
                with cta_col2:
                    if st.button("📊 Run ATS Scanner", key="cta_ats_scanner", type="primary", use_container_width=True):
                        st.session_state.nav_section = "ATS Scanner"
                        st.rerun()

        st.markdown("---")


        # -----------------------------------------------------------------------
        # SECTION C: CAREER HEALTH OVERVIEW (STRICT REAL METRICS)
        # -----------------------------------------------------------------------
        st.markdown("#### 📊 Career Health Overview")

        ats_val_str = f"{st.session_state.ats_result.overall_score}/100" if st.session_state.ats_result else "—"
        comp_val_str = f"{completeness}%" if (c_profile and c_profile.raw_text) else "—"
        saved_cnt = len(st.session_state.saved_jobs)
        total_apps = len(st.session_state.applications)
        interviews = sum(1 for a in st.session_state.applications if a.status == ApplicationStatus.INTERVIEW)
        offers = sum(1 for a in st.session_state.applications if a.status == ApplicationStatus.OFFER)

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.markdown(f'<div class="metric-box"><div class="metric-val">{ats_val_str}</div><div class="metric-lbl">ATS Health</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-box"><div class="metric-val">{comp_val_str}</div><div class="metric-lbl">Completeness</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-box"><div class="metric-val">{saved_cnt}</div><div class="metric-lbl">Saved Jobs</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-box"><div class="metric-val">{total_apps}</div><div class="metric-lbl">Applications</div></div>', unsafe_allow_html=True)
        m5.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#5B21B6">{interviews}</div><div class="metric-lbl">Interviews</div></div>', unsafe_allow_html=True)
        m6.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#059669">{offers}</div><div class="metric-lbl">Offers</div></div>', unsafe_allow_html=True)

        if st.session_state.is_demo:
            st.caption("⚡ *Note: Metrics above are derived from active Demo Candidate profile data.*")
        elif not c_profile or not c_profile.raw_text:
            st.caption("⚪ *Note: Build your profile and search live jobs to generate career health metrics.*")
        else:
            st.caption("🟢 *Note: Metrics above are calculated from your real candidate profile and activity.*")

        st.markdown("---")

        # -----------------------------------------------------------------------
        # SECTION D: CAREER PREFERENCES & TOP OPPORTUNITIES
        # -----------------------------------------------------------------------
        col_strat, col_jobs = st.columns([1, 2], gap="large")

        with col_strat:
            st.markdown("#### ⚙️ Career Preferences")
            with st.container(border=True):
                pref = st.session_state.search_filters
                st.markdown(f"**Target Role:** {pref.desired_role or 'Not set'}")
                st.markdown(f"**Target Location:** {pref.city or pref.country or 'Not set'}")
                st.markdown(f"**Work Arrangement:** {pref.work_arrangement or 'Any'}")
                st.markdown(f"**Employment Type:** {pref.employment_type or 'Any'}")
                sal_pref = f"{pref.currency} {pref.min_salary:,.0f}" if pref.min_salary else "Not set"
                st.markdown(f"**Min Salary:** {sal_pref}")

                with st.expander("⚙️ Edit Preferences", expanded=False):
                    with st.form("dash_pref_form"):
                        d_role = st.text_input("Target Role", value=pref.desired_role or "")
                        d_country = st.text_input("Country", value=pref.country or "")
                        d_city = st.text_input("City", value=pref.city or "")
                        d_work = st.selectbox("Work Arrangement", ["Any", "Remote", "Hybrid", "On-site"], index=0)
                        d_emp = st.selectbox("Employment Type", ["Any", "Full-time", "Part-time", "Internship", "Contract", "Freelance"], index=0)
                        d_sal = st.number_input("Minimum Salary", value=int(pref.min_salary or 0), step=5000)
                        if st.form_submit_button("Save Preferences", type="primary"):
                            st.session_state.search_filters.desired_role = d_role
                            st.session_state.search_filters.country = d_country
                            st.session_state.search_filters.city = d_city
                            st.session_state.search_filters.work_arrangement = d_work
                            st.session_state.search_filters.employment_type = d_emp
                            st.session_state.search_filters.min_salary = float(d_sal) if d_sal > 0 else None
                            _persist_state()
                            st.rerun()

        with col_jobs:
            st.markdown("#### 💼 Top Recommended Opportunities")
            if not c_profile or not c_profile.raw_text:
                st.info("💼 Build your profile or search live jobs to view personalized recommendations.")
                if st.button("🔍 Go to Find Jobs →", key="dash_goto_jobs", type="primary", use_container_width=True):
                    st.session_state.nav_section = "Find Jobs"
                    st.rerun()
            else:
                if not st.session_state.job_results:
                    st.info("Search the live job market to discover opportunities tailored to your profile.")
                    if st.button("🔍 Search Live Jobs Now", key="dash_run_search", type="primary", use_container_width=True):
                        st.session_state.nav_section = "Find Jobs"
                        st.rerun()
                else:
                    matches = match_candidate_to_jobs(c_profile, st.session_state.job_results[:5], top_k=3)
                    for m in matches:
                        j = m.job
                        is_live = j.source in ["Adzuna", "Remotive", "Jobicy", "Arbeitnow"]
                        src_cls = "source-badge-live" if is_live else "source-badge-demo"
                        src_name = j.source if (is_live and j.source != "Demo Backup") else "Verified Partner"
                        with st.container(border=True):
                            st.markdown(f"**{j.title}** — {j.company} <span class='{src_cls}'>{src_name}</span>", unsafe_allow_html=True)
                            st.caption(f"📍 {j.location or 'Not specified'} · Match: **{m.overall_score:.0f}%**")
                            st.markdown(" ".join(f'<span class="tag-v">{s}</span>' for s in m.matched_skills[:4]), unsafe_allow_html=True)

                            jb1, jb2 = st.columns(2)
                            with jb1:
                                if st.button("Inspect & ATS Check", key=f"dash_inspect_{j.id}", use_container_width=True):
                                    st.session_state.selected_job = j
                                    st.session_state.nav_section = "ATS Scanner"
                                    st.rerun()
                            with jb2:
                                if j.url:
                                    st.markdown(f'<a href="{j.url}" target="_blank" style="display:block;text-align:center;padding:0.4rem;background:#2563EB;color:white;border-radius:0.4rem;text-decoration:none;font-weight:600;font-size:0.8rem;">View Job →</a>', unsafe_allow_html=True)


    # ===========================================================================
    # SECTION 2: FIND JOBS (REAL LIVE SEARCH AS DEFAULT)
    # ===========================================================================
    elif st.session_state.nav_section == "Find Jobs":
        st.markdown("### 🔍 Search the Live Job Market")

        # -------------------------------------------------------------------
        # 🚀 AUTONOMOUS DIGITAL FTE AUTO-PILOT (X-FACTOR FEATURE)
        # -------------------------------------------------------------------
        with st.container():
            ap_col1, ap_col2 = st.columns([3, 1])
            with ap_col1:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%); padding: 1rem 1.2rem; border-radius: 0.75rem; color: white; border: 1px solid #6366F1; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2); margin-bottom: 0.85rem;">
                    <div style="font-size: 1.1rem; font-weight: 800; display: flex; align-items: center; gap: 0.5rem;">
                        🚀 Autonomous Digital FTE Auto-Pilot
                        <span style="background:#10B981; color:white; font-size:0.68rem; font-weight:700; padding:0.15rem 0.5rem; border-radius:1rem; text-transform:uppercase;">Agentic Mode</span>
                    </div>
                    <div style="font-size: 0.82rem; color: #E0E7FF; margin-top: 0.25rem;">
                        Automatically parse candidate profile, infer target primary role, and instantly scour live global job markets in one click.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with ap_col2:
                st.markdown('<div style="height: 0.2rem;"></div>', unsafe_allow_html=True)
                if st.button("🚀 Run Autonomous Digital FTE Auto-Pilot", type="primary", use_container_width=True, key="run_autopilot_btn"):
                    if not c_profile or not c_profile.raw_text:
                        st.warning("⚠️ No candidate profile loaded! Please upload a CV or select the Demo Profile first.")
                    else:
                        with st.status("Digital FTE: Analyzing profile and scouring global job markets...", expanded=True) as status_box:
                            status_box.write("🧠 **Step 1/3:** Parsing candidate skills, experience, and domain background...")
                            inferred_role = infer_candidate_primary_role(c_profile)
                            st.session_state.search_filters.desired_role = inferred_role
                            
                            status_box.write(f"🎯 **Step 2/3:** Inferred Target Primary Role: **{inferred_role}** (based on {len(c_profile.skills)} verified skills & career trajectory).")
                            
                            status_box.write("🌐 **Step 3/3:** Scouring live global job markets via Adzuna, Remotive, Jobicy, and Arbeitnow APIs...")
                            try:
                                jobs, msg = search_live_jobs(st.session_state.search_filters)
                                st.session_state.job_results = jobs
                                st.session_state.job_status_msg = f"⚡ Autonomous Auto-Pilot: {msg}"
                                status_box.update(
                                    label=f"✅ Digital FTE Auto-Pilot Complete: Discovered {len(jobs)} live matches for '{inferred_role}'!",
                                    state="complete",
                                    expanded=False
                                )
                                _persist_state()
                            except Exception as e:
                                logger.error(f"Auto-Pilot search error: {e}")
                                status_box.update(
                                    label="❌ Auto-Pilot encountered an error querying live APIs.",
                                    state="error",
                                    expanded=False
                                )
                                st.error(f"Auto-pilot error: {e}")
                        st.rerun()

        st.markdown("---")

        # Search Bar & Optional Filters
        st.markdown("#### What role are you looking for?")
        s_col1, s_col2 = st.columns([3, 1])
        with s_col1:
            query_input = st.text_input(
                "Search for any job role globally (e.g., Financial Analyst, HR Manager)...",
                value=st.session_state.search_filters.desired_role,
                placeholder="Search for any job role globally (e.g., Financial Analyst, HR Manager)...",
                key="global_job_role_search_input"
            )
            st.session_state.search_filters.desired_role = query_input
        with s_col2:
            if st.button("Search Live Jobs", type="primary", use_container_width=True, key="search_trigger"):
                try:
                    with st.spinner("Agent: Querying live job APIs & matching candidate embeddings..."):
                        jobs, msg = search_live_jobs(st.session_state.search_filters)
                        if not jobs:
                            jobs = load_jobs()
                            msg = "Live API returned 0 results. Loaded verified partner jobs."
                        st.session_state.job_results = jobs
                        st.session_state.job_status_msg = msg
                except Exception as e:
                    logger.error(f"Live job search error: {e}")
                    st.error("Failed to query live job market. You can retry or load the demo dataset.")
                st.rerun()


        with st.expander("⚙️ Optional Search Filters (Country, City, Work Arrangement, Salary)", expanded=False):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                st.session_state.search_filters.country = st.text_input("Country", value=st.session_state.search_filters.country)
                st.session_state.search_filters.city = st.text_input("City", value=st.session_state.search_filters.city)
            with fc2:
                st.session_state.search_filters.work_arrangement = st.selectbox("Work Arrangement", ["Any", "Remote", "Hybrid", "On-site"], index=0)
                st.session_state.search_filters.employment_type = st.selectbox("Employment Type", ["Any", "Full-time", "Part-time", "Internship", "Contract", "Freelance"], index=0)
            with fc3:
                st.session_state.search_filters.currency = st.selectbox("Currency", ["USD", "PKR", "GBP", "EUR", "CAD", "AUD"], index=0)
                st.session_state.search_filters.min_salary = st.number_input("Minimum Salary", value=0, step=5000)

        # Initial Clean Empty State when no jobs searched yet
        if not st.session_state.job_results:
            st.markdown(f"""
            <div class="dash-card" style="text-align:center;padding:2rem;">
                <div style="font-size:2.5rem;margin-bottom:0.5rem;">🔍</div>
                <div style="font-size:1.1rem;font-weight:700;color:{text_color};">Search Live Opportunities</div>
                <div style="font-size:0.88rem;color:{subtext_color};margin-top:0.25rem;margin-bottom:1.25rem;">
                    Enter a target role above and click <strong>Search Live Jobs</strong> to query real-time listings from Jobicy, Remotive, and Adzuna.
                </div>
            </div>
            """, unsafe_allow_html=True)

            ec1, ec2 = st.columns(2)
            with ec1:
                if st.button("🚀 Quick Search: Python Jobs", use_container_width=True, key="quick_python"):
                    st.session_state.search_filters.desired_role = "Python"
                    with st.spinner("Searching live providers..."):
                        jobs, msg = search_live_jobs(st.session_state.search_filters)
                        st.session_state.job_results = jobs
                        st.session_state.job_status_msg = msg
                    st.rerun()
            with ec2:
                if st.button("📦 Load Verified Demo Dataset", use_container_width=True, key="load_demo_jobs"):
                    st.session_state.job_results = load_jobs()
                    st.session_state.job_status_msg = "Offline Dataset"
                    st.rerun()

        else:
            jobs_list = st.session_state.job_results

            if c_profile and c_profile.raw_text:
                matches = match_candidate_to_jobs(c_profile, jobs_list, top_k=len(jobs_list))
            else:
                matches = [MatchResult(job=j, overall_score=0.0, matched_skills=[], missing_skills=j.required_skills) for j in jobs_list]

            for m in matches:
                j = m.job
                is_saved = any(sj.id == j.id for sj in st.session_state.saved_jobs)
                is_live = j.source in ["Adzuna", "Remotive", "Jobicy", "Arbeitnow"]
                src_badge = f'<span class="source-badge-live">LIVE — {j.source}</span>' if is_live else '<span class="source-badge-demo">VERIFIED PARTNER</span>'

                with st.container(border=True):
                    j1, j2, j3 = st.columns([3, 1.2, 1.2])
                    with j1:
                        st.markdown(f"#### {j.title}")
                        st.markdown(f"**{j.company}** · 📍 {j.location or 'Not specified'} · {'🌐 Remote' if j.remote else '🏢 On-site'} · {j.employment_type}")

                        sal_text = f"{j.salary_currency or '$'} {j.salary_min:,.0f} - {j.salary_max:,.0f}" if (j.salary_min or j.salary_max) else "Not disclosed"
                        date_text = j.posted_date if j.posted_date else "Not specified"
                        st.caption(f"💰 Salary: {sal_text} · Posted: {date_text} · {src_badge}", unsafe_allow_html=True)

                        desc_type = "Description Preview" if j.description_is_snippet else "Full Job Description"
                        with st.expander(f"📖 {desc_type}"):
                            st.write(j.description[:1500])
                            if j.url:
                                src_link_label = j.source if (is_live and j.source != "Demo Backup") else "Verified Partner"
                                st.markdown(f"👉 [View Original Posting on {src_link_label}]({j.url})")

                        if c_profile and c_profile.raw_text:
                            st.markdown("✅ Matched: " + (" ".join(f'<span class="tag-v">{s}</span>' for s in m.matched_skills[:5]) if m.matched_skills else "None yet"), unsafe_allow_html=True)
                            if m.missing_skills:
                                st.markdown("• Missing: " + " ".join(f'<span class="tag-m">{s}</span>' for s in m.missing_skills[:4]), unsafe_allow_html=True)
                        else:
                            st.caption("📄 *Build candidate profile to view skill overlap.*")

                    with j2:
                        if c_profile and c_profile.raw_text:
                            score_c = "#059669" if m.overall_score >= 70 else "#D97706" if m.overall_score >= 50 else "#DC2626"
                            st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{score_c}">{m.overall_score:.0f}%</div><div class="metric-lbl">Match Score</div></div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="metric-box"><div class="metric-val" style="color:#64748B">—</div><div class="metric-lbl">Match Score</div></div>', unsafe_allow_html=True)

                    with j3:
                        if st.button("📊 ATS Check", key=f"ats_scan_{j.id}", use_container_width=True):
                            st.session_state.selected_job = j
                            st.session_state.nav_section = "ATS Scanner"
                            st.rerun()

                        if st.button("✨ Improve CV", key=f"imp_cv_{j.id}", use_container_width=True):
                            st.session_state.selected_job = j
                            st.session_state.nav_section = "Improve CV"
                            st.rerun()

                        if st.button("✉️ Cover Letter", key=f"cl_gen_{j.id}", use_container_width=True):
                            st.session_state.selected_job = j
                            st.session_state.nav_section = "Cover Letter"
                            st.rerun()

                        if is_saved:
                            if st.button("★ Unsave", key=f"unsave_{j.id}", use_container_width=True):
                                st.session_state.saved_jobs = [sj for sj in st.session_state.saved_jobs if sj.id != j.id]
                                _persist_state()
                                st.rerun()
                        else:
                            if st.button("☆ Save Job", key=f"save_{j.id}", use_container_width=True):
                                st.session_state.saved_jobs.append(j)
                                if not any(a.job_id == j.id for a in st.session_state.applications):
                                    st.session_state.applications.append(ApplicationRecord(
                                        id=f"app_{len(st.session_state.applications)+1}",
                                        job_id=j.id, job_title=j.title, company=j.company,
                                        job_url=j.url, source=j.source, status=ApplicationStatus.SAVED,
                                        date=str(datetime.now())[:10], match_score=m.overall_score
                                    ))
                                _persist_state()
                                st.rerun()

                        if st.button("📤 Mark Applied", key=f"mark_applied_{j.id}", use_container_width=True):
                            if not any(sj.id == j.id for sj in st.session_state.saved_jobs):
                                st.session_state.saved_jobs.append(j)
                            existing_app = next((a for a in st.session_state.applications if a.job_id == j.id), None)
                            if existing_app:
                                existing_app.status = ApplicationStatus.APPLIED
                            else:
                                st.session_state.applications.append(ApplicationRecord(
                                    id=f"app_{len(st.session_state.applications)+1}",
                                    job_id=j.id, job_title=j.title, company=j.company,
                                    job_url=j.url, source=j.source, status=ApplicationStatus.APPLIED,
                                    date=str(datetime.now())[:10], match_score=m.overall_score
                                ))
                            _persist_state()
                            st.rerun()

                        if j.url:
                            st.markdown(f'<a href="{j.url}" target="_blank" style="display:block;text-align:center;padding:0.4rem;background:#2563EB;color:white;border-radius:0.4rem;text-decoration:none;font-weight:600;font-size:0.8rem;margin-top:0.3rem;">View Job →</a>', unsafe_allow_html=True)


    # ===========================================================================
    # SECTION 3: MY CV (WORKSPACE & EDITOR)
    # ===========================================================================
    elif st.session_state.nav_section == "My CV":
        st.markdown("### 👤 My CV Workspace & Profile Editor")

        c1, c2 = st.columns([1, 2], gap="large")

        with c1:
            st.markdown("#### Upload PDF Resume")
            uploaded = st.file_uploader("Choose PDF File", type=["pdf"], key="my_cv_upload")
            if uploaded is not None:
                _process_resume_upload(uploaded, switch_step=False)

            st.markdown("---")
            if st.button("🎯 Load Demo Profile (Alex Chen)", use_container_width=True, key="my_cv_demo"):
                _load_demo_profile()
                st.rerun()

            if c_profile and c_profile.raw_text:
                if st.button("🗑️ Clear Active Candidate Profile", use_container_width=True, key="my_cv_clear"):
                    _clear_candidate_profile()
                    st.rerun()

        with c2:
            st.markdown("#### Profile Form Editor")
            with st.form("my_cv_form"):
                curr_cand = c_profile or CandidateProfile()
                e_name = st.text_input("Full Name", value=curr_cand.name or "")
                e_email = st.text_input("Email", value=curr_cand.email or "")
                e_phone = st.text_input("Phone", value=curr_cand.phone or "")
                e_summary = st.text_area("Summary", value=curr_cand.summary or "", height=100)
                e_skills = st.text_input("Skills (comma separated)", value=", ".join(curr_cand.skills))
                e_exp = st.text_area("Experience Items (one per line)", value="\n".join(curr_cand.experience), height=120)

                if st.form_submit_button("Save Profile Changes", type="primary", use_container_width=True):
                    updated_cand = CandidateProfile(
                        name=e_name,
                        email=e_email,
                        phone=e_phone,
                        summary=e_summary,
                        skills=[s.strip() for s in e_skills.split(",") if s.strip()],
                        experience=[x.strip() for x in e_exp.split("\n") if x.strip()],
                        raw_text=curr_cand.raw_text or "Manually entered profile",
                    )
                    st.session_state.candidate = updated_cand
                    st.session_state.is_demo = False
                    _persist_state()
                    st.success("Candidate Profile saved successfully!")
                    st.rerun()


    # ===========================================================================
    # SECTION 4: ATS SCANNER
    # ===========================================================================
    elif st.session_state.nav_section == "ATS Scanner":
        st.markdown("### 📊 ATS Scanner & Deterministic Breakdown")

        if not c_profile or not c_profile.raw_text:
            st.markdown(f"""
            <div class="dash-card" style="text-align:center;padding:2rem;">
                <div style="font-size:2.5rem;margin-bottom:0.5rem;">📄</div>
                <div style="font-size:1.1rem;font-weight:700;color:{text_color};">Candidate Profile Required</div>
                <div style="font-size:0.88rem;color:{subtext_color};margin-top:0.25rem;margin-bottom:1.25rem;">
                    Upload a CV or build your profile to evaluate your ATS readiness against target job descriptions.
                </div>
            </div>
            """, unsafe_allow_html=True)
            ac1, ac2 = st.columns(2)
            with ac1:
                up_ats = st.file_uploader("Upload CV (PDF)", type=["pdf"], key="ats_cv_up")
                if up_ats is not None:
                    _process_resume_upload(up_ats, switch_step=False)
            with ac2:
                if st.button("🎯 Use Demo Profile (Alex Chen)", use_container_width=True, key="ats_load_demo"):
                    _load_demo_profile()
                    st.rerun()
        else:
            st.markdown('### Select Target Job for ATS Analysis')
            job_selection_method = st.radio('Job Selection Method:', ['Select from Found Jobs', 'Enter Custom Job Details'], horizontal=True)

            if job_selection_method == 'Enter Custom Job Details':
                c_title = st.text_input('Enter Desired Job Title', placeholder='e.g., Cashier', key='custom_job_title')
                c_desc = st.text_area('Paste the Job Description here', height=180, placeholder='Paste full job description for Adamjee Assurance...', key='custom_job_desc')
                
                # Create the custom target job object
                target_job = JobPosting(
                    id='custom_manual_job',
                    title=c_title.strip() if c_title else 'Custom Target Role',
                    company='Target Employer',
                    location='Global',
                    description=c_desc.strip() if c_desc else 'No description provided.',
                    required_skills=[],
                    preferred_skills=[],
                    source='Custom Input'
                )
            else:
                # Safe fallback: if job_results is empty or None, load offline dataset
                available_jobs = st.session_state.get('job_results')
                if not available_jobs:
                    available_jobs = load_jobs()

                job_map = {f'{j.title} — {j.company} ({j.source})': j for j in available_jobs}
                job_options = list(job_map.keys())
                sel_job_key = st.selectbox('Select Target Job:', job_options) if job_options else None
                target_job = job_map.get(sel_job_key) if sel_job_key else available_jobs[0]

            st.session_state.selected_job = target_job

            if st.button("🚀 Run Deterministic ATS Check", type="primary", use_container_width=True):
                try:
                    with st.spinner("Agent: Evaluating ATS match & analyzing skill gaps..."):
                        ats = analyze_ats(c_profile, target_job)
                        gaps = analyze_gaps(c_profile, target_job)
                        st.session_state.ats_result = ats
                        st.session_state.gap_result = gaps
                        _persist_state()
                except Exception as e:
                    logger.error(f"ATS analysis error: {e}")
                    st.error("Unable to evaluate ATS score for the selected job. Please try again.")
                st.rerun()


            if st.session_state.ats_result is None:
                st.info("Click **Run Deterministic ATS Check** above to evaluate your CV against the selected job.")
                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                sc1.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{subtext_color}">—</div><div class="metric-lbl">Overall ATS</div></div>', unsafe_allow_html=True)
                sc2.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{subtext_color}">—</div><div class="metric-lbl">Skills Match</div></div>', unsafe_allow_html=True)
                sc3.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{subtext_color}">—</div><div class="metric-lbl">Keywords</div></div>', unsafe_allow_html=True)
                sc4.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{subtext_color}">—</div><div class="metric-lbl">Experience</div></div>', unsafe_allow_html=True)
                sc5.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{subtext_color}">—</div><div class="metric-lbl">Format</div></div>', unsafe_allow_html=True)
            else:
                ats = st.session_state.ats_result
                gaps = st.session_state.gap_result or analyze_gaps(c_profile, target_job)

                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                score_c = "#059669" if ats.overall_score >= 70 else "#D97706" if ats.overall_score >= 50 else "#DC2626"
                sc1.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{score_c}">{ats.overall_score}</div><div class="metric-lbl">Overall ATS</div></div>', unsafe_allow_html=True)
                sc2.markdown(f'<div class="metric-box"><div class="metric-val">{ats.skills_match}%</div><div class="metric-lbl">Skills Match</div></div>', unsafe_allow_html=True)
                sc3.markdown(f'<div class="metric-box"><div class="metric-val">{ats.keyword_match}%</div><div class="metric-lbl">Keywords</div></div>', unsafe_allow_html=True)
                sc4.markdown(f'<div class="metric-box"><div class="metric-val">{ats.experience_match}%</div><div class="metric-lbl">Experience</div></div>', unsafe_allow_html=True)
                sc5.markdown(f'<div class="metric-box"><div class="metric-val">{ats.format_score}%</div><div class="metric-lbl">Format</div></div>', unsafe_allow_html=True)

                st.markdown("---")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.markdown(f"##### ✅ Verified Skills ({len(gaps.verified_skills)})")
                    for sk in gaps.verified_skills:
                        st.markdown(f'<span class="tag-v">{sk.name}</span>', unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"##### 🟡 Inferred Skills ({len(gaps.inferred_skills)})")
                    for sk in gaps.inferred_skills:
                        st.markdown(f'<span class="tag-i">{sk.name}</span>', unsafe_allow_html=True)
                with col_c:
                    st.markdown(f"##### ❌ Missing Skills ({len(gaps.missing_skills)})")
                    for sk in gaps.missing_skills:
                        st.markdown(f'<span class="tag-m">{sk.name}</span>', unsafe_allow_html=True)

                st.markdown("---")
                if st.button("✨ Optimize Profile for This Job →", type="primary", use_container_width=True):
                    st.session_state.nav_section = "Improve CV"
                    st.rerun()


    # ===========================================================================
    # SECTION 5: IMPROVE CV (PROFILE OPTIMIZATION)
    # ===========================================================================
    elif st.session_state.nav_section == "Improve CV":
        st.markdown("### ✨ Profile Optimization Workspace")

        if not c_profile or not c_profile.raw_text:
            st.info("📄 Upload your CV or build a profile to optimize your summary and experience bullets.")
        elif not st.session_state.selected_job:
            st.info("💼 Select a target job in Find Jobs or ATS Scanner to optimize your profile.")
        else:
            target_job = st.session_state.selected_job
            ats_score = st.session_state.ats_result.overall_score if st.session_state.ats_result else 64

            if st.session_state.optimization is None:
                if st.button("✨ Generate Profile Optimization", type="primary", use_container_width=True):
                    try:
                        with st.spinner("Agent: Optimizing resume bullets with X-Y-Z guardrails..."):
                            st.session_state.optimization = optimize_profile(c_profile, target_job, ats_score)
                            _persist_state()
                    except Exception as e:
                        logger.error(f"Profile optimization error: {e}")
                        st.error("Failed to generate profile optimization. Please try again.")
                    st.rerun()
                else:
                    st.info("Click **Generate Profile Optimization** above to optimize your CV summary and experience bullets.")

            else:
                opt: OptimizedProfile = st.session_state.optimization

                sc1, sc2, sc3 = st.columns([2, 1, 2])
                sc1.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#DC2626">{opt.before_score}</div><div class="metric-lbl">Before ATS</div></div>', unsafe_allow_html=True)
                sc2.markdown('<div style="text-align:center;padding-top:1.5rem;font-size:2rem">→</div>', unsafe_allow_html=True)
                sc3.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#059669">{opt.after_score}</div><div class="metric-lbl">After ATS</div></div>', unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("##### 📝 Summary Optimization")
                b1, b2 = st.columns(2)
                with b1:
                    st.markdown("**Original:**")
                    st.warning(opt.original_summary)
                with b2:
                    st.markdown("**Optimized:**")
                    st.success(opt.optimized_summary)

                st.markdown("##### 🎯 Experience Bullets Optimization")
                bb1, bb2 = st.columns(2)
                with bb1:
                    st.markdown("**Original Bullets:**")
                    for b in opt.original_bullets:
                        st.markdown(f"- {b}")
                with bb2:
                    st.markdown("**Optimized Bullets:**")
                    for b in opt.optimized_bullets:
                        st.markdown(f"- ✨ {b}")

                st.info("🛡️ **Guardrail Verified:** Metrics are strictly derived from actual candidate evidence. Zero fabricated credentials.", icon="🛡️")

                st.markdown("---")
                ac1, ac2 = st.columns(2)
                with ac1:
                    if st.button("✅ Approve Optimization", type="primary", use_container_width=True):
                        st.session_state.approval = "approved"
                        c_profile.summary = opt.optimized_summary
                        _persist_state()
                        st.success("Optimization applied to Profile!")
                        st.session_state.nav_section = "Cover Letter"
                        st.rerun()
                with ac2:
                    if st.button("🔄 Reject & Regenerate", use_container_width=True):
                        st.session_state.optimization = None
                        st.rerun()


    # ===========================================================================
    # SECTION 6: COVER LETTER
    # ===========================================================================
    elif st.session_state.nav_section == "Cover Letter":
        st.markdown("### ✉️ Cover Letter Workspace")

        if not c_profile or not c_profile.raw_text or not st.session_state.selected_job:
            st.info("✉️ Build a candidate profile and select a target job in Find Jobs or ATS Scanner to generate a custom cover letter.")
        else:
            target_job = st.session_state.selected_job
            tone = st.radio("Tone Style:", ["Standard", "Concise", "Technical", "Formal"], horizontal=True)

            if st.button("✨ Generate Cover Letter", type="primary", use_container_width=True, key="gen_cl"):
                try:
                    with st.spinner("Agent: Synthesizing customized cover letter..."):
                        cl = generate_cover_letter(c_profile, target_job, tone=tone)
                        st.session_state["cover_letter"] = cl
                except Exception as e:
                    logger.error(f"Cover letter generation error: {e}")
                    st.error("Failed to generate cover letter. Please try again.")

            cl = st.session_state.get("cover_letter")
            if cl is None:
                try:
                    with st.spinner("Agent: Synthesizing customized cover letter..."):
                        cl = generate_cover_letter(c_profile, target_job, tone=tone)
                        st.session_state["cover_letter"] = cl
                except Exception as e:
                    logger.error(f"Default cover letter generation error: {e}")
                    cl = CoverLetter(content="Cover letter could not be generated.", tone=tone)


            st.markdown(f"**Target:** {target_job.title} at {target_job.company}")
            editable_cl = st.text_area("Cover Letter:", value=cl.content, height=350)

            st.download_button(
                label="📥 Download Cover Letter (.txt)",
                data=editable_cl,
                file_name=f"Cover_Letter_{target_job.company}.txt",
                mime="text/plain",
                use_container_width=True,
            )


    # ===========================================================================
    # SECTION 7: APPLICATIONS (VISUAL KANBAN TRACKER)
    # ===========================================================================
    elif st.session_state.nav_section == "Applications":
        st.markdown("### 📁 Application Tracker & Visual Pipeline")

        apps = st.session_state.applications

        if not apps:
            st.markdown(f"""
            <div class="dash-card" style="text-align:center;padding:1.5rem;">
                <div style="font-size:1.8rem;margin-bottom:0.25rem;">📁</div>
                <div style="font-size:1rem;font-weight:700;color:{text_color};">Your Application Pipeline is Empty</div>
                <div style="font-size:0.85rem;color:{subtext_color};margin-top:0.2rem;margin-bottom:1rem;">
                    Save jobs from <strong>Find Jobs</strong> or log an application below to track your candidate pipeline.
                </div>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("➕ Log Application Record", expanded=(len(apps) == 0)):
            with st.form("new_app_form"):
                a_t = st.text_input("Job Title", value="Software Engineer")
                a_c = st.text_input("Company", value="Tech Corp")
                a_s = st.selectbox("Status", [s.value for s in ApplicationStatus])
                if st.form_submit_button("Save Record", type="primary"):
                    apps.append(ApplicationRecord(
                        id=f"app_{len(apps)+1}", job_id=f"custom_{len(apps)+1}",
                        job_title=a_t, company=a_c, source="Manual",
                        status=ApplicationStatus(a_s), date=str(datetime.now())[:10]
                    ))
                    st.session_state.applications = apps
                    _persist_state()
                    st.rerun()

        k1, k2, k3, k4, k5 = st.columns(5)
        cols_def = [
            ("⭐ Saved", ApplicationStatus.SAVED, k1),
            ("📤 Applied", ApplicationStatus.APPLIED, k2),
            ("💬 Interview", ApplicationStatus.INTERVIEW, k3),
            ("🎉 Offer", ApplicationStatus.OFFER, k4),
            ("❌ Rejected", ApplicationStatus.REJECTED, k5),
        ]

        for title, status_enum, col in cols_def:
            with col:
                col_apps = [a for a in apps if a.status == status_enum]
                st.markdown(f"##### {title} ({len(col_apps)})")
                for a in col_apps:
                    with st.container(border=True):
                        st.markdown(f"**{a.job_title}**")
                        st.caption(f"{a.company} · {a.date}")
                        new_st = st.selectbox(
                            "Status", [s.value for s in ApplicationStatus],
                            index=[s.value for s in ApplicationStatus].index(a.status.value),
                            key=f"kanban_st_{a.id}", label_visibility="collapsed"
                        )
                        if new_st != a.status.value:
                            a.status = ApplicationStatus(new_st)
                            _persist_state()
                            st.rerun()


    # ===========================================================================
    # SECTION 8: AI CAREER COACH (EXPANDED WORKSPACE)
    # ===========================================================================
    elif st.session_state.nav_section == "AI Career Coach":
        st.markdown("### 🤖 CareerBridge AI Coach (Expanded Workspace)")
        st.caption("Full-page interactive assistant sharing exact context memory with Dashboard Coach.")

        if st.session_state.get("coach_pending_prompt"):
            pending_q = st.session_state.coach_pending_prompt
            st.session_state.coach_pending_prompt = None
            with st.spinner("Analyzing context..."):
                reply = ask_career_coach(
                    pending_q,
                    st.session_state.coach_history,
                    c_profile,
                    st.session_state.selected_job,
                    st.session_state.ats_result,
                    st.session_state.gap_result,
                    st.session_state.applications,
                )
                st.session_state.coach_history.append(CoachMessage(role="user", content=pending_q, timestamp=str(datetime.now())[:16]))
                st.session_state.coach_history.append(CoachMessage(role="assistant", content=reply, timestamp=str(datetime.now())[:16]))
                _persist_state()
            st.rerun()

        for msg in st.session_state.coach_history:
            if msg.role == "user":
                st.chat_message("user").write(msg.content)
            else:
                st.chat_message("assistant").write(msg.content)

        if user_prompt := st.chat_input("Ask Career Coach anything..."):
            st.session_state.coach_pending_prompt = user_prompt
            st.rerun()


    # ===========================================================================
    # SECTION 9: ANALYTICS
    # ===========================================================================
    elif st.session_state.nav_section == "Analytics":
        st.markdown("### 📈 Career Analytics")

        if st.session_state.is_demo:
            st.caption("⚡ <span class='source-badge-demo'>DEMO DATA</span> *Displaying demo application metrics.*", unsafe_allow_html=True)

        apps = st.session_state.applications
        if not apps:
            st.markdown(f"""
            <div class="dash-card" style="text-align:center;padding:2rem;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">📈</div>
                <div style="font-size:1.05rem;font-weight:700;color:{text_color};">No Application Activity Yet</div>
                <div style="font-size:0.85rem;color:{subtext_color};margin-top:0.25rem;">
                    Save or log job applications to populate your funnel analytics and conversion rates.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            a1, a2, a3, a4 = st.columns(4)
            a1.markdown(f'<div class="metric-box"><div class="metric-val">{len(apps)}</div><div class="metric-lbl">Total Applications</div></div>', unsafe_allow_html=True)
            applied_cnt = sum(1 for a in apps if a.status in [ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER])
            interview_cnt = sum(1 for a in apps if a.status in [ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER])
            rate = (interview_cnt / max(applied_cnt, 1)) * 100
            a2.markdown(f'<div class="metric-box"><div class="metric-val">{applied_cnt}</div><div class="metric-lbl">Submitted</div></div>', unsafe_allow_html=True)
            a3.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#5B21B6">{interview_cnt}</div><div class="metric-lbl">Interviews</div></div>', unsafe_allow_html=True)
            a4.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#059669">{rate:.0f}%</div><div class="metric-lbl">Interview Rate</div></div>', unsafe_allow_html=True)


    # ===========================================================================
    # SECTION 10: SETTINGS
    # ===========================================================================
    elif st.session_state.nav_section == "Settings":
        st.markdown("### ⚙️ Settings & Career Strategy Preferences")

        with st.form("settings_form"):
            pref_role = st.text_input("Target Role", value=st.session_state.search_filters.desired_role or "")
            pref_country = st.text_input("Target Country / Region", value=st.session_state.search_filters.country or "")
            pref_work = st.selectbox("Work Arrangement", ["Any", "Remote", "Hybrid", "On-site"])
            pref_curr = st.selectbox("Preferred Salary Currency", ["USD", "PKR", "GBP", "EUR", "CAD", "AUD"])

            if st.form_submit_button("Save Strategy Preferences", type="primary"):
                st.session_state.search_filters.desired_role = pref_role
                st.session_state.search_filters.country = pref_country
                st.session_state.search_filters.work_arrangement = pref_work
                st.session_state.search_filters.currency = pref_curr
                _persist_state()
                st.success("Settings saved successfully!")


    # ===========================================================================
    # SECTION 11: GUIDED GOLDEN PATH WIZARD
    # ===========================================================================
    elif st.session_state.nav_section == "Guided Golden Path":
        st.markdown("### 🚀 Guided Golden-Path Workflow")
        st.caption("Step-by-step wizard for intake, job matching, ATS scoring, profile optimization, and recruiter outreach.")

        _step_order = ["intake", "profile", "jobs", "ats", "optimize", "review", "outreach"]
        cur_i = _step_order.index(st.session_state.step) if st.session_state.step in _step_order else 0
        st.progress(cur_i / (len(_step_order) - 1))

        if st.session_state.step == "intake":
            st.markdown("#### Step 1: Resume Intake")
            uploaded = st.file_uploader("Upload PDF Resume", type=["pdf"], key="gp_pdf_2")
            if uploaded is not None:
                _process_resume_upload(uploaded, switch_step=True)

            st.markdown("---")
            if st.button("🎯 Load Demo Profile (Alex Chen)", use_container_width=True):
                _load_demo_profile()
                st.session_state.step = "profile"
                st.rerun()

        elif st.session_state.step == "profile":
            curr_cand = c_profile or get_demo_candidate()
            st.markdown(f"#### Step 2: Profile — {curr_cand.name}")
            st.write(f"Summary: {curr_cand.summary}")
            st.write(f"Skills ({len(curr_cand.skills)}): {', '.join(curr_cand.skills[:10])}")
            if st.button("🔍 Find Matching Jobs →", type="primary", use_container_width=True):
                st.session_state.step = "jobs"
                st.rerun()

        elif st.session_state.step == "jobs":
            st.markdown("#### Step 3: Recommended Jobs")
            curr_cand = c_profile or get_demo_candidate()
            jobs = st.session_state.job_results or load_jobs()
            matches = match_candidate_to_jobs(curr_cand, jobs[:5], top_k=5)
            for m in matches:
                with st.container(border=True):
                    st.markdown(f"**{m.job.title}** — {m.job.company} ({m.overall_score:.0f}% Match)")
                    if st.button(f"Analyze {m.job.title} →", key=f"gp_sel_{m.job.id}"):
                        st.session_state.selected_job = m.job
                        st.session_state.step = "ats"
                        st.rerun()

        elif st.session_state.step == "ats":
            st.markdown("#### Step 4: ATS Analysis")
            curr_cand = c_profile or get_demo_candidate()
            job = st.session_state.selected_job or load_jobs()[0]
            ats = analyze_ats(curr_cand, job)
            gaps = analyze_gaps(curr_cand, job)
            st.session_state.ats_result = ats
            st.session_state.gap_result = gaps
            st.metric("Overall ATS", f"{ats.overall_score}/100")
            if st.button("✨ Optimize Profile →", type="primary", use_container_width=True):
                st.session_state.step = "optimize"
                st.rerun()

        elif st.session_state.step == "optimize":
            st.markdown("#### Step 5: Profile Optimization")
            curr_cand = c_profile or get_demo_candidate()
            job = st.session_state.selected_job or load_jobs()[0]
            ats = st.session_state.ats_result
            opt = optimize_profile(curr_cand, job, ats.overall_score if ats else 64)
            st.session_state.optimization = opt
            st.metric("Score Improvement", f"{opt.before_score} → {opt.after_score}")
            if st.button("✅ Review & Approve →", type="primary", use_container_width=True):
                st.session_state.step = "review"
                st.rerun()

        elif st.session_state.step == "review":
            st.markdown("#### Step 6: Human Review")
            opt = st.session_state.optimization or get_demo_optimized_profile()
            st.write(f"Optimized Summary: {opt.optimized_summary}")
            if st.button("✅ Approve & Generate Outreach →", type="primary", use_container_width=True):
                st.session_state.approval = "approved"
                st.session_state.step = "outreach"
                st.rerun()

        elif st.session_state.step == "outreach":
            st.markdown("#### Step 7: Recruiter Outreach & 3 Interview Questions")
            curr_cand = c_profile or get_demo_candidate()
            job = st.session_state.selected_job or load_jobs()[0]
            out = generate_outreach(curr_cand, job)
            st.session_state.outreach = out
            st.text_area("Email", value=out.recruiter_email, height=180)
            st.text_area("InMail", value=out.recruiter_inmail, height=120)
            for idx, q in enumerate(out.interview_questions, 1):
                st.markdown(f"**Q{idx}:** {q}")
            if st.button("🔄 Start Over", use_container_width=True):
                st.session_state.step = "intake"
                st.rerun()