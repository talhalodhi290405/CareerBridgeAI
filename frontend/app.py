"""CareerBridge AI — Autonomous Talent Triage & Profile Optimization System.

Single-process Streamlit application. No external backend required.
Run with: streamlit run frontend/app.py
"""
import sys
import os

# Ensure project root is on the path for backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CareerBridge AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Imports — all in-process, no HTTP calls
# ---------------------------------------------------------------------------
from backend.models import (
    CandidateProfile, JobPosting, MatchResult, ATSAnalysis,
    GapAnalysis, OptimizedProfile, OutreachPackage, SkillClassification,
)
from backend.config import is_demo_mode, logger
from backend.parser import parse_resume, parse_resume_text
from backend.rag_engine import load_jobs, match_candidate_to_jobs
from backend.ats_engine import analyze_ats, analyze_gaps
from backend.optimizer import optimize_profile
from backend.outreach import generate_outreach
from backend.demo import (
    get_demo_candidate, get_demo_ats_analysis, get_demo_gap_analysis,
    get_demo_optimized_profile, get_demo_outreach, get_demo_match_result,
    get_demo_target_job_id,
)

# ---------------------------------------------------------------------------
# Premium CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #0454D9;
    --primary-light: #3B82F6;
    --primary-dark: #1E3A8A;
    --accent: #06B6D4;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --bg: #F1F5F9;
    --card: #FFFFFF;
    --text: #0F172A;
    --text-muted: #64748B;
    --border: #E2E8F0;
    --radius: 1rem;
}

