import streamlit as st
import requests
import os
from dotenv import load_dotenv
import pdfplumber
import time

load_dotenv()

# --- CONFIG & BRANDING ---
st.set_page_config(page_title="CareerBridge AI", page_icon="🚀", layout="wide")

# --- LOVABLE-INSPIRED CUSTOM CSS ---
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #F8FAFC;
    }

    /* White card aesthetic for content areas */
    div[data-testid="stVerticalBlock"] > div:has(div.stMarkdown) {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }

    /* Customizing buttons for a premium look */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: 1px solid #E2E8F0;
    }
    .stButton>button:hover {
        border-color: #0454D9;
        color: #0454D9;
        transform: translateY(-2px);
    }

    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #0454D9 !important;
        font-weight: 700 !important;
    }

    /* Customizing text areas */
    .stTextArea textarea {
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
    }

    /* Hide default Streamlit header/footer for a SaaS feel */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'resume_text' not in st.session_state: st.session_state.resume_text = ""
if 'temp_file_path' not in st.session_state: st.session_state.temp_file_path = None
if 'selected_job' not in st.session_state: st.session_state.selected_job = None
if 'thread_id' not in st.session_state: st.session_state.thread_id = None
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None
if 'outreach_results' not in st.session_state: st.session_state.outreach_results = None
if 'final_deliverable' not in st.session_state: st.session_state.final_deliverable = ""
if 'applications' not in st.session_state: st.session_state.applications = []
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'workflow_step' not in st.session_state: st.session_state.workflow_step = 'START'

backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #0B1B3D;'>🚀 CareerBridge AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B; font-size: 1.2rem;'>Autonomous AI-Powered Placement Triage & Profile Optimization</p>", unsafe_allow_html=True)
st.divider()

# --- MAIN LAYOUT ---
main_col, side_col = st.columns([3, 1], gap="large")

