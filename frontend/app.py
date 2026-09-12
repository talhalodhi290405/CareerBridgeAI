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

backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')

# --- UI BRANDING ---
st.title("🚀 CareerBridge AI")
st.markdown("### Predictive ATS Analysis & Agentic Outreach Automation")
st.divider()

# --- SECTION 1: INPUTS & PREFERENCES ---
with st.container():
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("📄 Candidate Assets")
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

    with col2:
        st.subheader("🎯 Search Preferences")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            role = st.text_input("Desired Role", placeholder="e.g. Senior Python Engineer")
        with p_col2:
            location = st.selectbox("Location", ["Remote", "Onsite", "Global", "Hybrid"])
        with p_col3:
            job_type = st.selectbox("Job Type", ["Full-time", "Internship", "Contract"])

        if st.button("🔍 Find Matching Jobs", type="primary", use_container_width=True):
            if not st.session_state.resume_text or not role:
                st.error("Please upload a CV and specify a role.")
            else:
                with st.spinner("Searching for the best matches..."):
                    resp = requests.post(
                        f"{backend_url}/api/match_jobs",
                        json={"resume_text": st.session_state.resume_text, "role": role, "location": location, "job_type": job_type}
                    )
                    if resp.status_code == 200:
                        st.session_state.matches = resp.json().get("matches", [])
                        st.session_state.workflow_step = 'MATCHED'
                        st.rerun()

# --- SECTION 2: JOB SELECTION ---
if 'matches' in st.session_state and st.session_state.workflow_step == 'MATCHED':
    st.markdown("---")
    st.subheader("💼 Top Matching Opportunities")

    # Display jobs as a grid of cards
    cols = st.columns(3)
    for idx, match in enumerate(st.session_state.matches):
        with cols[idx % 3]:
            meta = match['metadata']
            with st.container(border=True):
                st.markdown(f"**{meta['title']}**")
                st.caption(f"{meta['company']} | {meta['location']}")
                st.write(match['document'][:150] + "...")
                if st.button(f"Analyze this Role", key=match['id'], use_container_width=True):
                    st.session_state.selected_job = match
                    st.session_state.workflow_step = 'ANALYZING'
                    st.rerun()

# --- SECTION 3: AGENTIC OBSERVABILITY & ATS ANALYSIS ---
if st.session_state.workflow_step == 'ANALYZING':
    st.markdown("---")
    job = st.session_state.selected_job
    st.subheader(f"🧠 Digital FTE Analysis: {job['metadata']['title']}")

    with st.status("Digital FTE is processing...", expanded=True) as status:
        st.write("🤖 Agent: Extracting technical entities from CV...")
        time.sleep(0.5)
        st.write("🤖 Agent: Querying Vector DB for role requirements...")
        time.sleep(0.6)

        resp = requests.post(
            f"{backend_url}/api/analyze_full",
            json={"file_path": st.session_state.temp_file_path, "job_id": job['id']}
        )

        if resp.status_code == 200:
            st.write("🤖 Agent: Calculating Predictive ATS Match Score...")
            time.sleep(0.5)
            st.write("🤖 Agent: Drafting optimization strategies...")
            time.sleep(0.6)
            st.session_state.analysis_results = resp.json()
            st.session_state.thread_id = resp.json().get("thread_id")
            st.session_state.workflow_step = 'VALIDATING'
            status.update(label="Analysis Complete", state="complete", expanded=False)
            st.rerun()
        else:
            st.error("Analysis failed.")
            status.update(label="Process Failed", state="error")

# --- SECTION 4: HITL WORKBENCH (ATS SCORE & EDITOR) ---
if st.session_state.workflow_step == 'VALIDATING':
    st.markdown("---")
    res = st.session_state.analysis_results
    ats, opt = res.get("ats_results", {}), res.get("optimizer_results", {})

    st.subheader("🛡️ HITL Workbench: Review & Approve")

    # Restore Predictive ATS Scoring UI
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
        with st.spinner("Generating deliverables..."):
            app_resp = requests.post(f"{backend_url}/api/approve", json={"thread_id": st.session_state.thread_id})
            if app_resp.status_code == 200:
                outreach = app_resp.json().get("outreach_results", {})
                st.session_state.outreach_results = outreach
                st.session_state.final_deliverable = f"COVER LETTER:\n{outreach.get('cover_letter')}\n\nEMAIL:\n{outreach.get('recruiter_email')}"
                st.session_state.workflow_step = 'EDITING'
                st.rerun()

# --- SECTION 5: CO-PILOT EDITOR ---
if st.session_state.workflow_step == 'EDITING':
    st.markdown("---")
    st.subheader("✍️ Co-Pilot Editor: Final Polish")

    col_chat, col_editor = st.columns([1, 2])

    with col_chat:
        st.markdown("**AI Editor**")
        for m in st.session_state.edit_messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if edit_prompt := st.chat_input("e.g. 'Make it more aggressive'"):
            st.session_state.edit_messages.append({"role": "user", "content": edit_prompt})
            with st.chat_message("user"): st.markdown(edit_prompt)
            with st.chat_message("assistant"):
                with st.spinner("Editing..."):
                    edit_resp = requests.post(
                        f"{backend_url}/api/edit_text",
                        json={"text": st.session_state.final_deliverable, "instruction": edit_prompt}
                    )
                    if edit_resp.status_code == 200:
                        st.session_state.final_deliverable = edit_resp.json().get("edited_text", "")
                        st.markdown("Text updated! Check the editor.")
                        st.session_state.edit_messages.append({"role": "assistant", "content": "Updated successfully."})
                    else:
                        st.error("Editing failed.")

    with col_editor:
        st.markdown("**Final Deliverables**")
        final_text = st.text_area("Review and edit the output:", value=st.session_state.final_deliverable, height=500)
        st.session_state.final_deliverable = final_text

        if st.button("🚀 Finalize & Submit", type="primary", use_container_width=True):
            job = st.session_state.selected_job
            st.session_state.applications.append({
                "title": job['metadata']['title'],
                "company": job['metadata']['company'],
                "deliverable": st.session_state.final_deliverable,
                "status": "Applied"
            })
            st.toast("Submitted successfully! 🎉")
            st.session_state.workflow_step = 'START'
            # Reset flow but keep history
            st.session_state.selected_job = None
            st.session_state.analysis_results = None
            st.session_state.outreach_results = None
            st.rerun()

# --- APPLICATION HISTORY ---
st.markdown("---")
if st.session_state.applications:
    st.subheader("📋 Application History")
    for app in st.session_state.applications:
        with st.container(border=True):
            st.markdown(f"**{app['title']}** at {app['company']} - Status: `{app['status']}`")
            with st.expander("View Submission"):
                st.write(app['deliverable'])
