"""
inference.py — Baseline inference script for IT Helpdesk Triage OpenEnv.
STRICTLY COMPLIANT WITH HACKATHON LOGGING AND OPENAI CLIENT RULES.
"""

import os
import sys
import time
from openai import OpenAI
from client import ITTriageClient
from models import TriageAction

# --- MANDATORY CONFIGURATION (HARDCODED FOR ZERO-ERROR DEPLOYMENT) ---
API_BASE_URL = "https://api.openai.com/v1"
MODEL_NAME   = "gpt-4o-mini"
# HF_TOKEN is picked from Space Secrets for security
HF_TOKEN     = os.environ.get("HF_TOKEN", "") 
# Internal URL for Docker container
ENV_BASE_URL = "http://0.0.0.0:7860" 

def run_task(task_id: str):
    # Initialize Clients
    client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)
    env_client = ITTriageClient(base_url=ENV_BASE_URL)
    
    # 🚨 MANDATORY LOG: START
    print(f"[START] Evaluating Task: {task_id}")
    
    try:
        obs = env_client.reset(task_id=task_id)
        done = False
        step_count = 0
        total_reward = 0

        while not done:
            step_count += 1
            
            # Simple Agent logic for the LLM
            prompt = f"Ticket: {obs.current_ticket.subject}\nDescription: {obs.current_ticket.description}\nTriage this."
            
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # 🚨 MANDATORY LOG: STEP
            action_desc = f"Analyzing ticket {obs.current_ticket.id}"
            print(f"[STEP] {step_count}: {action_desc}")

            # Logic to submit action back to environment
            # Note: In a real run, parse LLM response to fill these fields
            action = TriageAction(
                ticket_id=obs.current_ticket.id,
                category="software",
                priority="P3",
                assigned_team="application_support"
            )
            
            result = env_client.step(action)
            obs = result.observation
            done = result.done
            total_reward += result.reward

        # 🚨 MANDATORY LOG: END
        print(f"[END] Task: {task_id} | Final Score: {total_reward:.4f}")
        
    except Exception as e:
        # Fallback to prevent silent failure
        print(f"[END] Task: {task_id} | Error: {str(e)}")

if __name__ == "__main__":
    if not HF_TOKEN:
        print("[ERROR] HF_TOKEN is missing in Space Secrets!")
        sys.exit(1)
        
    # Running all required tasks
    for tid in ["basic_triage", "priority_routing", "incident_escalation"]:
        run_task(tid)
