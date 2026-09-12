import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="CareerBridge AI", page_icon="🚀", layout="wide")

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 'PREFERENCES'
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'outreach_results' not in st.session_state:
    st.session_state.outreach_results = None

backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')

st.title("🚀 CareerBridge AI")
st.markdown("### Agentic Candidate Matching & Outreach Automation")
st.divider()

# --- STEP 1: PREFERENCES ---
if st.session_state.step == 'PREFERENCES':
    st.subheader("🎯 Step 1: Define Your Search")

    col1, col2 = st.columns(2)
    with col1:
        role = st.text_input("Desired Role", placeholder="e.g. Senior Python Engineer")
        location = st.selectbox("Location Preference", ["Remote", "Onsite", "Global", "Hybrid"])
    with col2:
        job_type = st.selectbox("Job Type", ["Full-time", "Internship", "Contract"])
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

    if st.button("🔍 Find Matching Jobs", type="primary"):
        if not uploaded_file or not role:
            st.error("Please provide both a role and a resume.")
        else:
            with st.spinner("Analyzing resume and searching for jobs..."):
                # We need to extract text from PDF on the frontend or send the file to a temporary extract endpoint.
                # For this workflow, let's send the file to a simple extract helper or just use the backend's analyze logic.
                # Since /api/match_jobs needs resume_text, let's implement a quick extraction here using pdfplumber.
                import pdfplumber
                try:
                    with pdfplumber.open(uploaded_file) as pdf:
                        text = "".join([page.extract_text() or "" for page in pdf.pages])
                    st.session_state.resume_text = text

                    # Save file for the next step (/api/analyze_full)
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    st.session_state.temp_file_path = temp_path

                    # Call backend matching
                    resp = requests.post(
                        f"{backend_url}/api/match_jobs",
                        json={
                            "resume_text": text,
                            "role": role,
                            "location": location,
                            "job_type": job_type
                        }
                    )
                    if resp.status_code == 200:
                        st.session_state.matches = resp.json().get("matches", [])
                        st.session_state.step = 'SELECTING_JOB'
                        st.rerun()
                    else:
                        st.error("Matching failed. Please try again.")
                except Exception as e:
                    st.error(f"Error processing PDF: {e}")

# --- STEP 2: SELECTING JOB ---
elif st.session_state.step == 'SELECTING_JOB':
    st.subheader("💼 Step 2: Select the Best Match")
    st.info("We found the top 3 jobs that match your profile and preferences.")

    for match in st.session_state.matches:
        meta = match['metadata']
        with st.expander(f"{meta['title']} at {meta['company']} ({meta['location']})"):
            st.write(f"**Type:** {meta['type']}")
            st.write(f"**Description:** {match['document']}")
            if st.button(f"Apply for this role", key=match['id']):
                st.session_state.selected_job = match
                st.session_state.step = 'ANALYZING'
                st.rerun()

    if st.button("← Back to Preferences"):
        st.session_state.step = 'PREFERENCES'
        st.rerun()

# --- STEP 3: RUN AI ANALYSIS ---
elif st.session_state.step == 'ANALYZING':
    job = st.session_state.selected_job
    st.subheader(f"🧠 Step 3: AI Analysis for {job['metadata']['title']}")
    st.write(f"Applying for: **{job['metadata']['company']}**")

    if st.button("🚀 Run AI Analysis", type="primary"):
        with st.spinner("Executing LangGraph Pipeline (ATS $\rightarrow$ Optimization $\rightarrow$ HITL)..."):
            resp = requests.post(
                f"{backend_url}/api/analyze_full",
                json={
                    "file_path": st.session_state.temp_file_path,
                    "job_id": job['id']
                }
            )
            if resp.status_code == 200:
                st.session_state.analysis_results = resp.json()
                st.session_state.thread_id = resp.json().get("thread_id")
                st.session_state.step = 'VALIDATING'
                st.rerun()
            else:
                st.error("Analysis failed.")

    if st.button("← Back to Job List"):
        st.session_state.step = 'SELECTING_JOB'
        st.rerun()

# --- STEP 4: HUMAN VALIDATION ---
elif st.session_state.step == 'VALIDATING':
    res = st.session_state.analysis_results
    ats = res.get("ats_results", {})
    opt = res.get("optimizer_results", {})

    st.subheader("🛡️ Step 4: Human-in-the-Loop Validation")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("ATS Match Score", f"{ats.get('ats_score', 'N/A')}%", delta=ats.get("recommendation", ""))
        st.info(f"**Summary:** {ats.get('brief_summary', 'N/A')}")

        with st.expander("✅ Matched Skills"):
            for s in ats.get("matched_skills", []): st.write(f"- {s}")
        with st.expander("❌ Missing Skills"):
            for s in ats.get("missing_skills", []): st.write(f"- {s}")

    with col2:
        st.subheader("💡 AI Coach Advice")
        st.write(opt.get("actionable_feedback", "No feedback."))
        with st.expander("✨ Suggested Bullet Points"):
            for b in opt.get("suggested_bullet_points", []): st.write(f"- {b}")

    st.divider()
    st.warning("Do you approve this candidate for the final outreach generation?")

    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ Approve & Generate Outreach", type="primary"):
            with st.spinner("Agent is generating customized outreach..."):
                app_resp = requests.post(
                    f"{backend_url}/api/approve",
                    json={"thread_id": st.session_state.thread_id}
                )
                if app_resp.status_code == 200:
                    st.session_state.outreach_results = app_resp.json().get("outreach_results", {})
                    st.session_state.step = 'OUTREACH'
                    st.rerun()
                else:
                    st.error("Approval failed.")
    with col_no:
        if st.button("⛔ Reject"):
            st.session_state.step = 'ANALYZING'
            st.rerun()

# --- STEP 5: FINAL OUTREACH ---
elif st.session_state.step == 'OUTREACH':
    st.subheader("🎯 Step 5: Agentic Outreach Generation")
    out = st.session_state.outreach_results

    with st.expander("📄 Customized Cover Letter", expanded=True):
        st.write(out.get("cover_letter", "Not generated."))

    with st.expander("📧 Cold Recruiter Email", expanded=True):
        st.write(out.get("recruiter_email", "Not generated."))

    with st.expander("❓ Technical Interview Questions", expanded=True):
        qs = out.get("interview_questions", [])
        for i, q in enumerate(qs, 1):
            st.write(f"**Q{i}:** {q}")

    if st.button("🔄 Start Over"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
