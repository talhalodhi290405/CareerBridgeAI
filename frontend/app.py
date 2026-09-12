import streamlit as st
import requests
import os
from dotenv import load_dotenv
import pdfplumber
import time

load_dotenv()

st.set_page_config(page_title="CareerBridge AI | Digital FTE", page_icon="🤖", layout="wide")

# --- CUSTOM THEMING & CSS ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    .stTextArea textarea { border-radius: 12px; }
    .agent-log {
        background-color: #0F172A;
        color: #10B981;
        font-family: 'Courier New', Courier, monospace;
        padding: 15px;
        border-radius: 10px;
        height: 300px;
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.step = 'IDLE'
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
if 'applications' not in st.session_state:
    st.session_state.applications = []
if 'final_deliverable' not in st.session_state:
    st.session_state.final_deliverable = ""

backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🤖 Digital FTE")
    st.markdown("#### CareerBridge Autonomous Worker")
    st.markdown("---")
    view = st.radio(
        "Navigation",
        ["Delegation Desk", "Agentic Observability", "HITL Workbench"],
        index=0
    )
    st.markdown("---")
    st.caption("Status: 🟢 Active & Listening")

# --- VIEW 1: DELEGATION DESK ---
if view == "Delegation Desk":
    st.header("📥 Delegation Desk")
    st.markdown("Provide your intent. The Digital FTE will handle the research, matching, and drafting.")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Assets")
        uploaded_file = st.file_uploader("Upload CV (PDF)", type=["pdf"])
        if uploaded_file:
            st.success("CV Loaded ✅")

    with col2:
        st.subheader("Intent")
        intent = st.chat_input("e.g. 'Find me remote Python internships in Europe and tailor my CV for them'")

        if intent:
            if not uploaded_file:
                st.error("Please upload your CV first.")
            else:
                with st.spinner("Parsing intent and searching..."):
                    # Extract text
                    with pdfplumber.open(uploaded_file) as pdf:
                        text = "".join([page.extract_text() or "" for page in pdf.pages])
                    st.session_state.resume_text = text

                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    st.session_state.temp_file_path = temp_path

                    # Call backend match_jobs with raw prompt
                    resp = requests.post(
                        f"{backend_url}/api/match_jobs",
                        json={"prompt": intent, "resume_text": text}
                    )
                    if resp.status_code == 200:
                        st.session_state.matches = resp.json().get("matches", [])
                        st.session_state.step = 'MATCHING'
                        st.toast("Jobs matched! Head over to Observability to start the process.", icon="🚀")
                    else:
                        st.error("Matching failed.")

    if 'matches' in st.session_state:
        st.markdown("---")
        st.subheader("🎯 Suggested Roles")
        for match in st.session_state.matches:
            meta = match['metadata']
            with st.expander(f"**{meta['title']}** at {meta['company']}"):
                st.write(f"**Location:** {meta['location']} | **Type:** {meta['type']}")
                st.write(match['document'])
                if st.button(f"Delegate Analysis for this Role", key=match['id']):
                    st.session_state.selected_job = match
                    st.session_state.step = 'ANALYZING'
                    st.toast("Analysis delegated to Digital FTE ✅", icon="🤖")

# --- VIEW 2: AGENTIC OBSERVABILITY ---
elif view == "Agentic Observability":
    st.header("🔭 Agentic Observability")

    if st.session_state.step != 'ANALYZING':
        st.info("No active tasks. Head to the Delegation Desk to delegate a role.")
    else:
        job = st.session_state.selected_job
        st.subheader(f"Worker Process: {job['metadata']['title']}")

        # Real-time "Agent Thoughts" simulation
        with st.status("Digital FTE is processing...", expanded=True) as status:
            st.write("🤖 Agent: Initializing context...")
            time.sleep(0.5)
            st.write("🤖 Agent: Extracting technical entities from CV...")
            time.sleep(0.8)
            st.write("🤖 Agent: Querying Vector DB for role requirements...")
            time.sleep(0.6)

            # Actual API Call
            resp = requests.post(
                f"{backend_url}/api/analyze_full",
                json={"file_path": st.session_state.temp_file_path, "job_id": job['id']}
            )

            if resp.status_code == 200:
                st.write("🤖 Agent: Calculating ATS Match Score...")
                time.sleep(0.5)
                st.write("🤖 Agent: Drafting personalized optimization advice...")
                time.sleep(0.7)
                st.session_state.analysis_results = resp.json()
                st.session_state.thread_id = resp.json().get("thread_id")
                st.session_state.step = 'VALIDATING'
                status.update(label="Task Complete: Pending Human Review", state="complete", expanded=False)
                st.success("The Digital FTE has finished the analysis. Please review it in the HITL Workbench.")
            else:
                st.error("Agent encountered a system error during processing.")
                status.update(label="Process Failed", state="error")

# --- VIEW 3: HITL WORKBENCH ---
elif view == "HITL Workbench":
    st.header("🛠️ HITL Workbench")

    if st.session_state.step != 'VALIDATING' and st.session_state.step != 'OUTREACH':
        st.info("No deliverables ready for review. Please complete the Analysis phase first.")
    else:
        # 1. The ATS/Optimizer Review (if not yet approved)
        if st.session_state.step == 'VALIDATING':
            res = st.session_state.analysis_results
            ats, opt = res.get("ats_results", {}), res.get("optimizer_results", {})

            col1, col2 = st.columns([1, 1])
            with col1:
                st.metric("ATS Score", f"{ats.get('ats_score', 'N/A')}%", delta=ats.get("recommendation", ""))
                st.write(f"**Summary:** {ats.get('brief_summary', 'N/A')}")
                with st.expander("Matched Skills"):
                    for s in ats.get("matched_skills", []): st.write(f"- {s}")
            with col2:
                st.subheader("AI Coach Advice")
                st.write(opt.get("actionable_feedback", "N/A"))

            st.divider()
            if st.button("✅ Approve & Generate Deliverables", type="primary", use_container_width=True):
                with st.spinner("Digital FTE is drafting final documents..."):
                    app_resp = requests.post(f"{backend_url}/api/approve", json={"thread_id": st.session_state.thread_id})
                    if app_resp.status_code == 200:
                        outreach = app_resp.json().get("outreach_results", {})
                        st.session_state.outreach_results = outreach
                        # Initial deliverable text
                        st.session_state.final_deliverable = f"COVER LETTER:\n{outreach.get('cover_letter')}\n\nEMAIL:\n{outreach.get('recruiter_email')}"
                        st.session_state.step = 'OUTREACH'
                        st.rerun()

        # 2. The Co-Pilot Editor (Split Screen)
        if st.session_state.step == 'OUTREACH':
            st.subheader("✍️ Co-Pilot Editor")

            col_chat, col_editor = st.columns([1, 2])

            with col_chat:
                st.markdown("**AI Editor**")
                if "edit_messages" not in st.session_state: st.session_state.edit_messages = []

                for m in st.session_state.edit_messages:
                    with st.chat_message(m["role"]): st.markdown(m["content"])

                if edit_prompt := st.chat_input("e.g. 'Make the cover letter more aggressive'"):
                    st.session_state.edit_messages.append({"role": "user", "content": edit_prompt})
                    with st.chat_message("user"): st.markdown(edit_prompt)

                    with st.chat_message("assistant"):
                        with st.spinner("Editing..."):
                            edit_resp = requests.post(
                                f"{backend_url}/api/edit_text",
                                json={"text": st.session_state.final_deliverable, "instruction": edit_prompt}
                            )
                            if edit_resp.status_code == 200:
                                new_text = edit_resp.json().get("edited_text", "")
                                st.session_state.final_deliverable = new_text
                                st.markdown("Text updated! Check the editor on the right.")
                                st.session_state.edit_messages.append({"role": "assistant", "content": "I've updated the documents based on your request."})
                            else:
                                st.error("Editing failed.")

            with col_editor:
                st.markdown("**Final Deliverables**")
                edited_text = st.text_area(
                    "Review and manually edit the output:",
                    value=st.session_state.final_deliverable,
                    height=500
                )
                st.session_state.final_deliverable = edited_text

                if st.button("🚀 Finalize & Approve", type="primary", use_container_width=True):
                    job = st.session_state.selected_job
                    st.session_state.applications.append({
                        "title": job['metadata']['title'],
                        "company": job['metadata']['company'],
                        "deliverable": st.session_state.final_deliverable,
                        "status": "Applied"
                    })
                    st.toast("Application officially submitted! 🎉")
                    st.session_state.step = 'IDLE'
                    st.rerun()

    # Application History Tracker
    st.markdown("---")
    st.subheader("📋 Application History")
    if not st.session_state.applications:
        st.info("No applications submitted yet.")
    else:
        for app in st.session_state.applications:
            with st.container(border=True):
                st.markdown(f"**{app['title']}** at {app['company']} - Status: `{app['status']}`")
                with st.expander("View Finalized Deliverable"):
                    st.write(app['deliverable'])
