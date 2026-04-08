"""
inference.py — Baseline inference script for IT Helpdesk Triage OpenEnv.

Runs an OpenAI-compatible LLM against all 3 tasks and saves reproducible scores.

Required environment variables (hackathon spec):
  API_BASE_URL   — LLM API base URL  (e.g. https://api.openai.com/v1)
  MODEL_NAME     — model identifier  (e.g. gpt-4o-mini)
  HF_TOKEN       — Hugging Face / API key used for authentication

Optional:
  ENV_BASE_URL   — OpenEnv server URL (default: http://localhost:7860)

Usage:
  export API_BASE_URL=https://api.openai.com/v1
  export MODEL_NAME=gpt-4o-mini
  export HF_TOKEN=your_api_key
  python inference.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, Optional

from openai import OpenAI

from client import ITTriageClient
from models import AssignedTeam, TicketCategory, TicketPriority, TriageAction

# ──────────────────────────────────────────────────────────────────────────────
# Configuration — hackathon-specified variable names
# ──────────────────────────────────────────────────────────────────────────────

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "gpt-4o-mini")
HF_TOKEN     = os.environ.get("HF_TOKEN",     "")        # ← hackathon spec key
ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:7860")

if not HF_TOKEN:
    print("[ERROR] HF_TOKEN is not set. Please export HF_TOKEN=<your_api_key>")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────────────────────
# Clients
# ──────────────────────────────────────────────────────────────────────────────

env_client = ITTriageClient(base_url=ENV_BASE_URL)

# OpenAI client — uses HF_TOKEN as the API key (works for any OpenAI-compatible API)
llm_client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN,
)

# ──────────────────────────────────────────────────────────────────────────────
# Prompts
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a Senior IT Service Desk Manager with 15 years of ITIL-certified experience.
Your task is to triage incoming IT support tickets by making these decisions:

1. CATEGORY   — hardware | software | network | security | access | database | performance | other
2. PRIORITY   — P1 (Critical/down) | P2 (High) | P3 (Medium) | P4 (Low/routine)
3. TEAM       — infrastructure | application_support | network_ops | security_ops | database_admin | helpdesk
4. INCIDENT   — is this ticket a symptom of a larger declared major incident?
5. ESCALATION — should senior management be paged immediately?
6. RESOLUTION — for P1 tickets in 'incident_escalation' task: ordered remediation steps.

Key rules:
- Security threats, production outages, and revenue-impacting issues are ALWAYS P1.
- New-hire requests, reminders, planned renewals = P4, no escalation.
- Provide resolution_steps ONLY for P1 tickets in the 'incident_escalation' task.
- Respond ONLY with a valid JSON object — no prose, no markdown fences.
"""

TRIAGE_TEMPLATE = """\
Triage the following IT support ticket.

=== TICKET ===
ID          : {id}
Subject     : {subject}
Description : {description}
Reporter    : {reporter} ({dept})
Systems     : {systems}
Users hit   : {users}
SLA target  : {sla} hours
Timestamp   : {ts}

=== EPISODE CONTEXT ===
Task        : {task_id}
Active incidents declared so far: {incidents}
Tickets remaining after this one: {remaining}

Respond ONLY with this JSON (no extra text):
{{
  "ticket_id"              : "{id}",
  "category"               : "<category>",
  "priority"               : "<P1|P2|P3|P4>",
  "assigned_team"          : "<team>",
  "is_part_of_incident"    : <true|false>,
  "incident_id"            : "<INC-MAJOR-01 or null>",
  "resolution_steps"       : ["step 1", "step 2"] or null,
  "escalate_to_management" : <true|false>
}}
"""


