import streamlit as st
import requests
import os
from dotenv import load_dotenv
import pdfplumber
import time

load_dotenv()

# Branding & Config
st.set_page_config(page_title="CareerBridge AI", page_icon="🚀", layout="wide")

# --- SESSION STATE ---
if 'resume_text' not in st.session_state: st.session_state.resume_text = ""
if 'temp_file_path' not in st.session_state: st.session_state.temp_file_path = None
if 'selected_job' not in st.session_state: st.session_state.selected_job = None
if 'thread_id' not in st.session_state: st.session_state.thread_id = None
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None
if 'outreach_results' not in st.session_state: st.session_state.outreach_results = None
if 'final_deliverable' not in st.session_state: st.session_state.final_deliverable = ""
if 'applications' not in st.session_state: st.session_state.applications = []
if 'edit_messages' not in st.session_state: st.session_state.edit_messages = []
if 'workflow_step' not in st.session_state: st.session_state.workflow_step = 'START'
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')

# --- HEADER ---
st.title("🚀 CareerBridge AI")
st.markdown("### Enterprise-Grade Predictive ATS & Agentic Outreach")
st.divider()

# --- MAIN LAYOUT ---
main_col, side_col = st.columns([2, 1], gap="large")

# ------------------------------------------------------------------------------
# LEFT COLUMN: THE AGENT WORKSPACE
# ------------------------------------------------------------------------------
with main_col:
    # --- INPUT PHASE ---
    if st.session_state.workflow_step == 'START':
        st.subheader("🎯 Candidate Profiling")

        input_mode = st.radio("Input Method", ["Upload PDF CV", "Tell us about yourself (Text)"], horizontal=True)

        if input_mode == "Upload PDF CV":
            uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
            if uploaded_file:
                with pdfplumber.open(uploaded_file) as pdf:
                    text = "".join([page.extract_text() or "" for page in pdf.pages])
                    st.session_state.resume_text = text
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                st.session_state.temp_file_path = temp_path
                st.success("Resume parsed successfully ✅")
        else:
            st.session_state.resume_text = st.text_area("Describe your experience, skills, and achievements:", height=200, placeholder="I am a Python developer with 5 years of experience in FastAPI...")

        st.markdown("---")
        st.subheader("🔍 Search Preferences")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            role = st.text_input("Desired Role", placeholder="e.g. Senior Python Engineer")
        with p_col2:
            location = st.selectbox("Location Preference", ["Remote", "Onsite", "Global", "Hybrid"])
        with p_col3:
            job_type = st.selectbox("Job Type", ["Full-time", "Internship", "Contract"])

        # Optional filters
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            country = st.text_input("Country (Optional)", placeholder="e.g. Germany")
        with f_col2:
            city = st.text_input("City (Optional)", placeholder="e.g. Berlin")

        if st.button("🔍 Find Matching Jobs", type="primary", use_container_width=True):
            if not st.session_state.resume_text or not role:
                st.error("Please provide both a CV/Text and a desired role.")
            else:
                with st.spinner("Querying Vector DB for best matches..."):
                    resp = requests.post(
                        f"{backend_url}/api/match_jobs",
                        json={
                            "resume_text": st.session_state.resume_text,
                            "role": role,
                            "location": location,
                            "job_type": job_type,
                            "country": country,
                            "city": city
                        }
                    )
                    if resp.status_code == 200:
                        st.session_state.matches = resp.json().get("matches", [])
                        st.session_state.workflow_step = 'MATCHED'
                        st.rerun()

    # --- JOB SELECTION PHASE ---
    elif st.session_state.workflow_step == 'MATCHED':
        st.subheader("💼 Top Matching Opportunities")
        cols = st.columns(2)
        for idx, match in enumerate(st.session_state.matches):
            with cols[idx % 2]:
                meta = match['metadata']
                with st.container(border=True):
                    st.markdown(f"**{meta['title']}**")
                    st.caption(f"{meta['company']} | {meta['location']}")
                    st.write(match['document'][:150] + "...")
                    if st.button(f"Analyze this Role", key=match['id'], use_container_width=True):
                        st.session_state.selected_job = match
                        st.session_state.workflow_step = 'ANALYZING'
                        st.rerun()
        if st.button("← Change Preferences"):
            st.session_state.workflow_step = 'START'
            st.rerun()

    # --- OBSERVABILITY PHASE ---
    elif st.session_state.workflow_step == 'ANALYZING':
        job = st.session_state.selected_job
        st.subheader(f"🧠 Digital FTE Analysis: {job['metadata']['title']}")
        with st.status("Agent is executing pipeline...", expanded=True) as status:
            st.write("🤖 Agent: Initializing analysis context...")
            time.sleep(0.5)
            st.write("🤖 Agent: Calculating Predictive ATS Match Score...")
            time.sleep(0.6)

            resp = requests.post(
                f"{backend_url}/api/analyze_full",
                json={"file_path": st.session_state.temp_file_path, "job_id": job['id']}
            )
            if resp.status_code == 200:
                st.write("🤖 Agent: Drafting optimization gaps...")
                time.sleep(0.5)
                st.session_state.analysis_results = resp.json()
                st.session_state.thread_id = resp.json().get("thread_id")
                st.session_state.workflow_step = 'VALIDATING'
                status.update(label="Analysis Complete", state="complete", expanded=False)
                st.rerun()
            else:
                st.error("Analysis failed.")
                status.update(label="Process Failed", state="error")

    # --- HITL WORKBENCH PHASE ---
    elif st.session_state.workflow_step == 'VALIDATING':
        res = st.session_state.analysis_results
        ats, opt = res.get("ats_results", {}), res.get("optimizer_results", {})
        st.subheader("🛡️ HITL Workbench: Review & Approve")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("#### Predictive ATS Scoring")
            st.metric("Composite Match Score", f"{ats.get('ats_score', 'N/A')}%", delta=ats.get("recommendation", ""))
            st.info(f"**AI Summary:** {ats.get('brief_summary', 'N/A')}")
            with st.expander("✅ Matched Skills", expanded=True):
                for s in ats.get("matched_skills", []): st.write(f"- {s}")
            with st.expander("❌ Missing Skills", expanded=True):
                for s in ats.get("missing_skills", []): st.write(f"- {s}")
        with c2:
            st.markdown("#### Optimization Strategy")
            st.write(opt.get("actionable_feedback", "No feedback."))
            with st.expander("✨ Suggested Bullet Points", expanded=True):
                for b in opt.get("suggested_bullet_points", []): st.write(f"- {b}")

        st.divider()
        if st.button("✅ Approve & Generate Outreach", type="primary", use_container_width=True):
            with st.spinner("Agent is drafting deliverables..."):
                app_resp = requests.post(f"{backend_url}/api/approve", json={"thread_id": st.session_state.thread_id})
                if app_resp.status_code == 200:
                    outreach = app_resp.json().get("outreach_results", {})
                    st.session_state.outreach_results = outreach
                    st.session_state.final_deliverable = f"COVER LETTER:\n{outreach.get('cover_letter')}\n\nEMAIL:\n{outreach.get('recruiter_email')}"
                    st.session_state.workflow_step = 'EDITING'
                    st.rerun()

    # --- FINAL EDITOR PHASE ---
    elif st.session_state.workflow_step == 'EDITING':
        st.subheader("✍️ Final Deliverables Co-Pilot")

        # Editor area (Large text box)
        final_text = st.text_area("Final Review & Polish:", value=st.session_state.final_deliverable, height=600)
        st.session_state.final_deliverable = final_text

        if st.button("🚀 Finalize & Submit", type="primary", use_container_width=True):
            job = st.session_state.selected_job
            st.session_state.applications.append({
                "title": job['metadata']['title'],
                "company": job['metadata']['company'],
                "deliverable": st.session_state.final_deliverable,
                "status": "Applied"
            })
            st.toast("Application submitted successfully! 🎉")
            st.session_state.workflow_step = 'START'
            st.session_state.selected_job = None
            st.rerun()

