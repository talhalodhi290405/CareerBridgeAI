import os
import json
import pdfplumber
from fastapi import FastAPI, UploadFile, File, Body
import uvicorn

# Import the AI brain and RAG engine
from backend.agent_graph import app_graph
from backend.rag_engine import rag_engine

app = FastAPI(title="CareerBridge AI API")

# Index jobs on startup
@app.on_event("startup")
async def startup_event():
    rag_engine.index_jobs()

@app.get("/")
def health_check():
    return {"status": "online", "message": "CareerBridge AI Engine is running."}

@app.post("/api/match_jobs")
async def match_jobs(payload: dict = Body(...)):
    resume_text = payload.get("resume_text", "")
    role = payload.get("role", "")
    location = payload.get("location", "")
    job_type = payload.get("job_type", "")

    # Create a rich query combining preferences and resume
    query = f"Role: {role}, Location: {location}, Type: {job_type}. Candidate Experience: {resume_text[:500]}"

    matches = rag_engine.search_jobs(query)

    return {"matches": matches}

@app.post("/api/analyze_full")
async def analyze_resume_full(payload: dict = Body(...)):
    file_path = payload.get("file_path")
    job_id = payload.get("job_id")

    if not file_path or not job_id:
        return {"error": "Missing file_path or job_id"}

    # 1. Extract text from the PDF
    resume_text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if text:
                    resume_text += text + "\n"
    except Exception as e:
        return {"error": f"Failed to read PDF: {e}"}

    # 2. Load the specific job description from jobs.json
    try:
        with open("data/jobs.json", "r") as f:
            jobs = json.load(f)
            job = next((j for j in jobs if j["id"] == job_id), None)
            if not job:
                return {"error": "Job not found"}
            job_description = job["description"]
    except Exception:
        job_description = "General Technical Role"

    # 3. Prepare the initial memory
    initial_state = {
        "resume_text": resume_text,
        "job_description": job_description,
        "human_approved": False
    }

    config = {"configurable": {"thread_id": f"session_{job_id}"}}

    # Run until HITL pause
    for event in app_graph.stream(initial_state, config=config):
        pass

    current_state = app_graph.get_state(config).values

    return {
        "ats_results": current_state.get("ats_results", {}),
        "optimizer_results": current_state.get("optimizer_results", {}),
        "status": "Human validation required",
        "thread_id": f"session_{job_id}"
    }

@app.post("/api/approve")
async def approve_candidate(payload: dict = Body(...)):
    thread_id = payload.get("thread_id")
    config = {"configurable": {"thread_id": thread_id}}

    app_graph.update_state(config, {"human_approved": True})

    for event in app_graph.stream(None, config=config):
        pass

    final_state = app_graph.get_state(config).values

    return {
        "status": "Approved",
        "outreach_results": final_state.get("outreach_results", {})
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
