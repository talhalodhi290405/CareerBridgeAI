# 🚀 CareerBridge AI

**Autonomous Talent Triage & Profile Optimization System**

CareerBridge AI helps early-career candidates understand how well their resume matches a target technology job, identify ATS and skill gaps, improve their profile without inventing facts, and generate personalized recruiter outreach and interview preparation.

---

## 🎯 Problem

Early-career candidates face a black-box ATS screening process. They don't know:
- How their resume scores against real job requirements
- Which skills are missing vs. which are already strong
- How to improve their resume *without fabricating credentials*
- How to write compelling recruiter outreach grounded in actual experience

## 💡 Solution

CareerBridge AI provides a complete, transparent pipeline:

**Resume → Profile → Job Matching → ATS Scoring → Gap Analysis → AI Optimization → Human Review → Recruiter Outreach → Interview Prep**

Every score is deterministic and explainable. Every optimization is grounded in the candidate's actual evidence. The system never fabricates skills, metrics, or experience.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **PDF Resume Parsing** | pdfplumber-based extraction with structured section detection |
| **15 Curated Job Listings** | AI/ML, Software Engineering, Data, Robotics, Internships, Remote/Onsite |
| **Deterministic ATS Scoring** | Reproducible scores based on skill overlap, keyword coverage, section completeness |
| **VERIFIED / INFERRED / MISSING** | Transparent skill classification — never converts missing into verified |
| **AI Optimization** | LLM-powered profile enhancement with strict anti-hallucination guardrails |
| **X-Y-Z Guardrails** | Only uses real metrics from the resume — never invents percentages or figures |
| **Human-in-the-Loop** | Explicit approve/reject workflow before generating outreach |
| **Recruiter Email + InMail** | Personalized outreach grounded in candidate evidence |
| **3 Technical Interview Questions** | Role-specific, not generic behavioral questions |
| **Demo Mode** | Full golden path works offline with pre-computed results |
| **Graceful Fallback** | AI failures degrade to deterministic results — never crash |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│            Streamlit (Single Process)         │
├──────────────────────────────────────────────┤
│  frontend/app.py                             │
│    ├─ Resume Intake (PDF upload / Demo)      │
│    ├─ Candidate Profile Display              │
│    ├─ Job Matching (deterministic)           │
│    ├─ ATS Analysis (deterministic + LLM)     │
│    ├─ Gap Analysis (VERIFIED/INFERRED/MISS)  │
│    ├─ Optimization (LLM with fallback)       │
│    ├─ Human Approval                         │
│    └─ Outreach & Interview Prep              │
├──────────────────────────────────────────────┤
│  backend/                                    │
│    ├─ models.py      (Pydantic schemas)      │
│    ├─ config.py      (centralized config)    │
│    ├─ llm_service.py (Groq + fallback)       │
│    ├─ parser.py      (pdfplumber)            │
│    ├─ rag_engine.py  (job matching)          │
│    ├─ ats_engine.py  (deterministic scoring) │
│    ├─ optimizer.py   (profile optimization)  │
│    ├─ outreach.py    (email/InMail/questions) │
│    ├─ demo.py        (fallback data loader)  │
│    └─ prompts.py     (LLM prompt templates)  │
├──────────────────────────────────────────────┤
│  data/                                       │
│    ├─ jobs.json          (15 curated jobs)    │
│    └─ demo_backup.json   (offline demo data) │
└──────────────────────────────────────────────┘
```

**Single-process architecture** — no separate backend server required. Deploys directly to Streamlit Community Cloud.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend & App | Streamlit |
| PDF Parsing | pdfplumber |
| Data Models | Pydantic v2 |
| AI Inference | Groq API (Llama 3.1 8B) |
| Scoring | Deterministic Python |
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

### 4. Configure environment variables
```bash
# Copy and edit .env
# Set your Groq API key (get one at https://console.groq.com/keys)
GROQ_API_KEY=your_actual_groq_api_key
```

> **Note:** The application works fully in Demo Mode without an API key. The AI key enables LLM-powered optimizations.

### 5. Run the application
```bash
streamlit run frontend/app.py
```

The app will open at `http://localhost:8501`.

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | No | Groq API key for LLM features. Without it, Demo Mode activates automatically. |
| `LLM_MODEL` | No | Override the default model (default: `llama-3.1-8b-instant`) |

For Streamlit Community Cloud, set these in `.streamlit/secrets.toml` (not committed):
```toml
GROQ_API_KEY = "your_key_here"
```

---

## ⚡ Demo Mode

CareerBridge AI includes a complete **Demo Mode** that works without any external API:

1. Click **"Load Demo Profile"** on the intake screen
2. Walk through the entire golden path with pre-computed results
3. See Alex Chen's profile optimization from **48/100 → 88/100**

Demo Mode activates automatically when:
- No API key is configured
- The Groq API is unreachable
- An LLM request times out or returns invalid data

User message: *"AI service temporarily unavailable. Demo Mode has been activated."*

---

## 🚀 Deployment (Streamlit Community Cloud)

1. Push to GitHub
2. Connect to [share.streamlit.io](https://share.streamlit.io)
3. Set main file path: `frontend/app.py`
4. Add secrets in the Streamlit dashboard:
   ```
   GROQ_API_KEY = "your_key_here"
   ```
5. Deploy

No additional servers, databases, or infrastructure required.

---

## 🎯 Golden Path Demo Instructions

1. **Open the app** → See the intake screen
2. **Click "Load Demo Profile"** → Alex Chen's profile loads
3. **Click "Find Matching Jobs"** → 5 ranked jobs appear
4. **Click "Analyze" on ML Engineer** → ATS score + gap analysis
5. **Click "Optimize Profile"** → Before/After comparison (48→88)
6. **Click "Review & Approve"** → Human approval step
7. **Click "Approve Optimization"** → Outreach generated
8. **View tabs** → Recruiter Email, InMail, 3 Interview Questions

---

## 🛡️ AI Safety & Anti-Hallucination

CareerBridge AI implements strict guardrails:

- **Deterministic scoring**: ATS scores are computed from skill overlap, keyword coverage, and section completeness — not LLM-generated numbers
- **VERIFIED/INFERRED/MISSING**: Every skill is explicitly classified based on resume evidence
- **X-Y-Z Guardrail**: Metrics in optimized bullets only appear when real numbers exist in the resume
- **No fabrication**: The system never invents skills, companies, certifications, metrics, or experience
- **Schema validation**: All LLM outputs are validated against Pydantic schemas; invalid responses trigger deterministic fallback
- **Evidence grounding**: Outreach and interview questions reference only verified candidate information

---

## 🔄 Error & Fallback Behavior

| Failure | Behavior |
|---------|----------|
| Missing API key | Demo Mode activates automatically |
| LLM timeout | Deterministic fallback used |
| Invalid LLM JSON | Pydantic validation catches; fallback used |
| Malformed PDF | User-friendly error message; no crash |
| Network failure | Graceful degradation to offline mode |
| Rate limiting | Retry with backoff; then fallback |

**No raw tracebacks are ever shown to users.**

---

## 📄 License

MIT License — Built for hackathon demonstration purposes.
