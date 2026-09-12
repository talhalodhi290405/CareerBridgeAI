import os
import json
import pdfplumber
from fastapi import FastAPI, UploadFile, File
import uvicorn

# Import the AI brain we just built
from backend.agent_graph import app_graph

app = FastAPI(title="CareerBridge AI API")

@app.get("/")
def health_check():
    return {"status": "online", "message": "CareerBridge AI Engine is running."}

@app.post("/api/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    # 1. Save the uploaded PDF temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as f:
        f.write(await file.read())
        
    # 2. Extract text from the PDF
    resume_text = ""
    try:
        with pdfplumber.open(temp_file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if text:
                    resume_text += text + "\n"
    except Exception as e:
        return {"error": f"Failed to read PDF: {e}"}
    finally:
        # Delete the temp file so we don't clutter your computer
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    # 3. Load our target Job Description from jobs.json
    try:
        with open("data/jobs.json", "r") as f:
            jobs = json.load(f)
            job_description = json.dumps(jobs[0]) # Grab the first job
    except Exception:
        job_description = "Senior Python Engineer requiring FastAPI and Docker."

    # 4. Prepare the initial memory for our AI Agents
    initial_state = {
        "resume_text": resume_text,
        "job_description": job_description,
        "human_approved": False
    }
    
    # 5. Run the AI Workflow! (Thread ID is required for LangGraph memory)
    config = {"configurable": {"thread_id": "candidate_001"}}
    
    print(f"🚀 Starting AI Analysis for {file.filename}...")
    
    # This runs the agents until it hits our Human-in-the-Loop pause
    for event in app_graph.stream(initial_state, config=config):
        for key, value in event.items():
            print(f"✅ Finished AI Agent: {key}")

    # 6. Fetch the current state (which now contains the AI's JSON answers)
    current_state = app_graph.get_state(config).values

    return {
        "filename": file.filename,
        "ats_results": current_state.get("ats_results", {}),
        "optimizer_results": current_state.get("optimizer_results", {}),
        "status": "Human validation required"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)