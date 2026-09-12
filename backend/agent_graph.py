import os
import json
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# Initialize environment variables from .env file
load_dotenv()

# Initialize the blazing fast Groq Model
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    max_tokens=1024
)

# Import the prompts we wrote earlier
from backend.prompts import ATS_EVALUATION_PROMPT, RESUME_OPTIMIZER_PROMPT

class AgentState(TypedDict):
    resume_text: str
    job_description: str
    ats_results: Dict[str, Any]
    optimizer_results: Dict[str, Any]
    human_approved: bool

# --- NODE FUNCTIONS (The Real AI Agents) ---

def run_ats_agent(state: AgentState):
    print("🤖 ATS Agent: Reading resume and evaluating...")
    
    # Format the prompt with the actual resume and job description
    prompt = PromptTemplate.from_template(ATS_EVALUATION_PROMPT)
    chain = prompt | llm
    
    # Ask Groq to evaluate it
    response = chain.invoke({
        "resume_text": state["resume_text"],
        "job_description": state["job_description"]
    })
    
    # Parse the JSON response from Groq
    try:
        # Sometimes LLMs wrap JSON in markdown blocks like ```json ... ```
        clean_json = response.content.replace('```json', '').replace('```', '').strip()
        results = json.loads(clean_json)
    except Exception as e:
        print(f"Error parsing ATS JSON: {e}")
        results = {"ats_score": 0, "recommendation": "Error"}
        
    return {"ats_results": results}

def run_optimizer_agent(state: AgentState):
    print("✍️ Optimizer Agent: Writing resume improvements...")
    
    prompt = PromptTemplate.from_template(RESUME_OPTIMIZER_PROMPT)
    chain = prompt | llm
    
    response = chain.invoke({
        "ats_results": json.dumps(state.get("ats_results", {})),
        "resume_text": state["resume_text"]
    })
    
    try:
        clean_json = response.content.replace('```json', '').replace('```', '').strip()
        results = json.loads(clean_json)
    except:
        results = {"actionable_feedback": "Could not generate feedback."}
        
    return {"optimizer_results": results}

def human_validation_node(state: AgentState):
    print("⏸️ SYSTEM PAUSED: Waiting for human validation...")
    return state

# --- GRAPH ROUTING LOGIC ---
def route_after_human(state: AgentState):
    if state.get("human_approved"):
        return END
    else:
        return "run_optimizer_agent"

# --- BUILD THE GRAPH ---
workflow = StateGraph(AgentState)
workflow.add_node("ats_evaluator", run_ats_agent)
workflow.add_node("resume_optimizer", run_optimizer_agent)
workflow.add_node("human_validation", human_validation_node)

workflow.set_entry_point("ats_evaluator")
workflow.add_edge("ats_evaluator", "resume_optimizer")
workflow.add_edge("resume_optimizer", "human_validation")
workflow.add_conditional_edges("human_validation", route_after_human)

from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory, interrupt_before=["human_validation"])