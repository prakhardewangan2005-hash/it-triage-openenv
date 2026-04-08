---
title: IT Helpdesk Triage & Incident Management
emoji: 🎫
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
tags:
  - openenv
  - reinforcement-learning
  - enterprise-ai
  - it-operations
license: apache-2.0
---

# 🎫 IT Helpdesk Triage & Incident Management — OpenEnv

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-brightgreen)](https://huggingface.co/openenv)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-Apache%202.0-orange)](LICENSE)

A **production-grade OpenEnv RL training environment** that simulates a real enterprise IT Service Desk. An AI agent receives incoming IT support tickets and must make triage decisions — classifying, prioritising, routing, escalating, and ultimately managing a cascading PostgreSQL database outage spanning seven simultaneous tickets.

> Built for the **Meta × Hugging Face OpenEnv AI Hackathon** — Round 1.

---

## 🌍 Environment Description & Motivation

Every enterprise runs an IT service desk. Triage quality — getting the right ticket to the right team at the right priority — directly impacts SLA compliance, business continuity, and employee productivity. Poor triage means P1 outages sitting in a P3 queue, payroll batches missing bank cut-offs, or security breaches going uninvestigated.

This environment trains AI agents on **realistic, high-stakes triage scenarios** drawn from actual enterprise incident patterns. The skills learned here transfer directly to production helpdesk automation, on-call decision support, and agentic ITSM systems.

**Why this domain is non-trivial for LLMs:**
- Tickets are ambiguous — the same symptom (slow application) can be P1 or P3 depending on business context
- Incident detection requires correlating multiple tickets across time (root-cause reasoning)
- Remediation steps must be operationally correct, ordered, and specific — not generic advice
- Noise filtering is required in the hard task (2 of 7 tickets are irrelevant to the incident)

---

## 🗂️ Tasks

Three tasks of increasing difficulty, each with its own grader weights and success criteria.

| Task ID | Difficulty | Tickets | Max Steps | Key Challenge |
|---|---|---|---|---|
| `basic_triage` | 🟢 Easy | 5 | 10 | Category + Priority + Team routing |
| `priority_routing` | 🟡 Medium | 5 | 10 | Incident detection + Escalation decisions |
| `incident_escalation` | 🔴 Hard | 7 | 15 | Cascading DB outage + Noise filtering + Remediation steps |

### 🟢 Task 1 — Basic Triage (Easy)

Five standalone IT tickets covering the most common helpdesk categories: a jammed HR printer (hardware/P3), a locked Salesforce account with a 3 PM client proposal deadline (access/P2), a 45-user Wi-Fi degradation (network/P2), a live CEO-fraud phishing attempt (security/P1), and an Excel macro broken by an overnight Office update (software/P3).

**Agent must correctly assign:** category, priority (P1–P4), and resolver team for each ticket.

**Expected difficulty:** A frontier model should score ~0.85–1.0. A weaker model will struggle with the security/P1 escalation and the access vs. software distinction.

### 🟡 Task 2 — Priority Routing (Medium)

Five high-stakes enterprise tickets arriving simultaneously: SAP ERP degrading with 1,200 employees' payroll at risk of missing a bank ACH cut-off (performance/P1), a new-hire onboarding request (access/P4), e-commerce 503 errors at $800/min revenue loss (software/P1), VPN drops affecting 15 remote engineers (network/P2), and a SIEM alert showing possible lateral movement in the customer database (security/P1).

**Agent must additionally:** detect which tickets constitute major incidents, assign correct incident IDs, and decide whether to escalate to senior management.

**Expected difficulty:** Incident detection and escalation require reasoning across multiple tickets. The new-hire ticket is a deliberate P4 noise trap — escalating it to management incurs a penalty.

### 🔴 Task 3 — Incident Escalation (Hard)

A PostgreSQL WAL-corruption event takes down `db-prod-primary` at 14:32. Seven tickets flood in over 23 minutes:
- **TKT-H001** — Primary DB completely unresponsive (WAL corruption)
- **TKT-H002** — Auth service returning 500s (depends on primary DB)
- **TKT-H003** — E-commerce checkout failing ($2,400/min revenue loss)
- **TKT-H004** — ⚠️ *Noise:* Team lunch reminder
- **TKT-H005** — Metabase dashboards frozen (exec presentation in 80 min)
- **TKT-H006** — ⚠️ *Noise:* TLS cert expiring in 7 days (planned, non-urgent)
- **TKT-H007** — Nightly exec reporting batch job failed

**Agent must:** identify the 5 incident-linked tickets, declare `INC-MAJOR-01`, filter out the 2 noise tickets, and provide specific ordered remediation steps for each P1 ticket (DB failover, auth service restart, checkout recovery).

**Expected difficulty:** Genuinely challenges frontier models. Resolution steps are NLP-scored against ground-truth runbooks — generic advice does not score well.

---

## 📐 Action Space

```python
class TriageAction(BaseModel):
    ticket_id:              str             # Exact ID of the ticket being triaged
    category:               TicketCategory  # hardware | software | network | security
                                            # access | database | performance | other
    priority:               TicketPriority  # P1 (Critical) | P2 (High)
                                            # P3 (Medium)   | P4 (Low)
    assigned_team:          AssignedTeam    # infrastructure | application_support
                                            # network_ops | security_ops
                                            # database_admin | helpdesk
    is_part_of_incident:    bool            # True when ticket is a major-incident symptom
    incident_id:            str | None      # e.g. "INC-MAJOR-01" (medium + hard tasks)
    resolution_steps:       list[str]|None  # Ordered remediation steps (hard task P1s)
    escalate_to_management: bool            # Page senior management / C-suite
```

**Priority definitions (ITIL standard):**
- `P1` — Critical: complete outage or business-stopping event, SLA 1 hour
- `P2` — High: significant degradation or multiple users impacted, SLA 4 hours
- `P3` — Medium: partial degradation, workaround available, SLA 8 hours
- `P4` — Low: cosmetic, informational, or planned work, SLA 48 hours

---

## 👁️ Observation Space

```python
class Observation(BaseModel):
    task_id:          str            # Active task identifier
    current_ticket:   Ticket | None  # Next ticket to triage (None = queue exhausted)
    queue_remaining:  int            # Tickets still waiting in queue
    processed_count:  int            # Tickets triaged so far this episode
    step_number:      int            # Current step (0-based)
    action_feedback:  str | None     # Correctness feedback on the previous action
    cumulative_score: float          # Running mean reward 0.0–1.0
    episode_done:     bool           # True when episode has ended
    active_incidents: list[str]      # Incident IDs declared so far
    hints:            list[str]      # Task-level guidance for the agent

class Ticket(BaseModel):
    id:                  str       # Unique identifier e.g. "TKT-H001"
    subject:             str       # One-line summary
    description:         str       # Full free-text from reporter
    reporter:            str       # Reporter name
    reporter_department: str       # Business department
    timestamp:           str       # ISO-8601 creation time
    affected_systems:    list[str] # Hostnames / service identifiers
    affected_users_count: int      # Number of end-users impacted
    sla_hours:           int       # SLA resolution target in hours
```

---

## 💰 Reward Function

Rewards are **dense** — computed per step across 6 independent dimensions, not just at episode end. All values are strictly bounded to `[0.0, 1.0]`. This provides a continuous learning signal suitable for policy gradient and GRPO training.

### Grader weight profiles by difficulty

| Dimension | Easy | Medium | Hard | Notes |
|---|---|---|---|---|
| Category classification | 0.40 | 0.28 | 0.20 | Exact match required |
| Priority assignment | 0.35 | 0.22 | 0.18 | Partial credit for ±1 level |
| Team routing | 0.25 | 0.18 | 0.14 | Exact match from 6 teams |
| Incident detection | — | 0.18 | 0.20 | Medium + Hard only |
| Escalation decision | — | 0.14 | 0.12 | Penalty for over-escalating P4 |
| Resolution quality | — | — | 0.16 | Hard only — NLP scored |

### Partial credit rules

**Priority:** Assigning P2 when P1 is expected scores `0.5` instead of `0.0`. This creates a learning gradient rather than a hard cliff, allowing models to learn from near-misses.

**Incident detection:** Correctly identifying `is_part_of_incident=True/False` scores `0.7`. Providing the correct `incident_id` (e.g. `INC-MAJOR-01`) on top of that scores `1.0`.

**Resolution steps (Hard only):** NLP-scored against ground-truth runbooks using a weighted combination of keyword recall (35%) and ordered step recall (65%). Agents that cover the right concepts in their own words are rewarded — exact string matching is not required.

**Escalation penalty:** Escalating a P4 low-priority ticket to senior management incurs a `-0.15` penalty, preventing reward hacking via an always-escalate strategy.

---

## 🚀 Setup & Usage Instructions

### Prerequisites

- Python 3.11+
- Docker (for containerised deployment)
- An OpenAI-compatible API key (set as `HF_TOKEN`)

### Local development

```bash
# 1. Clone the repo
git clone https://huggingface.co/spaces/hyperlinken/triage
cd triage

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
uvicorn app:app --host 0.0.0.0 --port 7860 --reload

# 4. Run the baseline inference script (separate terminal)
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="your_api_key_here"
python inference.py
```

### Docker

```bash
# Build and run locally
docker build -t it-triage-env .
docker run -p 7860:7860 \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o-mini" \
  -e HF_TOKEN="your_api_key" \
  it-triage-env

# Verify it's running
curl http://localhost:7860/health
```

### Manual curl interaction

```bash
# Reset to the hard task
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "incident_escalation"}'

# Submit a triage action for the DB ticket
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-H001",
    "category": "database",
    "priority": "P1",
    "assigned_team": "database_admin",
    "is_part_of_incident": true,
    "incident_id": "INC-MAJOR-01",
    "escalate_to_management": true,
    "resolution_steps": [
      "Promote db-prod-replica-01 to primary using SELECT pg_promote()",
      "Update all application DB_HOST configs to point to replica",
      "Do NOT restart db-prod-primary — preserve WAL for forensics",
      "Open bridge call with DBA team and follow runbook DB-DR-001"
    ]
  }'

# Check full environment state
curl http://localhost:7860/state
```

---

## 📊 Baseline Scores

Produced by running `inference.py` with `gpt-4o-mini` at `temperature=0`. Scores are deterministic and reproducible across runs.

| Task | Model | Score |
|---|---|---|
| `basic_triage` | gpt-4o-mini | **0.92** |
| `priority_routing` | gpt-4o-mini | **0.76** |
| `incident_escalation` | gpt-4o-mini | **0.58** |
| **Overall Average** | gpt-4o-mini | **0.75** |

Full reproducible results saved to `baseline_scores.json` after running `inference.py`.

---

## 🔌 API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Interactive HTML dashboard |
| `GET` | `/health` | JSON health check — `{"status": "ok", "tasks": [...]}` |
| `POST` | `/reset` | Start new episode — body: `{"task_id": "basic_triage"}` |
| `POST` | `/step` | Submit `TriageAction` → returns `StepResult(obs, reward, done, info)` |
| `GET` | `/state` | Full `EnvironmentState` snapshot with action history |
| `GET` | `/tasks` | All tasks with difficulty, ticket count, grader weights |
| `GET` | `/docs` | Interactive Swagger UI |
| `GET` | `/redoc` | ReDoc UI |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   OpenEnv Interface                      │
│  POST /reset  ──►  Observation (first ticket in queue)  │
│  POST /step   ──►  StepResult (obs + reward + done)     │
│  GET  /state  ──►  EnvironmentState (full snapshot)     │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────▼────────────────┐
         │   ITTriageEnvironment (core)   │
         │                                │
         │  Task Registry                 │
         │  ├─ basic_triage    (easy)     │
         │  ├─ priority_routing (medium)  │
         │  └─ incident_escalation (hard) │
         │                                │
         │  Dense Reward Engine           │
         │  ├─ Category score (exact)     │
         │  ├─ Priority score (partial)   │
         │  ├─ Routing score  (exact)     │
         │  ├─ Incident score (partial)   │
         │  ├─ Escalation score + penalty │
         │  └─ Resolution score (NLP)     │
         └────────────────────────────────┘
```

---

## 📦 File Structure

```
it-triage-env/
├── models.py         # Pydantic Action / Observation / State / Reward models
├── environment.py    # Core environment logic, ticket datasets, reward engine
├── app.py            # FastAPI server — OpenEnv REST endpoints
├── client.py         # Typed HTTP client for use in agents and inference
├── inference.py      # Baseline LLM inference script (uses HF_TOKEN)
├── openenv.yaml      # OpenEnv specification metadata
├── requirements.txt  # Python dependencies
├── Dockerfile        # Container definition for HF Spaces deployment
└── README.md         # This file
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `HF_TOKEN` | inference | — | API key for the LLM (OpenAI-compatible) |
| `API_BASE_URL` | inference | `https://api.openai.com/v1` | LLM API base URL |
| `MODEL_NAME` | inference | `gpt-4o-mini` | LLM model identifier |
| `ENV_BASE_URL` | inference | `http://localhost:7860` | OpenEnv server URL |
| `PORT` | optional | `7860` | Server port override |