.stApp {
    background-color: var(--bg);
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit defaults */
header {visibility: hidden;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

/* Header */
.hero-title {
    font-size: 2.5rem; font-weight: 800; color: var(--text);
    text-align: center; margin-bottom: 0.25rem; letter-spacing: -0.03em;
}
.hero-sub {
    font-size: 1.05rem; color: var(--text-muted);
    text-align: center; margin-bottom: 1.5rem; font-weight: 400;
}
.mode-badge {
    display: inline-block; padding: 0.25rem 0.75rem; border-radius: 2rem;
    font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.05em;
}
.mode-live {background: #DCFCE7; color: #166534;}
.mode-demo {background: #FEF3C7; color: #92400E;}

/* Buttons */
.stButton>button {
    background-color: var(--primary) !important;
    color: white !important; border-radius: 0.75rem !important;
    border: none !important; padding: 0.55rem 1.1rem !important;
    font-weight: 600 !important; font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(4,84,217,0.15) !important;
}
.stButton>button:hover {
    background-color: var(--primary-dark) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(4,84,217,0.25) !important;
}

/* Metrics */
[data-testid="stMetricValue"] {
    font-size: 2.75rem !important; font-weight: 800 !important;
    color: var(--primary) !important;
}
[data-testid="stMetricDelta"] {font-weight: 600 !important;}

/* Progress bars */
.stProgress > div > div {border-radius: 1rem; height: 0.5rem;}

/* Section headers */
.section-hdr {
    font-size: 1.35rem; font-weight: 700; color: var(--text);
    margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;
}

/* Score card */
.score-card {
    text-align: center; padding: 1.5rem; border-radius: var(--radius);
    border: 1px solid var(--border); background: var(--card);
}
.score-big {font-size: 3rem; font-weight: 800; line-height: 1;}
.score-label {font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;}

/* Skill tags */
.skill-tag {
    display: inline-block; padding: 0.2rem 0.6rem; margin: 0.15rem;
    border-radius: 0.5rem; font-size: 0.8rem; font-weight: 500;
}
.tag-verified {background: #DCFCE7; color: #166534;}
.tag-inferred {background: #FEF3C7; color: #92400E;}
.tag-missing  {background: #FEE2E2; color: #991B1B;}
.tag-matched  {background: #DBEAFE; color: #1E40AF;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
_defaults = {
    "step": "intake",           # intake → profile → jobs → ats → optimize → review → outreach
    "candidate": None,          # CandidateProfile
    "is_demo": False,           # using demo profile?
    "jobs": None,               # list[JobPosting]
    "matches": None,            # list[MatchResult]
    "selected_match": None,     # MatchResult
    "ats_result": None,         # ATSAnalysis
    "gap_result": None,         # GapAnalysis
    "optimization": None,       # OptimizedProfile
    "approval": None,           # "approved" | "rejected" | None
    "outreach": None,           # OutreachPackage
    "demo_mode_active": False,  # AI fallback engaged
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _reset():
    for k, v in _defaults.items():
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="hero-title">🚀 CareerBridge AI</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Autonomous Talent Triage & Profile Optimization</div>', unsafe_allow_html=True)

# Mode badge
if is_demo_mode() or st.session_state.get("demo_mode_active"):
    st.markdown('<div style="text-align:center"><span class="mode-badge mode-demo">⚡ Demo Mode — Pre-computed Results</span></div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center"><span class="mode-badge mode-live">🟢 Live — AI-Powered</span></div>', unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Progress bar
# ---------------------------------------------------------------------------
_step_order = ["intake", "profile", "jobs", "ats", "optimize", "review", "outreach"]
_step_labels = {
    "intake": "📄 Resume", "profile": "👤 Profile", "jobs": "💼 Jobs",
    "ats": "📊 ATS", "optimize": "✨ Optimize", "review": "✅ Review", "outreach": "📧 Outreach"
}
current_idx = _step_order.index(st.session_state.step) if st.session_state.step in _step_order else 0
progress = current_idx / (len(_step_order) - 1)
cols = st.columns(len(_step_order))
for i, step_key in enumerate(_step_order):
    with cols[i]:
        if i <= current_idx:
            st.markdown(f"<div style='text-align:center;font-size:0.8rem;font-weight:600;color:var(--primary)'>{_step_labels[step_key]}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:center;font-size:0.8rem;color:var(--text-muted)'>{_step_labels[step_key]}</div>", unsafe_allow_html=True)
st.progress(progress)


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: RESUME INTAKE
# ═══════════════════════════════════════════════════════════════════════════
if st.session_state.step == "intake":
    st.markdown('<div class="section-hdr">📄 Resume Intake</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("#### Upload Your Resume")
        uploaded = st.file_uploader("Upload a PDF resume", type=["pdf"], key="pdf_upload")
        if uploaded is not None:
            with st.spinner("Parsing resume…"):
                candidate = parse_resume(uploaded.getvalue())
            if candidate and candidate.raw_text:
                st.session_state.candidate = candidate
                st.session_state.is_demo = False
                st.session_state.step = "profile"
                st.rerun()
            else:
                st.error("Could not extract text from this PDF. Please try a different file.")

    with col2:
        st.markdown("#### Or Load Demo Profile")
        st.info("Load a pre-built candidate profile to explore the full CareerBridge workflow without uploading a resume.")
        if st.button("🎯 Load Demo Profile", use_container_width=True, key="load_demo"):
            st.session_state.candidate = get_demo_candidate()
            st.session_state.is_demo = True
            st.session_state.step = "profile"
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: CANDIDATE PROFILE
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "profile":
    c: CandidateProfile = st.session_state.candidate
    st.markdown('<div class="section-hdr">👤 Candidate Profile</div>', unsafe_allow_html=True)

    # Identity row
    id_cols = st.columns(4)
    id_cols[0].markdown(f"**Name:** {c.name or 'N/A'}")
    id_cols[1].markdown(f"**Email:** {c.email or 'N/A'}")
    id_cols[2].markdown(f"**Phone:** {c.phone or 'N/A'}")
    id_cols[3].markdown(f"**Location:** {c.location or 'N/A'}")

    if c.summary:
        st.markdown(f"**Summary:** {c.summary}")

    col_a, col_b = st.columns(2)
    with col_a:
        if c.skills:
            st.markdown("**Skills**")
            skills_html = " ".join(f'<span class="skill-tag tag-matched">{s}</span>' for s in c.skills)
            st.markdown(skills_html, unsafe_allow_html=True)

        if c.education:
            st.markdown("**Education**")
            for ed in c.education:
                st.markdown(f"- {ed}")

        if c.certifications:
            st.markdown("**Certifications**")
            for cert in c.certifications:
                st.markdown(f"- {cert}")

    with col_b:
        if c.experience:
            st.markdown("**Experience**")
            for exp in c.experience[:6]:
                st.markdown(f"- {exp}")

        if c.projects:
            st.markdown("**Projects**")
            for proj in c.projects[:4]:
                st.markdown(f"- {proj}")

    st.markdown("---")
    bc1, bc2 = st.columns([1, 5])
    with bc1:
        if st.button("← Back", key="back_to_intake"):
            _reset()
            st.rerun()
    with bc2:
        if st.button("🔍 Find Matching Jobs →", type="primary", use_container_width=True, key="find_jobs"):
            with st.spinner("Loading jobs and computing matches…"):
                jobs = load_jobs()
                st.session_state.jobs = jobs
                matches = match_candidate_to_jobs(c, jobs, top_k=5)
                st.session_state.matches = matches
            st.session_state.step = "jobs"
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: JOB MATCHING
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "jobs":
    st.markdown('<div class="section-hdr">💼 Recommended Jobs</div>', unsafe_allow_html=True)
    matches = st.session_state.matches or []

    if not matches:
        st.warning("No matching jobs found. Try a different resume.")
    else:
        for i, m in enumerate(matches):
            j = m.job
            with st.container(border=True):
                jc1, jc2, jc3 = st.columns([3, 1, 1])
                with jc1:
                    st.markdown(f"**{j.title}** — {j.company}")
                    st.caption(f"📍 {j.location} {'🌐 Remote' if j.remote else '🏢 Onsite'} · {j.experience_level} · {j.type}")
                    matched_tags = " ".join(f'<span class="skill-tag tag-verified">{s}</span>' for s in m.matched_skills[:5])
                    missing_tags = " ".join(f'<span class="skill-tag tag-missing">{s}</span>' for s in m.missing_skills[:4])
                    st.markdown(f"✅ {matched_tags}", unsafe_allow_html=True)
                    if missing_tags:
                        st.markdown(f"❌ {missing_tags}", unsafe_allow_html=True)
                with jc2:
                    score_color = "#10B981" if m.overall_score >= 70 else "#F59E0B" if m.overall_score >= 50 else "#EF4444"
                    st.markdown(f'<div class="score-card"><div class="score-big" style="color:{score_color}">{m.overall_score:.0f}%</div><div class="score-label">Match Score</div></div>', unsafe_allow_html=True)
                with jc3:
                    if st.button("Analyze →", key=f"sel_{i}", use_container_width=True):
                        st.session_state.selected_match = m
                        st.session_state.step = "ats"
                        st.rerun()

    st.markdown("---")
    if st.button("← Back to Profile", key="back_to_profile"):
        st.session_state.step = "profile"
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: ATS ANALYSIS + GAP ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "ats":
    m: MatchResult = st.session_state.selected_match
    c: CandidateProfile = st.session_state.candidate
    job = m.job

    # Compute ATS if not cached
    if st.session_state.ats_result is None:
        with st.spinner("Running ATS analysis…"):
            try:
                if st.session_state.is_demo and is_demo_mode():
                    ats = get_demo_ats_analysis()
                    gaps = get_demo_gap_analysis()
                    st.session_state.demo_mode_active = True
                else:
                    ats = analyze_ats(c, job)
                    gaps = analyze_gaps(c, job)
            except Exception as e:
                logger.error(f"ATS analysis failed: {e}")
                ats = get_demo_ats_analysis()
                gaps = get_demo_gap_analysis()
                st.session_state.demo_mode_active = True
        st.session_state.ats_result = ats
        st.session_state.gap_result = gaps

    ats: ATSAnalysis = st.session_state.ats_result
    gaps: GapAnalysis = st.session_state.gap_result

    st.markdown(f'<div class="section-hdr">📊 ATS Analysis — {job.title} at {job.company}</div>', unsafe_allow_html=True)

    # Score cards
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    score_color = "#10B981" if ats.overall_score >= 70 else "#F59E0B" if ats.overall_score >= 50 else "#EF4444"
    sc1.markdown(f'<div class="score-card"><div class="score-big" style="color:{score_color}">{ats.overall_score}</div><div class="score-label">Overall ATS</div></div>', unsafe_allow_html=True)
    sc2.markdown(f'<div class="score-card"><div class="score-big" style="color:var(--primary);font-size:2rem">{ats.skills_match}%</div><div class="score-label">Skills Match</div></div>', unsafe_allow_html=True)
    sc3.markdown(f'<div class="score-card"><div class="score-big" style="color:var(--primary);font-size:2rem">{ats.keyword_match}%</div><div class="score-label">Keywords</div></div>', unsafe_allow_html=True)
    sc4.markdown(f'<div class="score-card"><div class="score-big" style="color:var(--primary);font-size:2rem">{ats.experience_match}%</div><div class="score-label">Experience</div></div>', unsafe_allow_html=True)
    sc5.markdown(f'<div class="score-card"><div class="score-big" style="color:var(--primary);font-size:2rem">{ats.format_score}%</div><div class="score-label">Format</div></div>', unsafe_allow_html=True)

    st.markdown(f"**Summary:** {ats.summary}")

    # Strengths & Gaps
    sg1, sg2 = st.columns(2)
    with sg1:
        st.markdown("##### ✅ Strengths")
        for s in ats.strengths:
            st.success(s, icon="✔️")
    with sg2:
        st.markdown("##### ❌ Gaps")
        for g in ats.gaps:
            st.error(g, icon="⚠️")

    if ats.recommendations:
        st.markdown("##### 💡 Recommendations")
        for r in ats.recommendations:
            st.info(r, icon="💡")

    # Gap Analysis
    st.markdown("---")
    st.markdown('<div class="section-hdr">🔍 Skill Gap Analysis</div>', unsafe_allow_html=True)

    gc1, gc2, gc3 = st.columns(3)
    with gc1:
        st.markdown(f"##### ✅ Verified ({len(gaps.verified_skills)})")
        for sk in gaps.verified_skills:
            st.markdown(f'<span class="skill-tag tag-verified">{sk.name}</span>', unsafe_allow_html=True)
            if sk.evidence:
                st.caption(sk.evidence)
    with gc2:
        st.markdown(f"##### 🟡 Inferred ({len(gaps.inferred_skills)})")
        for sk in gaps.inferred_skills:
            st.markdown(f'<span class="skill-tag tag-inferred">{sk.name}</span>', unsafe_allow_html=True)
            if sk.evidence:
                st.caption(sk.evidence)
    with gc3:
        st.markdown(f"##### ❌ Missing ({len(gaps.missing_skills)})")
        for sk in gaps.missing_skills:
            st.markdown(f'<span class="skill-tag tag-missing">{sk.name}</span>', unsafe_allow_html=True)

    if gaps.profile_weaknesses:
        st.markdown("**Profile Weaknesses:**")
        for w in gaps.profile_weaknesses:
            st.warning(w, icon="⚠️")

    st.markdown("---")
    bc1, bc2 = st.columns([1, 5])
    with bc1:
        if st.button("← Back", key="back_to_jobs"):
            st.session_state.ats_result = None
            st.session_state.gap_result = None
            st.session_state.step = "jobs"
            st.rerun()
    with bc2:
        if st.button("✨ Optimize Profile →", type="primary", use_container_width=True, key="run_optimize"):
            st.session_state.step = "optimize"
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: OPTIMIZATION — BEFORE / AFTER
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "optimize":
    c: CandidateProfile = st.session_state.candidate
    m: MatchResult = st.session_state.selected_match
    ats: ATSAnalysis = st.session_state.ats_result
    job = m.job

    if st.session_state.optimization is None:
        with st.spinner("Generating optimized profile…"):
            try:
                if st.session_state.is_demo and is_demo_mode():
                    opt = get_demo_optimized_profile()
                    st.session_state.demo_mode_active = True
                else:
                    opt = optimize_profile(c, job, ats.overall_score)
            except Exception as e:
                logger.error(f"Optimization failed: {e}")
                opt = get_demo_optimized_profile()
                st.session_state.demo_mode_active = True
        st.session_state.optimization = opt

    opt: OptimizedProfile = st.session_state.optimization

    st.markdown('<div class="section-hdr">✨ Profile Optimization</div>', unsafe_allow_html=True)

    # Score comparison
    sc1, sc2, sc3 = st.columns([2, 1, 2])
    before_color = "#EF4444" if opt.before_score < 50 else "#F59E0B" if opt.before_score < 70 else "#10B981"
    after_color = "#10B981" if opt.after_score >= 70 else "#F59E0B"
    with sc1:
        st.markdown(f'<div class="score-card"><div class="score-big" style="color:{before_color}">{opt.before_score}</div><div class="score-label">Before Optimization</div></div>', unsafe_allow_html=True)
    with sc2:
        st.markdown('<div style="text-align:center;padding-top:2rem;font-size:2rem">→</div>', unsafe_allow_html=True)
    with sc3:
        st.markdown(f'<div class="score-card"><div class="score-big" style="color:{after_color}">{opt.after_score}</div><div class="score-label">After Optimization</div></div>', unsafe_allow_html=True)

    delta = opt.after_score - opt.before_score
    st.metric("Score Improvement", f"+{delta} points", delta=f"+{delta}")

    # Summary comparison
    st.markdown("---")
    st.markdown("##### Professional Summary")
    bs1, bs2 = st.columns(2)
    with bs1:
        st.markdown("**Before:**")
        st.warning(opt.original_summary)
    with bs2:
        st.markdown("**After:**")
        st.success(opt.optimized_summary)

    # Bullets comparison
    st.markdown("##### Experience Bullets")
    bb1, bb2 = st.columns(2)
    with bb1:
        st.markdown("**Original:**")
        for b in opt.original_bullets:
            st.markdown(f"- {b}")
    with bb2:
        st.markdown("**Optimized:**")
        for b in opt.optimized_bullets:
            st.markdown(f"- ✨ {b}")

    # Improvements made
    if opt.improvements_made:
        st.markdown("##### 🔧 Improvements Made")
        for imp in opt.improvements_made:
            st.info(imp, icon="🔧")

    st.markdown("---")
    bc1, bc2 = st.columns([1, 5])
    with bc1:
        if st.button("← Back", key="back_to_ats"):
            st.session_state.optimization = None
            st.session_state.step = "ats"
            st.rerun()
    with bc2:
        if st.button("✅ Review & Approve →", type="primary", use_container_width=True, key="go_review"):
            st.session_state.step = "review"
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: HUMAN REVIEW / APPROVAL
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "review":
    opt: OptimizedProfile = st.session_state.optimization
    st.markdown('<div class="section-hdr">✅ Human Review</div>', unsafe_allow_html=True)

    st.markdown("Review the optimized profile below. Approve to generate recruiter outreach, or reject to regenerate.")

    with st.container(border=True):
        st.markdown(f"**Optimized Summary:** {opt.optimized_summary}")
        st.markdown("**Optimized Bullets:**")
        for b in opt.optimized_bullets:
            st.markdown(f"- {b}")
        st.markdown(f"**Score:** {opt.before_score} → **{opt.after_score}**")

    st.markdown("---")
    ac1, ac2, ac3 = st.columns([2, 2, 1])
    with ac1:
        if st.button("✅ Approve Optimization", type="primary", use_container_width=True, key="approve_btn"):
            st.session_state.approval = "approved"
            st.session_state.step = "outreach"
            st.rerun()
    with ac2:
        if st.button("🔄 Reject & Regenerate", use_container_width=True, key="reject_btn"):
            st.session_state.approval = "rejected"
            st.session_state.optimization = None
            st.session_state.step = "optimize"
            st.rerun()
    with ac3:
        if st.button("← Back", key="back_to_opt"):
            st.session_state.step = "optimize"
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# STEP 7: OUTREACH & INTERVIEW
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "outreach":
    c: CandidateProfile = st.session_state.candidate
    m: MatchResult = st.session_state.selected_match
    job = m.job

    if st.session_state.outreach is None:
        with st.spinner("Generating recruiter outreach and interview questions…"):
            try:
                if st.session_state.is_demo and is_demo_mode():
                    out = get_demo_outreach()
                    st.session_state.demo_mode_active = True
                else:
                    out = generate_outreach(c, job)
            except Exception as e:
                logger.error(f"Outreach generation failed: {e}")
                out = get_demo_outreach()
                st.session_state.demo_mode_active = True
        st.session_state.outreach = out

    out: OutreachPackage = st.session_state.outreach

    st.markdown('<div class="section-hdr">📧 Recruiter Outreach & Interview Prep</div>', unsafe_allow_html=True)

    tab_email, tab_inmail, tab_questions = st.tabs(["📧 Recruiter Email", "💬 LinkedIn InMail", "🎯 Interview Questions"])

    with tab_email:
        st.markdown("##### Personalized Recruiter Email")
        st.text_area("Email", value=out.recruiter_email, height=300, key="email_display", disabled=False)

    with tab_inmail:
        st.markdown("##### LinkedIn InMail Message")
        st.text_area("InMail", value=out.recruiter_inmail, height=200, key="inmail_display", disabled=False)

    with tab_questions:
        st.markdown("##### Technical Interview Preparation")
        st.markdown(f"Tailored for: **{job.title}** at **{job.company}**")
        for i, q in enumerate(out.interview_questions[:3], 1):
            with st.container(border=True):
                st.markdown(f"**Question {i}**")
                st.markdown(q)

    st.markdown("---")
    fc1, fc2 = st.columns([1, 3])
    with fc1:
        if st.button("← Back to Review", key="back_to_review"):
            st.session_state.outreach = None
            st.session_state.step = "review"
            st.rerun()
    with fc2:
        if st.button("🔄 Start Over", use_container_width=True, key="start_over"):
            _reset()
            st.rerun()

    st.success("🎉 CareerBridge AI workflow complete! Your optimized profile, outreach, and interview prep are ready.", icon="🚀")