# --- APPLICATION HISTORY (BOTTOM) ---
if st.session_state.applications:
    st.markdown("---")
    st.subheader("📋 Application History")
    for app in st.session_state.applications:
        with st.container(border=True):
            st.markdown(f"**{app['title']}** at {app['company']} - Status: `{app['status']}`")
            with st.expander("View Submission"):
                st.write(app['deliverable'])

# ------------------------------------------------------------------------------
# RIGHT COLUMN: FEATURE PANEL & CHATBOT
# ------------------------------------------------------------------------------
with side_col:
    st.subheader("🤖 Career AI Assistant")
    st.markdown("Ask me for interview tips, CV tweaks, or career advice.")

    # Chat Interface
    chat_container = st.container(height=500)
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        if prompt := st.chat_input("How can I improve my CV?"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    resp = requests.post(
                        f"{backend_url}/api/chat",
                        json={"message": prompt, "history": st.session_state.chat_history[:-1]}
                    )
                    if resp.status_code == 200:
                        answer = resp.json().get("response", "I'm sorry, I had a glitch.")
                        st.markdown(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    else:
                        st.error("Chat service unavailable.")

    st.markdown("---")
    st.markdown("**Quick Tips:**")
    st.info("- Focus on quantifyable achievements (e.g. 'Increased revenue by 20%').")
    st.info("- Use strong action verbs like 'Architected' or 'Spearheaded'.")
    st.info("- Tailor your summary to the specific job description.")