def call_llm(obs_dict: Dict[str, Any], retries: int = 3) -> TriageAction:
    """Send observation to the LLM and parse the JSON TriageAction."""
    ticket = obs_dict["current_ticket"]
    prompt = TRIAGE_TEMPLATE.format(
        id=ticket["id"],
        subject=ticket["subject"],
        description=ticket["description"],
        reporter=ticket["reporter"],
        dept=ticket["reporter_department"],
        systems=", ".join(ticket["affected_systems"]) or "N/A",
        users=ticket["affected_users_count"],
        sla=ticket["sla_hours"],
        ts=ticket["timestamp"],
        task_id=obs_dict["task_id"],
        incidents=obs_dict.get("active_incidents") or "none",
        remaining=obs_dict.get("queue_remaining", 0),
    )

    last_error: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            resp = llm_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
                timeout=60,
            )
            raw  = resp.choices[0].message.content
            data = json.loads(raw)

            # Normalise priority
            pri = str(data.get("priority", "P3")).upper().strip()
            if pri not in ("P1","P2","P3","P4"):
                pri = next((p for p in ("P1","P2","P3","P4") if p in pri), "P3")
            data["priority"]  = pri
            data["ticket_id"] = ticket["id"]

            return TriageAction(**data)

        except Exception as exc:
            last_error = exc
            print(f"    [WARN] LLM attempt {attempt}/{retries} failed: {exc}")
            time.sleep(2 ** attempt)

    print(f"    [ERROR] All {retries} attempts failed. Using safe fallback.")
    return TriageAction(
        ticket_id=ticket["id"],
        category=TicketCategory.OTHER,
        priority=TicketPriority.P3,
        assigned_team=AssignedTeam.HELPDESK,
    )


# ──────────────────────────────────────────────────────────────────────────────

def run_task(task_id: str) -> float:
    """Run one full episode and return final cumulative score."""
    BAR = 40
    print(f"\n{'='*65}\n  TASK: {task_id.upper()}\n{'='*65}")

    obs = env_client.reset(task_id=task_id)
    total = obs.queue_remaining + 1
    print(f"  Tickets : {total}")

    steps = 0
    while not obs.episode_done and obs.current_ticket is not None:
        t  = obs.current_ticket
        n  = steps + 1
        print(f"\n  +-- Step {n}/{total} -- {t.id}")
        print(f"  |   {t.subject[:70]}{'...' if len(t.subject)>70 else ''}")
        print(f"  |   SLA:{t.sla_hours}h  users:{t.affected_users_count}")

        action = call_llm(obs.model_dump())
        result = env_client.step(action)
        obs    = result.observation
        steps += 1

        filled = int(result.reward * BAR)
        bar    = "█" * filled + "░" * (BAR - filled)
        print(f"  |   [{action.category.value}] {action.priority.value} → {action.assigned_team.value}")
        print(f"  |   reward [{bar}] {result.reward:.4f}")
        if obs.action_feedback:
            print(f"  +-- {obs.action_feedback}")
        if result.done:
            break

    score = obs.cumulative_score
    print(f"\n  ─ Episode done | steps:{steps} | score:{score:.4f}")
    return score


def main() -> None:
    print("\n" + "="*65)
    print("   IT HELPDESK TRIAGE — BASELINE INFERENCE")
    print("="*65)
    print(f"  Server : {ENV_BASE_URL}")
    print(f"  Model  : {MODEL_NAME}")
    print(f"  API    : {API_BASE_URL}")

    try:
        h = env_client.health()
        print(f"  Status : {h.get('status','?').upper()}")
    except Exception as exc:
        print(f"[FATAL] Cannot reach {ENV_BASE_URL}: {exc}")
        sys.exit(1)

    tasks  = ["basic_triage", "priority_routing", "incident_escalation"]
    scores: Dict[str, float] = {}
    for tid in tasks:
        scores[tid] = run_task(tid)

    overall = sum(scores.values()) / len(scores)
    BAR_W   = 30

    print("\n" + "="*65)
    print("                    FINAL RESULTS")
    print("="*65)
    for tid, sc in scores.items():
        bar = "█" * int(sc * BAR_W) + "░" * (BAR_W - int(sc * BAR_W))
        print(f"  {tid:<28} [{bar}] {sc:.4f}")
    print("-"*65)
    print(f"  {'OVERALL':<28} {'─'*BAR_W}  {overall:.4f}")
    print("="*65)

    payload = {
        "environment":   "it-helpdesk-triage",
        "model":         MODEL_NAME,
        "api_base":      API_BASE_URL,
        "task_scores":   scores,
        "overall_score": round(overall, 4),
    }
    with open("baseline_scores.json", "w") as f:
        json.dump(payload, f, indent=2)
    print("\n  ✅ Scores saved → baseline_scores.json\n")


if __name__ == "__main__":
    main()
