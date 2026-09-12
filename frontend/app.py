import streamlit as st
import requests
import os
from dotenv import load_dotenv
import pdfplumber

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
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'applications' not in st.session_state:
    st.session_state.applications = []

backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🚀 CareerBridge AI")
    st.markdown("---")
    view = st.radio(
        "Navigation",
        ["Dashboard & Analysis", "AI Career Chatbot", "Application Tracker"],
        index=0
    )
    st.markdown("---")
    st.caption("Powered by Groq & LangGraph")

# --- VIEW 1: DASHBOARD & ANALYSIS ---
if view == "Dashboard & Analysis":
    st.header("📊 Dashboard & Analysis")

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
                    try:
                        with pdfplumber.open(uploaded_file) as pdf:
                            text = "".join([page.extract_text() or "" for page in pdf.pages])
                        st.session_state.resume_text = text

                        temp_path = f"temp_{uploaded_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getvalue())
                        st.session_state.temp_file_path = temp_path

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
                            st.error("Matching failed.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    elif st.session_state.step == 'SELECTING_JOB':
        st.subheader("💼 Step 2: Select the Best Match")
        for match in st.session_state.matches:
            meta = match['metadata']
            with st.expander(f"{meta['title']} at {meta['company']} ({meta['location']})"):
                st.write(f"**Type:** {meta['type']}")
                st.write(f"**Description:** {match['document']}")
                if st.button(f"Select this Job", key=match['id']):
                    st.session_state.selected_job = match
                    st.session_state.step = 'ANALYZING'
                    st.rerun()
        if st.button("← Back to Preferences"):
            st.session_state.step = 'PREFERENCES'
            st.rerun()

    elif st.session_state.step == 'ANALYZING':
        job = st.session_state.selected_job
        st.subheader(f"🧠 Step 3: AI Analysis for {job['metadata']['title']}")
        if st.button("🚀 Run AI Analysis", type="primary"):
            with st.spinner("Executing LangGraph Pipeline..."):
                resp = requests.post(
                    f"{backend_url}/api/analyze_full",
                    json={"file_path": st.session_state.temp_file_path, "job_id": job['id']}
                )
                if resp.status_code == 200:
                    st.session_state.analysis_results = resp.json()
                    st.session_state.thread_id = resp.json().get("thread_id")
                    st.session_state.step = 'VALIDATING'
                    st.rerun()
        if st.button("← Back to Job List"):
            st.session_state.step = 'SELECTING_JOB'
            st.rerun()

    elif st.session_state.step == 'VALIDATING':
        res = st.session_state.analysis_results
        ats, opt = res.get("ats_results", {}), res.get("optimizer_results", {})
        st.subheader("🛡️ Step 4: Human Validation")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("ATS Match Score", f"{ats.get('ats_score', 'N/A')}%", delta=ats.get("recommendation", ""))
            st.info(f"**Summary:** {ats.get('brief_summary', 'N/A')}")
            with st.expander("✅ Matched Skills"):
                for s in ats.get("matched_skills", []): st.write(f"- {s}")
            with st.expander("❌ Missing Skills"):
                for s in ats.get("missing_skills", []): st.write(f"- {s}")
        with c2:
            st.subheader("💡 AI Coach Advice")
            st.write(opt.get("actionable_feedback", "No feedback."))
            with st.expander("✨ Suggested Bullet Points"):
                for b in opt.get("suggested_bullet_points", []): st.write(f"- {b}")

        st.divider()
        if st.button("✅ Approve & Generate Outreach", type="primary"):
            with st.spinner("Generating customized outreach..."):
                app_resp = requests.post(f"{backend_url}/api/approve", json={"thread_id": st.session_state.thread_id})
                if app_resp.status_code == 200:
                    outreach = app_resp.json().get("outreach_results", {})
                    st.session_state.outreach_results = outreach
                    # Add to Application Tracker
                    job = st.session_state.selected_job
                    st.session_state.applications.append({
                        "title": job['metadata']['title'],
                        "company": job['metadata']['company'],
                        "email": outreach.get("recruiter_email", "N/A"),
                        "status": "Applied"
                    })
                    st.session_state.step = 'OUTREACH'
                    st.rerun()

    elif st.session_state.step == 'OUTREACH':
        st.subheader("🎯 Step 5: Agentic Outreach Generation")
        out = st.session_state.outreach_results
        with st.expander("📄 Customized Cover Letter", expanded=True): st.write(out.get("cover_letter", "N/A"))
        with st.expander("📧 Cold Recruiter Email", expanded=True): st.write(out.get("recruiter_email", "N/A"))
        with st.expander("❓ Technical Interview Questions", expanded=True):
            for i, q in enumerate(out.get("interview_questions", []), 1): st.write(f"**Q{i}:** {q}")
        if st.button("🔄 Start Over"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

# --- VIEW 2: AI CAREER CHATBOT ---
elif view == "AI Career Chatbot":
    st.header("🤖 AI Career Chatbot")
    st.markdown("Ask me anything about your CV, interview tips, or career advice!")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("How can I improve my resume for a Senior role?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                resp = requests.post(
                    f"{backend_url}/api/chat",
                    json={"message": prompt, "history": st.session_state.messages[:-1]}
                )
                if resp.status_code == 200:
                    answer = resp.json().get("response", "I'm sorry, I encountered an error.")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("Chat failed.")

# --- VIEW 3: APPLICATION TRACKER ---
elif view == "Application Tracker":
    st.header("📋 Application Tracker")
    if not st.session_state.applications:
        st.info("No applications tracked yet. Go to Dashboard to approve a match!")
    else:
        for app in st.session_state.applications:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{app['title']}** at {app['company']}")
                    with st.expander("View Sent Email"):
                        st.write(app['email'])
                with col2:
                    st.markdown(f"**Status:** `{app['status']}`")
