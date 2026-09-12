# 🚀 CareerBridge AI — Career Intelligence & Talent Triage Platform

**Autonomous Talent Triage, Profile Optimization & Live Career Command Center**

CareerBridge AI helps early-career candidates understand how well their resume matches target technology jobs, identify ATS and skill gaps, optimize their profile without inventing facts, search live global job listings, track job applications, and generate personalized cover letters and recruiter outreach.

---

## 🎯 Problem

Early-career candidates face a black-box ATS screening process. They don't know:
- How their resume scores against real job requirements
- Which skills are missing vs. which are already strong
- How to improve their resume *without fabricating credentials*
- Where to discover live matching technical opportunities
- How to manage their application pipeline and prepare for technical interviews

## 💡 Solution

CareerBridge AI provides a dual-interface career intelligence system:

1. **Guided Step-by-Step Golden-Path Wizard**:
   Resume Intake → Profile → Job Matching → ATS Scoring → Gap Analysis → AI Optimization → Human Review → Recruiter Outreach → Interview Prep

2. **Enterprise Career Command Center Dashboard**:
   A 10-section HR-Tech dashboard with live job search, application Kanban pipeline, interactive profile editor, cover letter generator, AI Career Coach chatbot, and pipeline analytics.

Every score is deterministic and explainable. Every optimization is grounded in the candidate's actual evidence. The system never fabricates skills, metrics, or experience.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **10-Section Navigation** | Dashboard, Find Jobs, My CV, ATS Scanner, Improve CV, Cover Letter, Applications, AI Coach, Analytics, Settings |
| **Live Job Search** | Provider abstraction chain: Adzuna → Remotive → Jobicy → Arbeitnow → Emergency Demo Backup |
| **PDF Resume Parsing** | pdfplumber-based extraction with structured section detection |
| **Deterministic ATS Scoring** | Reproducible scores based on skill overlap, keyword coverage, section completeness |
| **VERIFIED / INFERRED / MISSING** | Transparent skill classification — never converts missing into verified |
| **AI Profile Optimization** | LLM-powered enhancement with strict anti-hallucination guardrails |
| **X-Y-Z Guardrails** | Only uses real metrics from the resume — never invents percentages or figures |
| **Cover Letter Generator** | Tailored cover letters with Standard, Concise, Technical, and Formal tone controls |
| **Application Tracker** | Visual Kanban pipeline (Saved → Applied → Interview → Offer + Rejected) |
| **AI Career Coach Chatbot** | Interactive assistant with candidate profile, ATS, and application memory |
| **Demo Mode & Fallback** | Full golden path works offline with pre-computed results when API keys are absent |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         Streamlit App (frontend/app.py)                          │
├──────────────────────────────────────────────────────────────────────────────────┤
│ Persistent 10-Section Navigation Sidebar:                                       │
│ 1. 📊 Dashboard      2. 🔍 Find Jobs    3. 👤 My CV           4. 📊 ATS Scanner   │
│ 5. ✨ Improve CV     6. ✉️ Cover Letter 7. 📁 Applications    8. 🤖 AI Coach      │
│ 9. 📈 Analytics     10. ⚙️ Settings    [🚀 Guided Golden-Path Wizard]            │
├──────────────────────────────────────────────────────────────────────────────────┤
│ Backend Services (backend/):                                                     │
│ ├─ job_service.py   (Adzuna → Remotive → Jobicy → Arbeitnow → Demo Backup)      │
│ ├─ cover_letter.py  (Standard, Concise, Technical, Formal cover letter generator)│
│ ├─ coach.py         (Context-aware AI Career Coach Chatbot)                     │
│ ├─ storage.py       (Local session state persistence helper)                    │
│ ├─ models.py        (Pydantic schemas: CandidateProfile, JobPosting, Apps, etc.) │
│ ├─ config.py        (Centralized configuration & API key management)             │
│ ├─ llm_service.py   (Groq SDK interface with deterministic fallback)            │
│ ├─ parser.py        (pdfplumber structured resume parser)                        │
│ ├─ rag_engine.py    (Deterministic skill & keyword matching engine)             │
│ ├─ ats_engine.py    (Deterministic ATS scoring & gap classification)           │
│ ├─ optimizer.py     (Anti-hallucination profile optimizer)                       │
│ ├─ outreach.py      (Recruiter email, LinkedIn InMail & 3 technical questions)  │
│ └─ demo.py          (Offline demo dataset loader)                                │
├──────────────────────────────────────────────────────────────────────────────────┤
│ Data Layer (data/):                                                              │
│ ├─ jobs.json        (15 curated technical job listings)                          │
│ └─ demo_backup.json (Offline pre-computed backup dataset)                       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Single-process Streamlit Architecture:**
The app is intentionally deployed as a unified single-process Streamlit application. No separate FastAPI server or ChromaDB instance is required at runtime, ensuring maximum deployment reliability on Streamlit Community Cloud.

---

## 💾 Persistence Model

> **Hackathon persistence stores application state locally for the active deployment instance.**

Candidate profiles, saved jobs, application status changes, search preferences, and coach conversation history are saved locally in `data/user_session.json` to preserve state across Streamlit reruns.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend & App | Streamlit |
| PDF Parsing | pdfplumber |
| Data Models | Pydantic v2 |
| AI Inference | Groq API (Llama 3.1 8B Instant) |
| Live Job Providers | Adzuna API, Remotive API, Jobicy API, Arbeitnow API |
| Scoring Engine | Deterministic Python |
| Configuration | python-dotenv / st.secrets |

---

## 🚀 Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-org/CareerBridge-AI.git
cd CareerBridge-AI
```

### 2. Create a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables (Optional)
Create `.env` or set in `.streamlit/secrets.toml`:
```env
GROQ_API_KEY=your_actual_groq_api_key
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
```

> **Note:** The application works fully in Demo Mode without API keys. Free open APIs (Remotive, Jobicy) supply live jobs automatically if Adzuna keys are absent.

### 5. Run the application
```bash
streamlit run frontend/app.py
```

The app will open at `http://localhost:8501`.

---

## 🔐 Environment Variables & Secrets

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | No | Groq API key for LLM features. Without it, Fallback Mode activates automatically. |
| `ADZUNA_APP_ID` | No | Adzuna job search APP ID. |
| `ADZUNA_APP_KEY` | No | Adzuna job search APP KEY. |

For Streamlit Community Cloud deployment, configure `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_key_here"
ADZUNA_APP_ID = "your_id_here"
ADZUNA_APP_KEY = "your_key_here"
```

---

## ⚡ Demo Mode & Fallback Integrity

CareerBridge AI includes complete offline fallback capabilities:
- **Missing API Keys**: Activates Demo Mode automatically for LLM functions.
- **Job Providers**: Falls back gracefully across providers (Adzuna → Remotive → Jobicy → Arbeitnow → Demo Backup).
- **Data Integrity**: Static demo jobs are explicitly labeled `Source: Demo Backup`. Live jobs display their exact source badge (`Source: Remotive`, `Source: Jobicy`, `Source: Adzuna`).

---

## 🚀 Deployment (Streamlit Community Cloud)

1. Push code to GitHub repository
2. Connect repository to [share.streamlit.io](https://share.streamlit.io)
3. Set main file path: `frontend/app.py`
4. Add secrets in Streamlit App Dashboard (optional)
5. Deploy!

---

## 📄 License

MIT License — Built for hackathon demonstration.
