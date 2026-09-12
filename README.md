# 🚀 CareerBridge AI — AI Career Intelligence Platform & Career Command Center

> **Autonomous Talent Triage, Profile Optimization & Live Career Command Center**

![Uploading Gemini_Generated_Image_m29qj5m29qj5m29q.jpeg…]()



---

## 🚀 Live Application & Demo

### 🌐 Live Production Application
👉 **[https://careerbridgeai.streamlit.app/](https://careerbridgeai.streamlit.app/)**

### 📹 3.5-Minute Demo Video
🎥 **[Watch Demo Video on YouTube](Link coming soon)** *(Link coming soon)*

---

## 💡 System Overview & Core Capabilities

CareerBridge AI is an enterprise-grade AI Career Intelligence Platform built to bridge the gap between job candidates and ATS algorithms. Operating as a **Digital FTE (Full-Time Equivalent)** career strategist, the platform combines deterministic document validation, RAG-powered job matching, ATS scoring, anti-hallucination profile optimization, and interactive AI career coaching.

### 🌟 Key Architectural Pillars

1. **Digital FTE Career Workflow**:
   - End-to-end automation from PDF intake, 7-stage security validation, job matching, ATS scoring, resume bullet optimization with X-Y-Z metrics, to tailored cover letter and recruiter outreach generation.

2. **7-Stage Document Validation & Security Pipeline**:
   - **File Signature Verification**: Enforces magic bytes inspection (`%PDF-`) to block extension spoofing.
   - **Strict MIME Type Whitelisting**: Accepts PDF resumes only (`application/pdf`).
   - **Maximum File Size Cap**: Restricts payload to $\le 10\text{ MB}$.
   - **Encrypted / Password Protection Guard**: Detects and rejects locked PDFs.
   - **Corrupted / Empty Buffer Detection**: Validates physical byte stream integrity.
   - **Document Type Classifier**: Distinguishes resumes from invoices, IDs, tax forms, or receipts.
   - **Extraction Quality Assessor**: Computes confidence score ($\ge 40\%$) and detects unparseable scans or missing email/skills.

3. **Human-in-the-Loop (HITL) Workbench**:
   - Transparent side-by-side Before/After optimization workbench where candidates inspect, edit, approve, or reject AI-recommended bullet enhancements and cover letters before applying.

---

## 🏗️ Decoupled Cloud Architecture

CareerBridge AI employs a decoupled microservices architecture designed for enterprise scalability, fast response times, and high availability:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           Frontend: Streamlit Web Platform                           │
│                       (Hosted on Streamlit Community Cloud)                         │
└──────────────────────────────────────────┬──────────────────────────────────────────┘
                                           │ HTTPS / REST API
┌──────────────────────────────────────────▼──────────────────────────────────────────┐
│                             Backend Engine: FastAPI Microservice                    │
│                             (Hosted on Render Cloud Infrastructure)                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ├─ 🛡️ 7-Stage Validation Pipeline  (pdfplumber / Magic Byte Signature Inspection) │
│  ├─ 📊 Deterministic ATS Engine     (Skill Overlap & Keyword Extraction)            │
│  ├─ 🎯 Anti-Hallucination Optimizer (X-Y-Z Metric Verification Guardrails)           │
│  └─ 📁 Offline Fallback Store       (demo_backup.json Fail-Safe Dataset)            │
└──────────────┬───────────────────────────┬───────────────────────────┬──────────────┘
               │                           │                           │
┌──────────────▼────────────┐ ┌────────────▼────────────┐ ┌────────────▼────────────┐
│      Groq Developer API   │ │   ChromaDB RAG Engine   │ │     Live Job Market API   │
│ (Llama 3.1 8B Instant LLM)│ │ (Vector Skill Embeddings)│ │(Adzuna, Remotive, Jobicy) │
└───────────────────────────┘ └─────────────────────────┘ └───────────────────────────┘
```

- **Frontend Tier**: Lightweight, interactive Streamlit frontend with dual light/dark SaaS theme, 10-section sidebar navigation, and real-time status indicators.
- **Backend Tier**: High-performance FastAPI ASGI microservice entrypoint (`backend/main.py`) deployed on Render infrastructure.
- **AI & RAG Tier**: Groq Llama 3.1 8B Instant model providing lightning-fast inference ($\sim 300\text{ms}$) coupled with ChromaDB vector search and deterministic Python fallback engines.
- **Resilience Tier**: Offline `demo_backup.json` fail-safe ensuring 100% operational uptime even during cloud network or API provider outages.

---

## ✨ Features & Module Directory

| Module | Description |
|--------|-------------|
| 📊 **Dashboard** | Candidate command center with profile status, prompt action chips, interactive AI Coach, career health metrics, and top job recommendations. |
| 🔍 **Find Jobs** | Live job market search engine querying Adzuna, Remotive, Jobicy, and Arbeitnow APIs with match scoring. |
| 👤 **My CV** | Interactive candidate profile editor, PDF intake uploader, and manual profile builder. |
| 📊 **ATS Scanner** | Deterministic ATS readiness calculator returning overall score, skills match %, keyword match %, experience match %, and format score. |
| ✨ **Improve CV** | HITL optimization workbench featuring side-by-side original vs. X-Y-Z metric-enhanced resume bullet points. |
| ✉️ **Cover Letter** | Customizable cover letter generator with Standard, Concise, Technical, and Formal tone styles. |
| 📁 **Applications** | Visual Kanban pipeline tracking candidate application stages (Saved → Applied → Interview → Offer → Rejected). |
| 🤖 **AI Career Coach** | Full-page context-aware career coach chatbot maintaining real-time memory of candidate profile, ATS results, and active applications. |
| 📈 **Analytics** | Application funnel metrics and interview conversion rate reporting. |
| 🚀 **Guided Golden Path** | 7-step wizard guiding candidates sequentially through intake, profile, job selection, ATS check, optimization, review, and recruiter outreach. |

---

## 🚀 How to Access & Deployment Guide

### 🌐 Direct Browser Access
No installation required! Access the live production application directly:
👉 **[https://careerbridgeai.streamlit.app/](https://careerbridgeai.streamlit.app/)**

---

## 💻 Local Setup & Developer Guide

### Prerequisites
- Python 3.10+
- Git

### 1. Clone Repository
```bash
git clone https://github.com/talhalodhi290405/CareerBridgeAI.git
cd CareerBridgeAI
```

### 2. Create & Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables (Optional)
Create `.env` in project root:
```env
GROQ_API_KEY=your_groq_api_key
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
```
*Note: If no API keys are provided, CareerBridge AI operates seamlessly using its offline fallback dataset and deterministic engines.*

### 5. Run Backend & Frontend

#### Launch Streamlit Frontend:
```bash
streamlit run frontend/app.py
```

#### Launch FastAPI Backend (Optional):
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

---

## 🧪 Testing & Verification Suite

Run automated unit and integration tests:
```bash
python -m unittest tests/test_document_validation.py
python -m unittest tests/test_skill_extraction.py
python comprehensive_audit.py
```

---

## 📄 License & Submissions

Distributed under the MIT License. Built for hackathon submission lock.
