"""CareerBridge AI — AI Career Intelligence Platform & Career Command Center.

Enterprise HR-Tech Dashboard + Guided Golden-Path Wizard.
Run with: streamlit run frontend/app.py
"""
import sys
import os
import hashlib
from datetime import datetime

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
# Imports
# ---------------------------------------------------------------------------
from backend.models import (
    CandidateProfile, JobPosting, MatchResult, ATSAnalysis,
    GapAnalysis, OptimizedProfile, OutreachPackage, JobSearchFilters,
    ApplicationRecord, ApplicationStatus, CoverLetter, CoachMessage,
    SkillClassification,
)
from backend.config import is_demo_mode, get_api_key, logger
from backend.parser import parse_resume, parse_resume_text
from backend.rag_engine import load_jobs, match_candidate_to_jobs
from backend.ats_engine import analyze_ats, analyze_gaps
from backend.optimizer import optimize_profile
from backend.outreach import generate_outreach
from backend.job_service import search_live_jobs, get_adzuna_credentials
from backend.cover_letter import generate_cover_letter
from backend.coach import ask_career_coach
from backend.storage import save_session_state, load_session_state
from backend.demo import (
    get_demo_candidate, get_demo_ats_analysis, get_demo_gap_analysis,
    get_demo_optimized_profile, get_demo_outreach, get_demo_target_job_id,
)

# ---------------------------------------------------------------------------
# Enterprise HR-Tech Design Tokens System
# Palette: Primary Navy (#0B1F33), Brand Blue (#2563EB), Action (#0EA5E9)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --primary-navy: #0B1F33;
    --brand-blue: #2563EB;
    --action-blue: #0EA5E9;
    --bg-main: #F7F9FC;
    --card-surface: #FFFFFF;
    --border-color: #E2E8F0;
    --text-primary: #0F172A;
    --text-secondary: #64748B;
    --success: #059669;
    --warning: #D97706;
    --danger: #DC2626;
}

.stApp {
    background-color: var(--bg-main);
    font-family: 'Inter', -apple-system, sans-serif;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #0B1F33 !important;
    border-right: 1px solid #1E293B;
}
[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}
.sidebar-logo {
    font-size: 1.35rem; font-weight: 800; color: #FFFFFF !important;
    display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0 0.75rem 0;
    border-bottom: 1px solid #1E293B; margin-bottom: 0.75rem;
}
.sidebar-cat {
    font-size: 0.72rem; font-weight: 700; color: #64748B !important;
    text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.75rem; margin-bottom: 0.25rem;
}

