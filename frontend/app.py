import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="CareerBridge AI", page_icon="🚀", layout="wide")

st.title("🚀 CareerBridge AI")
st.markdown("### AI-Powered Candidate Placement & Profile Optimization")
st.divider()

col1, col2 = st.columns([1, 1.5])

# LEFT COLUMN: UPLOAD ZONE
with col1:
    st.subheader("📄 1. Upload Resume")
    uploaded_file = st.file_uploader("Drag and drop PDF here", type=["pdf"])
    
    if uploaded_file:
        st.success(f"Loaded: {uploaded_file.name}")
        analyze_button = st.button("🧠 Run AI Analysis", type="primary", use_container_width=True)

# RIGHT COLUMN: RESULTS DASHBOARD
with col2:
    st.subheader("📊 2. AI Analysis Dashboard")
    
    if uploaded_file and 'analyze_button' in locals() and analyze_button:
        with st.spinner("AI is analyzing resume and querying the LLM..."):
            
            # 1. Send the file to your FastAPI backend
            try:
                # We package the file bytes to send over HTTP
                backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = requests.post(f"{backend_url}/api/analyze", files=files)

                if response.status_code == 200:
                    data = response.json()
                    ats = data.get("ats_results", {})
                    opt = data.get("optimizer_results", {})
                    st.session_state.thread_id = data.get("thread_id")

                    # 2. Display ATS Results
                    st.metric(
                        label="ATS Match Score",
                        value=f"{ats.get('ats_score', 'N/A')}%",
                        delta=ats.get("recommendation", "")
                    )

                    st.info(f"**AI Summary:** {ats.get('brief_summary', 'N/A')}")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        with st.expander("✅ Matched Skills", expanded=True):
                            for skill in ats.get("matched_skills", []):
                                st.write(f"- {skill}")
                    with col_b:
                        with st.expander("❌ Missing Skills", expanded=True):
                            for skill in ats.get("missing_skills", []):
                                st.write(f"- {skill}")

                    st.divider()

                    # 3. Display Optimizer Results
                    st.subheader("💡 3. AI Resume Coach")
                    st.write(opt.get("actionable_feedback", "No feedback provided."))

                    with st.expander("✨ Suggested Resume Bullet Points", expanded=True):
                        for bullet in opt.get("suggested_bullet_points", []):
                            st.write(f"- {bullet}")

                    st.divider()

                    # 4. HITL Zone
                    st.subheader("🛡️ 4. Human Validation Required")
                    st.warning("The AI workflow is currently paused. Do you approve this candidate?")

                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ Approve Match", use_container_width=True):
                            with st.spinner("Generating customized outreach..."):
                                backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')
                                approx_resp = requests.post(
                                    f"{backend_url}/api/approve",
                                    json={"thread_id": st.session_state.get("thread_id")}
                                )
                                if approx_resp.status_code == 200:
                                    st.session_state.outreach_results = approx_resp.json().get("outreach_results", {})
                                    st.rerun()
                    with col_no:
                        st.button("⛔ Reject Match", use_container_width=True)

                else:
                    st.error(f"Backend Error: {response.status_code} - {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("🚨 Could not connect to the backend! Make sure FastAPI is running on port 8000.")

    # --- NEW: Agentic Outreach Display ---
    if 'outreach_results' in st.session_state and st.session_state.outreach_results:
        st.divider()
        st.subheader("🎯 5. Agentic Outreach Generation")
        results = st.session_state.outreach_results

        with st.expander("📄 Customized Cover Letter", expanded=True):
            st.write(results.get("cover_letter", "No cover letter generated."))

        with st.expander("📧 Cold Recruiter Email", expanded=True):
            st.write(results.get("recruiter_email", "No email generated."))

        with st.expander("❓ Technical Interview Questions", expanded=True):
            questions = results.get("interview_questions", [])
            if questions:
                for i, q in enumerate(questions, 1):
                    st.write(f"**Q{i}:** {q}")
            else:
                st.write("No questions generated.")


    elif not uploaded_file:
        st.info("Upload a resume on the left to see the AI dashboard.")