# ------------------------------------------------------------------------------
# LEFT COLUMN: THE WORKSPACE
# ------------------------------------------------------------------------------
with main_col:
    # INPUT AREA
    with st.container():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("#### 📄 Asset Upload")
            input_mode = st.radio("Input Method", ["Upload PDF CV", "Text Profile"], horizontal=True)
            if input_mode == "Upload PDF CV":
                uploaded_file = st.file_uploader("PDF Resume", type=["pdf"])
                if uploaded_file:
                    with pdfplumber.open(uploaded_file) as pdf:
                        st.session_state.resume_text = "".join([page.extract_text() or "" for page in pdf.pages])
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f: f.write(uploaded_file.getvalue())
                    st.session_state.temp_file_path = temp_path
            else:
                st.session_state.resume_text = st.text_area("Profile Details", placeholder="Describe your experience...", height=150)

        with col2:
            st.markdown("#### 🎯 Target Preferences")
            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1: role = st.text_input("Role", placeholder="e.g. Python Dev")
            with p_col2: location = st.selectbox("Location", ["Remote", "Onsite", "Global", "Hybrid"])
            with p_col3: job_type = st.selectbox("Type", ["Full-time", "Internship", "Contract"])

            if st.button("🔍 Find Best Matches", type="primary", use_container_width=True):
                if not st.session_state.resume_text or not role:
                    st.error("Missing CV or Role.")
                else:
                    with st.spinner("Searching..."):
                        resp = requests.post(f"{backend_url}/api/match_jobs",
                                           json={"resume_text": st.session_state.resume_text, "role": role, "location": location, "job_type": job_type})
                        if resp.status_code == 200:
                            st.session_state.matches = resp.json().get("matches", [])
                            st.session_state.workflow_step = 'MATCHED'
                            st.rerun()

    # THE CORE FEATURE TABS
    if st.session_state.workflow_step in ['MATCHED', 'ANALYZING', 'VALIDATING', 'EDITING']:
        st.markdown("---")

        # Define the 4 Core Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["💼 Job Matches", "📄 CV Builder", "✉️ Cover Letter & Emails", "🎯 Interview Prep"])

        # --- TAB 1: JOB MATCHES ---
        with tab1:
            if st.session_state.workflow_step == 'MATCHED':
                st.subheader("Best Matching Roles")
                for match in st.session_state.matches:
                    meta = match['metadata']
                    with st.container(border=True):
                        st.markdown(f"**{meta['title']}** | {meta['company']}")
                        st.write(match['document'][:200] + "...")
                        if st.button(f"Run AI Analysis", key=match['id'], use_container_width=True):
                            st.session_state.selected_job = match
                            st.session_state.workflow_step = 'ANALYZING'
                            st.rerun()

            elif st.session_state.workflow_step in ['ANALYZING', 'VALIDATING', 'EDITING']:
                # Show the ATS Score and Gap Analysis
                if st.session_state.analysis_results:
                    res = st.session_state.analysis_results
                    ats = res.get("ats_results", {})
                    st.subheader(f"ATS Report: {st.session_state.selected_job['metadata']['title']}")

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric("Composite Match Score", f"{ats.get('ats_score', 'N/A')}%", delta=ats.get("recommendation", ""))
                    with c2:
                        st.info(f"**AI Summary:** {ats.get('brief_summary', 'N/A')}")

                    st.markdown("**Skill Gap Analysis**")
                    g_col1, g_col2 = st.columns(2)
                    with g_col1:
                        with st.expander("✅ Matched Skills", expanded=True):
                            for s in ats.get("matched_skills", []): st.write(f"✔️ {s}")
                    with g_col2:
                        with st.expander("❌ Missing Skills", expanded=True):
                            for s in ats.get("missing_skills", []): st.write(f"⚠️ {s}")

                if st.session_state.workflow_step == 'ANALYZING':
                    with st.status("Digital FTE is analyzing...", expanded=True) as status:
                        st.write("🤖 Agent: Calculating Predictive ATS Score...")
                        time.sleep(0.5)
                        resp = requests.post(f"{backend_url}/api/analyze_full",
                                           json={"file_path": st.session_state.temp_file_path, "job_id": st.session_state.selected_job['id']})
                        if resp.status_code == 200:
                            st.session_state.analysis_results = resp.json()
                            st.session_state.thread_id = resp.json().get("thread_id")
                            st.session_state.workflow_step = 'VALIDATING'
                            status.update(label="Analysis Complete", state="complete")
                            st.rerun()

        # --- TAB 2: CV BUILDER (X-Y-Z Formula) ---
        with tab2:
            if st.session_state.workflow_step == 'VALIDATING':
                st.subheader("X-Y-Z Bullet Point Optimizer")
                opt = st.session_state.analysis_results.get("optimizer_results", {})
                st.markdown("The AI has rewritten your points using the **X-Y-Z Formula**: *'Accomplished [X] as measured by [Y], by doing [Z]'*")

                for b in opt.get("suggested_bullet_points", []):
                    st.write(f"✨ {b}")

                if st.button("✅ Approve & Generate Outreach", type="primary", use_container_width=True):
                    with st.spinner("Drafting deliverables..."):
                        app_resp = requests.post(f"{backend_url}/api/approve", json={"thread_id": st.session_state.thread_id})
                        if app_resp.status_code == 200:
                            outreach = app_resp.json().get("outreach_results", {})
                            st.session_state.outreach_results = outreach
                            st.session_state.final_deliverable = f"COVER LETTER:\n{outreach.get('cover_letter')}\n\nEMAIL:\n{outreach.get('recruiter_email')}"
                            st.session_state.workflow_step = 'EDITING'
                            st.rerun()
            elif st.session_state.workflow_step == 'EDITING':
                st.subheader("Final CV Polish")
                st.text_area("Final Edit:", value=st.session_state.final_deliverable, height=400, key="cv_editor")
            else:
                st.info("Please select a job and approve the analysis to unlock the CV Builder.")

        # --- TAB 3: COVER LETTER & EMAILS ---
        with tab3:
            if st.session_state.workflow_step == 'EDITING':
                st.subheader("Tailored Outreach")
                out = st.session_state.outreach_results
                with st.container(border=True):
                    st.markdown("**Professional Cover Letter**")
                    st.write(out.get("cover_letter", "N/A"))
                with st.container(border=True):
                    st.markdown("**Cold Recruiter InMail**")
                    st.write(out.get("recruiter_email", "N/A"))
            else:
                st.info("Approval required to generate outreach materials.")

        # --- TAB 4: INTERVIEW PREP ---
        with tab4:
            if st.session_state.workflow_step == 'EDITING':
                st.subheader("Role-Specific Technical Prep")
                out = st.session_state.outreach_results
                qs = out.get("interview_questions", [])
                for i, q in enumerate(qs, 1):
                    with st.container(border=True):
                        st.markdown(f"**Question {i}**")
                        st.write(q)
            else:
                st.info("Approval required to generate interview questions.")

    # Final Submit Button
    if st.session_state.workflow_step == 'EDITING':
        st.markdown("---")
        if st.button("🚀 Finalize & Submit Application", type="primary", use_container_width=True):
            job = st.session_state.selected_job
            st.session_state.applications.append({
                "title": job['metadata']['title'],
                "company": job['metadata']['company'],
                "deliverable": st.session_state.final_deliverable,
                "status": "Applied"
            })
            st.toast("Submitted successfully! 🎉")
            st.session_state.workflow_step = 'START'
            st.session_state.selected_job = None
            st.rerun()

# ------------------------------------------------------------------------------
# RIGHT COLUMN: FEATURE PANEL & CHATBOT
# ------------------------------------------------------------------------------
with side_col:
    st.subheader("🤖 AI Career Assistant")

    # Chat History
    chat_container = st.container(height=600)
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

    # Chat Input (Bottom of the right panel)
    if prompt := st.chat_input("Ask me about your CV or interview tips..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    resp = requests.post(f"{backend_url}/api/chat",
                                       json={"message": prompt, "history": st.session_state.chat_history[:-1]})
                    if resp.status_code == 200:
                        answer = resp.json().get("response", "Error.")
                        st.markdown(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    else:
                        st.error("Chat failed.")

# Application History (Footer)
if st.session_state.applications:
    st.markdown("---")
    st.subheader("📋 Application History")
    for app in st.session_state.applications:
        with st.container(border=True):
            st.markdown(f"**{app['title']}** at {app['company']} - Status: `{app['status']}`")
            with st.expander("View Submission"): st.write(app['deliverable'])