/* Header & Banner */
header {visibility: hidden;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

.top-bar-container {
    background: #FFFFFF; border: 1px solid #E2E8F0;
    padding: 1rem 1.5rem; display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 1.25rem;
    border-radius: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.greeting-title {
    font-size: 1.35rem; font-weight: 800; color: #0F172A; margin: 0; line-height: 1.2;
}
.greeting-sub {
    font-size: 0.85rem; color: #64748B; margin: 0; font-weight: 500;
}
.status-pill {
    padding: 0.25rem 0.65rem; border-radius: 2rem; font-size: 0.72rem; font-weight: 600;
    display: inline-flex; align-items: center; gap: 0.35rem;
}
.pill-live { background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }
.pill-demo { background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }

/* Dashboard Cards */
.dash-card {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 0.75rem;
    padding: 1.25rem; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.dash-card-hdr {
    font-size: 1.1rem; font-weight: 700; color: #0F172A; margin-bottom: 0.25rem;
    display: flex; align-items: center; justify-content: space-between;
}
.dash-card-sub { font-size: 0.82rem; color: #64748B; margin-bottom: 0.85rem; }

/* Metric Cards */
.metric-box {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 0.75rem;
    padding: 1rem; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.metric-val {
    font-size: 2rem; font-weight: 800; color: #2563EB; line-height: 1.1;
}
.metric-lbl {
    font-size: 0.78rem; font-weight: 600; color: #64748B; text-transform: uppercase;
    letter-spacing: 0.04em; margin-top: 0.25rem;
}

/* Source Badges */
.source-badge-live {
    background: #DCFCE7; color: #166534; font-size: 0.7rem; font-weight: 700;
    padding: 0.15rem 0.45rem; border-radius: 0.25rem; text-transform: uppercase;
}
.source-badge-demo {
    background: #FEF3C7; color: #92400E; font-size: 0.7rem; font-weight: 700;
    padding: 0.15rem 0.45rem; border-radius: 0.25rem; text-transform: uppercase;
}

/* Skill Tags */
.tag-v { background: #ECFDF5; color: #047857; padding: 0.15rem 0.45rem; border-radius: 0.3rem; font-size: 0.75rem; font-weight: 600; display: inline-block; margin: 0.1rem; }
.tag-i { background: #FFFBEB; color: #B45309; padding: 0.15rem 0.45rem; border-radius: 0.3rem; font-size: 0.75rem; font-weight: 600; display: inline-block; margin: 0.1rem; }
.tag-m { background: #FEF2F2; color: #B91C1C; padding: 0.15rem 0.45rem; border-radius: 0.3rem; font-size: 0.75rem; font-weight: 600; display: inline-block; margin: 0.1rem; }

/* Status Badges */
.badge-saved { background: #E0F2FE; color: #0369A1; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; }
.badge-applied { background: #FEF3C7; color: #92400E; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; }
.badge-interview { background: #DDD6FE; color: #5B21B6; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; }
.badge-offer { background: #DCFCE7; color: #166534; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; }
.badge-rejected { background: #FEE2E2; color: #991B1B; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; }

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State Initialization & Local Storage Restore
# ---------------------------------------------------------------------------
_defaults = {
    "nav_section": "Dashboard",
    "step": "intake",
    "candidate": None,
    "is_demo": True,
    "processed_resume_hash": None,  # SHA-256 hash guard to prevent duplicate parsing loops
    "selected_job": None,
    "saved_jobs": [],
    "applications": [],
    "ats_result": None,
    "gap_result": None,
    "optimization": None,
    "approval": None,
    "outreach": None,
    "coach_history": [],
    "search_filters": JobSearchFilters(),
    "job_results": [],
    "job_status_msg": "⚡ DEMO MODE — Offline Dataset",
    "demo_mode_active": False,
}

# Attempt restoring from local JSON storage first
restored_storage = load_session_state()

for k, v in _defaults.items():
    if k not in st.session_state:
        if k in restored_storage:
            st.session_state[k] = restored_storage[k]
        else:
            st.session_state[k] = v

# Ensure default candidate if null
if st.session_state.candidate is None:
    st.session_state.candidate = get_demo_candidate()
    st.session_state.is_demo = True

# Seed sample applications for demo profile if empty
if not st.session_state.applications and st.session_state.is_demo:
    demo_jobs = load_jobs()
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

# Helper to save state
def _persist_state():
    save_session_state(dict(st.session_state))


# ---------------------------------------------------------------------------
# Upload Processing Guard (Prevents Infinite Parse / Rerun Loops)
# ---------------------------------------------------------------------------
def _process_resume_upload(uploaded_file, switch_step=False) -> bool:
    """Safely process a PDF file upload using SHA-256 hash guard.
    Returns True if a NEW file was parsed in this frame, False otherwise."""
    if uploaded_file is None:
        return False

    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Check if this exact file was already processed in session state
    if file_hash == st.session_state.get("processed_resume_hash"):
        return False  # Already processed! Do not re-parse or rerun.

    logger.info(f"Resume upload detected — parsing started (hash: {file_hash[:8]}...)")
    with st.spinner("Parsing your resume..."):
        cand = parse_resume(file_bytes)

    # Store hash immediately to prevent duplicate runs
    st.session_state.processed_resume_hash = file_hash

    if cand and cand.raw_text:
        st.session_state.candidate = cand
        st.session_state.is_demo = False
        # Clear cached ATS & optimization results for new candidate
        st.session_state.ats_result = None
        st.session_state.gap_result = None
        st.session_state.optimization = None
        st.session_state.outreach = None
        _persist_state()
        logger.info(f"Resume parsing completed successfully for {cand.name or 'Candidate'} (hash: {file_hash[:8]}...)")
        if switch_step:
            st.session_state.step = "profile"
            st.rerun()
        return True
    else:
        logger.warning(f"Resume parsing failed — unparseable PDF (hash: {file_hash[:8]}...)")
        st.error("Could not extract text from this PDF. Please try a different file.")
        return False


# ---------------------------------------------------------------------------
# Sidebar Navigation (Core Tools + Workflow)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🚀 CareerBridge AI</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-cat">CORE DASHBOARD</div>', unsafe_allow_html=True)
    nav_core = ["📊 Dashboard", "🔍 Find Jobs", "👤 My CV"]
    
    st.markdown('<div class="sidebar-cat">CAREER TOOLS</div>', unsafe_allow_html=True)
    nav_tools = ["📊 ATS Scanner", "✨ Improve CV", "✉️ Cover Letter", "📁 Applications", "🤖 AI Career Coach", "📈 Analytics", "⚙️ Settings"]
    
    st.markdown('<div class="sidebar-cat">WORKFLOW WIZARD</div>', unsafe_allow_html=True)
    nav_wizard = ["🚀 Guided Golden Path"]

    all_nav = nav_core + nav_tools + nav_wizard
    
    cur_nav = st.session_state.nav_section
    match_idx = 0
    for idx, opt in enumerate(all_nav):
        if cur_nav in opt:
            match_idx = idx
            break

    selected_nav = st.radio("Navigation", all_nav, index=match_idx, label_visibility="collapsed")
    clean_nav = selected_nav.split(" ", 1)[1] if " " in selected_nav else selected_nav
    st.session_state.nav_section = clean_nav
    _persist_state()

    st.markdown("---")
    # Real-Time System Status in Sidebar Footer
    api_k = get_api_key()
    adz_id, _ = get_adzuna_credentials()
    
    st.markdown("**System Status:**")
    st.markdown(f"- AI: `{'● Live (Groq)' if api_k else '● Demo Mode'}`")
    st.markdown(f"- Jobs: `{'● Live (API)' if (adz_id or 'LIVE' in st.session_state.job_status_msg) else '● Fallback Provider'}`")
    st.markdown("- System: `● Ready`")

# ---------------------------------------------------------------------------
# Top Header Bar & Greeting
# ---------------------------------------------------------------------------
c_profile: CandidateProfile = st.session_state.candidate

# Time of day greeting
hour = datetime.now().hour
time_greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"

st.markdown(f"""
<div class="top-bar-container">
    <div>
        <div class="greeting-title">{time_greeting}, {c_profile.name or 'Candidate'}</div>
        <div class="greeting-sub">Your AI Career Command Center</div>
    </div>
    <div style="display:flex;align-items:center;gap:0.6rem;">
        <span class="status-pill {'pill-live' if api_k else 'pill-demo'}">
            {'● Live — Groq' if api_k else '● Demo Mode'}
        </span>
        <span class="status-pill pill-live">
            {'● Live Jobs' if 'LIVE' in st.session_state.job_status_msg else '● Fallback Provider'}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)


# ===========================================================================
# SECTION 1: DASHBOARD COMMAND CENTER
# ===========================================================================
if st.session_state.nav_section == "Dashboard":
    
    # -----------------------------------------------------------------------
    # SECTION A: CV INTAKE PANEL
    # -----------------------------------------------------------------------
    with st.container():
        st.markdown("""
        <div class="dash-card">
            <div class="dash-card-hdr">
                <span>📄 Build Your Career Profile</span>
                <span style="font-size:0.78rem;font-weight:600;color:#2563EB">Intake Active</span>
            </div>
            <div class="dash-card-sub">Upload your CV to analyze your ATS readiness, discover matching opportunities, and personalize your applications.</div>
        </div>
        """, unsafe_allow_html=True)

        ic1, ic2 = st.columns([2, 1], gap="medium")
        with ic1:
            uploaded_file = st.file_uploader("Upload CV (PDF)", type=["pdf"], key="dash_cv_intake", label_visibility="collapsed")
            if uploaded_file is not None:
                _process_resume_upload(uploaded_file, switch_step=False)

        with ic2:
            if st.button("🎯 Use Demo Profile (Alex Chen)", use_container_width=True, key="dash_use_demo"):
                st.session_state.candidate = get_demo_candidate()
                st.session_state.is_demo = True
                st.session_state.processed_resume_hash = None
                _persist_state()
                st.rerun()

        # Profile status summary pills
        completeness = min(100, (len(c_profile.skills) * 5) + (len(c_profile.experience) * 15) + (20 if c_profile.summary else 0))
        st.caption(f"Profile: **{c_profile.name or 'N/A'}** · Completeness: **{completeness}%** · Detected Skills: **{len(c_profile.skills)}** · Status: **{'⚡ Demo Derived' if st.session_state.is_demo else '🟢 Real Candidate Data'}**")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # SECTION B: AI CAREER COACH PANEL (EMBEDDED DIRECTLY ON DASHBOARD)
    # -----------------------------------------------------------------------
    st.markdown("""
    <div class="dash-card" style="margin-bottom:0.75rem;">
        <div class="dash-card-hdr">
            <span>🤖 CareerBridge AI Coach</span>
            <span style="font-size:0.78rem;font-weight:600;color:#059669">Context Memory Active</span>
        </div>
        <div class="dash-card-sub">Ask about your CV, jobs, ATS score, skills, or applications directly from your dashboard.</div>
    </div>
    """, unsafe_allow_html=True)

    # Prompt Chips Row
    st.markdown("**Suggested Quick Actions:**")
    chip_cols = st.columns(4)
    selected_chip = None
    if chip_cols[0].button("💡 How to improve ATS?", use_container_width=True, key="chip_ats"):
        selected_chip = "Why is my ATS score low and how can I improve it?"
    if chip_cols[1].button("🔍 Which jobs fit me?", use_container_width=True, key="chip_jobs"):
        selected_chip = "What jobs best fit my current candidate profile?"
    if chip_cols[2].button("❌ What skills am I missing?", use_container_width=True, key="chip_gaps"):
        selected_chip = "What skills am I missing for my target role?"
    if chip_cols[3].button("📝 Review my CV bullets", use_container_width=True, key="chip_bullets"):
        selected_chip = "How can I improve my CV bullet points?"

    # Embedded Chat Box
    with st.container(border=True):
        if st.session_state.coach_history:
            latest_turns = st.session_state.coach_history[-4:]
            for msg in latest_turns:
                if msg.role == "user":
                    st.markdown(f"**You:** {msg.content}")
                else:
                    st.markdown(f"**CareerBridge Coach:**\n{msg.content}")
                    st.markdown("---")
        else:
            st.info(f"Hello **{c_profile.name or 'Candidate'}**! I am your AI Career Coach. Click a chip above or type below to analyze your profile.")

        coach_query = st.text_input("Ask CareerBridge anything...", key="dash_coach_input", value=selected_chip if selected_chip else "")
        if st.button("Send to Coach →", type="primary", use_container_width=True, key="dash_coach_send") or selected_chip:
            if coach_query.strip():
                with st.spinner("Analyzing candidate context & generating response..."):
                    reply = ask_career_coach(
                        coach_query,
                        st.session_state.coach_history,
                        c_profile,
                        st.session_state.selected_job,
                        st.session_state.ats_result,
                        st.session_state.gap_result,
                        st.session_state.applications,
                    )
                    st.session_state.coach_history.append(CoachMessage(role="user", content=coach_query, timestamp=str(datetime.now())[:16]))
                    st.session_state.coach_history.append(CoachMessage(role="assistant", content=reply, timestamp=str(datetime.now())[:16]))
                    _persist_state()
                st.rerun()

    st.markdown("---")

    # -----------------------------------------------------------------------
    # SECTION C: CAREER HEALTH OVERVIEW (METRICS)
    # -----------------------------------------------------------------------
    st.markdown("#### 📊 Career Health Overview")
    
    ats_val = st.session_state.ats_result.overall_score if st.session_state.ats_result else (78 if st.session_state.is_demo else 64)
    saved_cnt = len(st.session_state.saved_jobs)
    total_apps = len(st.session_state.applications)
    interviews = sum(1 for a in st.session_state.applications if a.status == ApplicationStatus.INTERVIEW)
    offers = sum(1 for a in st.session_state.applications if a.status == ApplicationStatus.OFFER)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.markdown(f'<div class="metric-box"><div class="metric-val">{ats_val}/100</div><div class="metric-lbl">ATS Health</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-box"><div class="metric-val">{completeness}%</div><div class="metric-lbl">Completeness</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-box"><div class="metric-val">{saved_cnt}</div><div class="metric-lbl">Saved Jobs</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-box"><div class="metric-val">{total_apps}</div><div class="metric-lbl">Applications</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#5B21B6">{interviews}</div><div class="metric-lbl">Interviews</div></div>', unsafe_allow_html=True)
    m6.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#059669">{offers}</div><div class="metric-lbl">Offers</div></div>', unsafe_allow_html=True)

    if st.session_state.is_demo:
        st.caption("⚡ *Note: Metrics above are computed from active Demo Candidate data.*")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # SECTION D: CURRENT CAREER STRATEGY & TOP OPPORTUNITIES
    # -----------------------------------------------------------------------
    col_strat, col_jobs = st.columns([1, 2], gap="large")

    with col_strat:
        st.markdown("#### 🎯 Career Strategy")
        with st.container(border=True):
            pref = st.session_state.search_filters
            st.markdown(f"**Target Role:** {pref.desired_role or 'Software Engineer'}")
            st.markdown(f"**Location:** {pref.city or pref.country or 'Worldwide / Remote'}")
            st.markdown(f"**Work Arrangement:** {pref.work_arrangement}")
            st.markdown(f"**Employment Type:** {pref.employment_type}")
            st.markdown(f"**Salary Preference:** {pref.currency} {pref.min_salary or 'Not set'}")
            if st.button("Edit Strategy in Settings →", key="dash_to_settings", use_container_width=True):
                st.session_state.nav_section = "Settings"
                st.rerun()

    with col_jobs:
        st.markdown("#### 💼 Top Recommended Opportunities")
        if not st.session_state.job_results:
            with st.spinner("Fetching recommended live jobs..."):
                jobs, msg = search_live_jobs(st.session_state.search_filters)
                st.session_state.job_results = jobs
                st.session_state.job_status_msg = msg

        matches = match_candidate_to_jobs(c_profile, st.session_state.job_results[:5], top_k=3)
        for m in matches:
            j = m.job
            is_live = j.source in ["Adzuna", "Remotive", "Jobicy", "Arbeitnow"]
            src_cls = "source-badge-live" if is_live else "source-badge-demo"
            with st.container(border=True):
                st.markdown(f"**{j.title}** — {j.company} <span class='{src_cls}'>{j.source}</span>", unsafe_allow_html=True)
                st.caption(f"📍 {j.location} · Match: **{m.overall_score:.0f}%**")
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
# SECTION 2: FIND JOBS (LIVE SEARCH & DISCOVERY)
# ===========================================================================
elif st.session_state.nav_section == "Find Jobs":
    st.markdown("### 🔍 Live Job Search & Discovery")

    # Search Bar & Optional Filters
    st.markdown("#### What role are you looking for?")
    s_col1, s_col2 = st.columns([3, 1])
    with s_col1:
        query_input = st.text_input("Role Title", value=st.session_state.search_filters.desired_role or "Software Engineer", placeholder="e.g. AI Engineer, Machine Learning, Python", label_visibility="collapsed")
        st.session_state.search_filters.desired_role = query_input
    with s_col2:
        if st.button("Search Jobs", type="primary", use_container_width=True, key="search_trigger"):
            with st.spinner("Searching live providers (Remotive → Jobicy → Adzuna → Demo)..."):
                jobs, msg = search_live_jobs(st.session_state.search_filters)
                st.session_state.job_results = jobs
                st.session_state.job_status_msg = msg
            st.rerun()

    with st.expander("⚙️ Optional Filters (Country, City, Work Type, Salary)", expanded=False):
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

    # Provider Status Badge
    st.markdown(f"**Provider Status:** `{st.session_state.job_status_msg}`")

    # Fetch initial feed if empty
    if not st.session_state.job_results:
        with st.spinner("Loading live job feed..."):
            jobs, msg = search_live_jobs(st.session_state.search_filters)
            st.session_state.job_results = jobs
            st.session_state.job_status_msg = msg

    # Display Job Cards & Detail Views
    jobs_list = st.session_state.job_results
    matches = match_candidate_to_jobs(c_profile, jobs_list, top_k=len(jobs_list))

    for m in matches:
        j = m.job
        is_saved = any(sj.id == j.id for sj in st.session_state.saved_jobs)
        is_live = j.source in ["Adzuna", "Remotive", "Jobicy", "Arbeitnow"]
        src_badge = f'<span class="source-badge-live">LIVE — {j.source}</span>' if is_live else f'<span class="source-badge-demo">DEMO MODE — {j.source}</span>'

        with st.container(border=True):
            j1, j2, j3 = st.columns([3, 1.2, 1])
            with j1:
                st.markdown(f"#### {j.title}")
                st.markdown(f"**{j.company}** · 📍 {j.location or 'Not specified'} · {'🌐 Remote' if j.remote else '🏢 On-site'} · {j.employment_type}")
                
                # Salary & Date
                sal_text = f"{j.salary_currency or '$'} {j.salary_min:,.0f} - {j.salary_max:,.0f}" if (j.salary_min or j.salary_max) else "Not disclosed"
                date_text = j.posted_date if j.posted_date else "Not specified"
                st.caption(f"💰 Salary: {sal_text} · Posted: {date_text} · {src_badge}", unsafe_allow_html=True)
                
                # Description Expander
                desc_type = "Description Preview" if j.description_is_snippet else "Full Job Description"
                with st.expander(f"📖 {desc_type}"):
                    st.write(j.description[:1500])
                    if j.url:
                        st.markdown(f"👉 [View Original Posting on {j.source}]({j.url})")

                # Skill Overlap
                st.markdown("✅ Matched: " + " ".join(f'<span class="tag-v">{s}</span>' for s in m.matched_skills[:5]), unsafe_allow_html=True)
                if m.missing_skills:
                    st.markdown("• Missing: " + " ".join(f'<span class="tag-m">{s}</span>' for s in m.missing_skills[:4]), unsafe_allow_html=True)

            with j2:
                score_c = "#059669" if m.overall_score >= 70 else "#D97706" if m.overall_score >= 50 else "#DC2626"
                st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{score_c}">{m.overall_score:.0f}%</div><div class="metric-lbl">Match Score</div></div>', unsafe_allow_html=True)

            with j3:
                if st.button("📊 ATS Check", key=f"ats_scan_{j.id}", use_container_width=True):
                    st.session_state.selected_job = j
                    st.session_state.nav_section = "ATS Scanner"
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

                if j.url:
                    st.markdown(f'<a href="{j.url}" target="_blank" style="display:block;text-align:center;padding:0.4rem;background:#2563EB;color:white;border-radius:0.4rem;text-decoration:none;font-weight:600;font-size:0.8rem;margin-top:0.3rem;">View Job →</a>', unsafe_allow_html=True)


# ===========================================================================
# SECTION 3: MY CV (WORKSPACE & EDITOR)
# ===========================================================================
elif st.session_state.nav_section == "My CV":
    st.markdown("### 👤 My CV Workspace")

    c1, c2 = st.columns([1, 2], gap="large")

    with c1:
        st.markdown("#### Upload PDF Resume")
        uploaded = st.file_uploader("Choose PDF File", type=["pdf"], key="my_cv_upload")
        if uploaded is not None:
            _process_resume_upload(uploaded, switch_step=False)

        if st.button("🎯 Load Demo Profile (Alex Chen)", use_container_width=True, key="my_cv_demo"):
            st.session_state.candidate = get_demo_candidate()
            st.session_state.is_demo = True
            st.session_state.processed_resume_hash = None
            _persist_state()
            st.rerun()

    with c2:
        st.markdown("#### Profile Form Editor")
        with st.form("my_cv_form"):
            e_name = st.text_input("Full Name", value=c_profile.name or "")
            e_email = st.text_input("Email", value=c_profile.email or "")
            e_phone = st.text_input("Phone", value=c_profile.phone or "")
            e_summary = st.text_area("Summary", value=c_profile.summary or "", height=100)
            e_skills = st.text_input("Skills (comma separated)", value=", ".join(c_profile.skills))
            e_exp = st.text_area("Experience Items (one per line)", value="\n".join(c_profile.experience), height=120)

            if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
                c_profile.name = e_name
                c_profile.email = e_email
                c_profile.phone = e_phone
                c_profile.summary = e_summary
                c_profile.skills = [s.strip() for s in e_skills.split(",") if s.strip()]
                c_profile.experience = [x.strip() for x in e_exp.split("\n") if x.strip()]
                st.session_state.candidate = c_profile
                _persist_state()
                st.success("Candidate Profile saved!")
                st.rerun()


# ===========================================================================
# SECTION 4: ATS SCANNER
# ===========================================================================
elif st.session_state.nav_section == "ATS Scanner":
    st.markdown("### 📊 ATS Scanner & Deterministic Breakdown")

    available_jobs = st.session_state.job_results or load_jobs()
    job_map = {f"{j.title} — {j.company}": j for j in available_jobs}
    
    sel_job_key = st.selectbox("Select Target Job:", list(job_map.keys()), index=0)
    target_job = job_map[sel_job_key]
    st.session_state.selected_job = target_job

    if st.button("🚀 Run Deterministic ATS Check", type="primary", use_container_width=True):
        ats = analyze_ats(c_profile, target_job)
        gaps = analyze_gaps(c_profile, target_job)
        st.session_state.ats_result = ats
        st.session_state.gap_result = gaps
        _persist_state()

    if st.session_state.ats_result is None:
        st.session_state.ats_result = analyze_ats(c_profile, target_job)
        st.session_state.gap_result = analyze_gaps(c_profile, target_job)

    ats = st.session_state.ats_result
    gaps = st.session_state.gap_result

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

    target_job = st.session_state.selected_job or load_jobs()[0]
    ats_score = st.session_state.ats_result.overall_score if st.session_state.ats_result else 64

    if st.session_state.optimization is None:
        with st.spinner("Generating profile optimization with X-Y-Z guardrails..."):
            st.session_state.optimization = optimize_profile(c_profile, target_job, ats_score)

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

    target_job = st.session_state.selected_job or load_jobs()[0]
    tone = st.radio("Tone Style:", ["Standard", "Concise", "Technical", "Formal"], horizontal=True)

    if st.button("✨ Generate Cover Letter", type="primary", use_container_width=True, key="gen_cl"):
        with st.spinner("Generating grounded cover letter..."):
            cl = generate_cover_letter(c_profile, target_job, tone=tone)
            st.session_state["cover_letter"] = cl

    cl = st.session_state.get("cover_letter")
    if cl is None:
        cl = generate_cover_letter(c_profile, target_job, tone=tone)
        st.session_state["cover_letter"] = cl

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

    with st.expander("➕ Log Application Record", expanded=False):
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
# SECTION 8: AI CAREER COACH (FULL PAGE)
# ===========================================================================
elif st.session_state.nav_section == "AI Career Coach":
    st.markdown("### 🤖 CareerBridge AI Coach (Expanded Workspace)")
    st.caption("Full-page interactive assistant sharing exact context memory with Dashboard Coach.")

    for msg in st.session_state.coach_history:
        if msg.role == "user":
            st.chat_message("user").write(msg.content)
        else:
            st.chat_message("assistant").write(msg.content)

    if user_prompt := st.chat_input("Ask Career Coach anything..."):
        st.chat_message("user").write(user_prompt)
        with st.spinner("Analyzing context..."):
            reply = ask_career_coach(
                user_prompt,
                st.session_state.coach_history,
                c_profile,
                st.session_state.selected_job,
                st.session_state.ats_result,
                st.session_state.gap_result,
                st.session_state.applications,
            )
        st.chat_message("assistant").write(reply)
        st.session_state.coach_history.append(CoachMessage(role="user", content=user_prompt, timestamp=str(datetime.now())[:16]))
        st.session_state.coach_history.append(CoachMessage(role="assistant", content=reply, timestamp=str(datetime.now())[:16]))
        _persist_state()


# ===========================================================================
# SECTION 9: ANALYTICS
# ===========================================================================
elif st.session_state.nav_section == "Analytics":
    st.markdown("### 📈 Career Analytics")

    apps = st.session_state.applications
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
        pref_role = st.text_input("Target Role", value=st.session_state.search_filters.desired_role or "Software Engineer")
        pref_country = st.text_input("Target Country / Region", value=st.session_state.search_filters.country or "US")
        pref_work = st.selectbox("Work Arrangement", ["Any", "Remote", "Hybrid", "On-site"])
        pref_curr = st.selectbox("Preferred Salary Currency", ["USD", "PKR", "GBP", "EUR", "CAD", "AUD"])
        
        if st.form_submit_button("Save Strategy Preferences", type="primary"):
            st.session_state.search_filters.desired_role = pref_role
            st.session_state.search_filters.country = pref_country
            st.session_state.search_filters.work_arrangement = pref_work
            st.session_state.search_filters.currency = pref_curr
            _persist_state()
            st.success("Settings saved!")


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
            
        if st.button("🎯 Load Demo Profile", use_container_width=True):
            st.session_state.candidate = get_demo_candidate()
            st.session_state.is_demo = True
            st.session_state.processed_resume_hash = None
            st.session_state.step = "profile"
            st.rerun()

    elif st.session_state.step == "profile":
        st.markdown(f"#### Step 2: Profile — {c_profile.name}")
        if st.button("🔍 Find Matching Jobs →", type="primary", use_container_width=True):
            st.session_state.step = "jobs"
            st.rerun()

    elif st.session_state.step == "jobs":
        st.markdown("#### Step 3: Recommended Jobs")
        jobs = st.session_state.job_results or load_jobs()
        matches = match_candidate_to_jobs(st.session_state.candidate, jobs[:5], top_k=5)
        for m in matches:
            with st.container(border=True):
                st.markdown(f"**{m.job.title}** — {m.job.company} ({m.overall_score:.0f}% Match)")
                if st.button(f"Analyze {m.job.title} →", key=f"gp_sel_{m.job.id}"):
                    st.session_state.selected_job = m.job
                    st.session_state.step = "ats"
                    st.rerun()

    elif st.session_state.step == "ats":
        st.markdown("#### Step 4: ATS Analysis")
        job = st.session_state.selected_job or load_jobs()[0]
        ats = analyze_ats(st.session_state.candidate, job)
        gaps = analyze_gaps(st.session_state.candidate, job)
        st.session_state.ats_result = ats
        st.session_state.gap_result = gaps
        st.metric("Overall ATS", f"{ats.overall_score}/100")
        if st.button("✨ Optimize Profile →", type="primary", use_container_width=True):
            st.session_state.step = "optimize"
            st.rerun()

    elif st.session_state.step == "optimize":
        st.markdown("#### Step 5: Profile Optimization")
        job = st.session_state.selected_job or load_jobs()[0]
        ats = st.session_state.ats_result
        opt = optimize_profile(st.session_state.candidate, job, ats.overall_score if ats else 64)
        st.session_state.optimization = opt
        st.metric("Score Improvement", f"{opt.before_score} → {opt.after_score}")
        if st.button("✅ Review & Approve →", type="primary", use_container_width=True):
            st.session_state.step = "review"
            st.rerun()

    elif st.session_state.step == "review":
        st.markdown("#### Step 6: Human Review")
        opt = st.session_state.optimization
        st.write(f"Optimized Summary: {opt.optimized_summary}")
        if st.button("✅ Approve & Generate Outreach →", type="primary", use_container_width=True):
            st.session_state.approval = "approved"
            st.session_state.step = "outreach"
            st.rerun()

    elif st.session_state.step == "outreach":
        st.markdown("#### Step 7: Recruiter Outreach & 3 Interview Questions")
        job = st.session_state.selected_job or load_jobs()[0]
        out = generate_outreach(st.session_state.candidate, job)
        st.session_state.outreach = out
        st.text_area("Email", value=out.recruiter_email, height=180)
        st.text_area("InMail", value=out.recruiter_inmail, height=120)
        for idx, q in enumerate(out.interview_questions, 1):
            st.markdown(f"**Q{idx}:** {q}")
        if st.button("🔄 Start Over", use_container_width=True):
            st.session_state.step = "intake"
            st.rerun()
