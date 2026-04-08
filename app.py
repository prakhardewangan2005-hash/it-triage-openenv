"""
app.py — IT Helpdesk Triage OpenEnv — Alternative Premium Design
Cyberpunk / terminal aesthetic with green-on-dark, scanlines, typewriter effects.
"""
from __future__ import annotations
import logging, os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from environment import ITTriageEnvironment
from models import EnvironmentState, Observation, StepResult, TriageAction

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IT Helpdesk Triage & Incident Management — OpenEnv",
    description="Production-grade OpenEnv RL environment for enterprise IT service desk simulation.",
    version="1.0.0", docs_url="/docs", redoc_url="/redoc",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
env = ITTriageEnvironment()

class ResetRequest(BaseModel):
    task_id: str = "basic_triage"

LANDING_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IT Helpdesk Triage — OpenEnv</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

:root{
  --bg:#020408;
  --surface:#040c14;
  --card:#071220;
  --border:#0d2235;
  --border2:#1a3a55;
  --cyan:#00d4ff;
  --cyan2:#00a8cc;
  --green:#00ff9d;
  --green2:#00cc7a;
  --orange:#ff6b35;
  --yellow:#ffd700;
  --red:#ff3355;
  --text:#e8f4f8;
  --muted:#4a7a94;
  --muted2:#7ab3cc;
  --mono:'Space Mono',monospace;
  --sans:'Space Grotesk',system-ui,sans-serif;
}

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);font-family:var(--sans);overflow-x:hidden;line-height:1.6}

/* GRID BACKGROUND */
body::before{
  content:'';position:fixed;inset:0;
  background-image:
    linear-gradient(rgba(0,212,255,0.03) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,212,255,0.03) 1px,transparent 1px);
  background-size:40px 40px;
  pointer-events:none;z-index:0;
}

/* SCANLINES */
body::after{
  content:'';position:fixed;inset:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.08) 2px,rgba(0,0,0,0.08) 4px);
  pointer-events:none;z-index:1;
}

/* ── NAV ── */
nav{
  position:fixed;top:0;left:0;right:0;z-index:100;
  display:flex;align-items:center;justify-content:space-between;
  padding:1rem 2.5rem;
  background:rgba(2,4,8,0.85);
  border-bottom:1px solid var(--border);
  backdrop-filter:blur(16px);
}
.nav-logo{
  font-family:var(--mono);font-size:0.85rem;font-weight:700;
  color:var(--cyan);letter-spacing:0.05em;
  display:flex;align-items:center;gap:0.75rem;
}
.nav-logo-icon{
  width:32px;height:32px;border:1px solid var(--cyan);
  border-radius:6px;display:flex;align-items:center;justify-content:center;
  font-size:1rem;color:var(--cyan);
  box-shadow:0 0 12px rgba(0,212,255,0.3);
}
.nav-links{display:flex;gap:0.5rem}
.nav-link{
  font-family:var(--mono);font-size:0.72rem;font-weight:700;
  padding:0.4rem 0.9rem;border:1px solid var(--border2);
  border-radius:5px;color:var(--muted2);text-decoration:none;
  letter-spacing:0.05em;transition:all 0.2s;
}
.nav-link:hover{border-color:var(--cyan);color:var(--cyan);box-shadow:0 0 12px rgba(0,212,255,0.2)}
.nav-link.primary{border-color:var(--cyan);color:var(--cyan);background:rgba(0,212,255,0.08)}
.nav-link.primary:hover{background:rgba(0,212,255,0.18)}

/* ── HERO ── */
.hero{
  min-height:100vh;display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  padding:8rem 2rem 6rem;text-align:center;
  position:relative;z-index:2;
}

/* corner decorations */
.corner{position:absolute;width:60px;height:60px;opacity:0.4}
.corner-tl{top:120px;left:40px;border-top:2px solid var(--cyan);border-left:2px solid var(--cyan)}
.corner-tr{top:120px;right:40px;border-top:2px solid var(--cyan);border-right:2px solid var(--cyan)}
.corner-bl{bottom:60px;left:40px;border-bottom:2px solid var(--cyan);border-left:2px solid var(--cyan)}
.corner-br{bottom:60px;right:40px;border-bottom:2px solid var(--cyan);border-right:2px solid var(--cyan)}

.sys-label{
  font-family:var(--mono);font-size:0.7rem;color:var(--cyan);
  letter-spacing:0.2em;text-transform:uppercase;
  margin-bottom:1.5rem;opacity:0.8;
  display:flex;align-items:center;justify-content:center;gap:0.75rem;
}
.sys-label::before,.sys-label::after{content:'//';opacity:0.5}

.hero h1{
  font-size:clamp(2.8rem,7vw,5.5rem);
  font-weight:700;letter-spacing:-0.03em;
  line-height:1.05;margin-bottom:1rem;
}
.hero h1 .w1{color:var(--text)}
.hero h1 .w2{
  color:var(--cyan);
  text-shadow:0 0 40px rgba(0,212,255,0.5),0 0 80px rgba(0,212,255,0.2);
}
.hero h1 .w3{color:var(--text)}
.hero h1 .w4{
  color:var(--green);
  text-shadow:0 0 40px rgba(0,255,157,0.4);
}

.hero-sub{
  font-size:1rem;color:var(--muted2);max-width:560px;
  margin:1.5rem auto 3rem;line-height:1.75;
}

/* TERMINAL PROMPT */
.prompt-bar{
  display:inline-flex;align-items:center;gap:0.5rem;
  font-family:var(--mono);font-size:0.8rem;
  background:rgba(0,212,255,0.06);
  border:1px solid var(--border2);
  border-radius:8px;padding:0.6rem 1.2rem;
  margin-bottom:2.5rem;color:var(--muted2);
}
.prompt-bar .ps{color:var(--green)}
.prompt-bar .cmd{color:var(--cyan)}
.cursor{
  display:inline-block;width:8px;height:14px;
  background:var(--cyan);margin-left:2px;
  animation:blink 1s infinite;vertical-align:middle;
}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}

.hero-btns{display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;margin-bottom:4rem}
.btn-cyber{
  font-family:var(--mono);font-size:0.8rem;font-weight:700;
  letter-spacing:0.08em;padding:0.8rem 1.8rem;
  border-radius:6px;text-decoration:none;
  transition:all 0.2s;position:relative;overflow:hidden;
}
.btn-cyber-primary{
  background:transparent;color:var(--cyan);
  border:1px solid var(--cyan);
  box-shadow:0 0 20px rgba(0,212,255,0.2),inset 0 0 20px rgba(0,212,255,0.05);
}
.btn-cyber-primary:hover{
  background:rgba(0,212,255,0.12);
  box-shadow:0 0 30px rgba(0,212,255,0.4),inset 0 0 30px rgba(0,212,255,0.1);
}
.btn-cyber-green{
  background:transparent;color:var(--green);
  border:1px solid var(--green2);
  box-shadow:0 0 20px rgba(0,255,157,0.15);
}
.btn-cyber-green:hover{
  background:rgba(0,255,157,0.1);
  box-shadow:0 0 30px rgba(0,255,157,0.35);
}
.btn-cyber-ghost{
  background:transparent;color:var(--muted2);
  border:1px solid var(--border2);
}
.btn-cyber-ghost:hover{border-color:var(--muted2);color:var(--text)}

/* ── METRICS ROW ── */
.metrics-row{
  display:grid;
  grid-template-columns:repeat(5,1fr);
  gap:1px;background:var(--border);
  border:1px solid var(--border);border-radius:12px;
  overflow:hidden;width:100%;max-width:900px;
}
.metric{background:var(--card);padding:1.5rem 1rem;text-align:center}
.metric-val{
  font-family:var(--mono);font-size:2rem;font-weight:700;
  color:var(--cyan);
  text-shadow:0 0 20px rgba(0,212,255,0.5);
  display:block;line-height:1.1;
}
.metric-label{font-size:0.7rem;color:var(--muted);margin-top:0.3rem;letter-spacing:0.05em;font-family:var(--mono)}

/* ── SECTIONS ── */
section{position:relative;z-index:2;padding:6rem 2rem}
.container{max-width:1100px;margin:0 auto}
.section-eyebrow{
  font-family:var(--mono);font-size:0.68rem;font-weight:700;
  letter-spacing:0.18em;color:var(--cyan);text-transform:uppercase;
  margin-bottom:0.75rem;
  display:flex;align-items:center;gap:0.75rem;
}
.section-eyebrow::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,var(--border2),transparent)}
h2{font-size:1.9rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:0.5rem}
.section-sub{color:var(--muted2);margin-bottom:3rem;font-size:0.95rem}

/* SECTION DIVIDER */
.divider{
  height:1px;
  background:linear-gradient(90deg,transparent,var(--border2) 30%,var(--border2) 70%,transparent);
  position:relative;z-index:2;
}

/* ── TASK PANELS ── */
.tasks-col{display:flex;flex-direction:column;gap:1.5rem}
.task-panel{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:12px;
  padding:2rem;
  display:grid;grid-template-columns:auto 1fr auto;
  gap:1.5rem;align-items:start;
  transition:border-color 0.25s,box-shadow 0.25s;
  cursor:default;
}
.task-panel:hover{border-color:var(--cyan);box-shadow:0 0 30px rgba(0,212,255,0.08)}
.task-panel.medium:hover{border-color:var(--yellow);box-shadow:0 0 30px rgba(255,215,0,0.08)}
.task-panel.hard:hover{border-color:var(--red);box-shadow:0 0 30px rgba(255,51,85,0.08)}

.task-num{
  font-family:var(--mono);font-size:2.5rem;font-weight:700;
  line-height:1;padding-top:0.2rem;
}
.easy   .task-num{color:var(--green);text-shadow:0 0 20px rgba(0,255,157,0.4)}
.medium .task-num{color:var(--yellow);text-shadow:0 0 20px rgba(255,215,0,0.4)}
.hard   .task-num{color:var(--red);text-shadow:0 0 20px rgba(255,51,85,0.4)}

.task-body h3{font-size:1.1rem;font-weight:700;margin-bottom:0.5rem}
.task-body p{font-size:0.875rem;color:var(--muted2);line-height:1.65}

.task-chips{display:flex;flex-direction:column;gap:0.5rem;min-width:120px}
.chip{
  font-family:var(--mono);font-size:0.68rem;font-weight:700;
  letter-spacing:0.05em;padding:0.35rem 0.7rem;
  border-radius:5px;text-align:center;white-space:nowrap;
}
.chip-diff.easy  {background:rgba(0,255,157,0.1);border:1px solid rgba(0,255,157,0.3);color:var(--green)}
.chip-diff.medium{background:rgba(255,215,0,0.1);border:1px solid rgba(255,215,0,0.3);color:var(--yellow)}
.chip-diff.hard  {background:rgba(255,51,85,0.1);border:1px solid rgba(255,51,85,0.3);color:var(--red)}
.chip-info{background:rgba(0,212,255,0.06);border:1px solid var(--border2);color:var(--muted2)}

/* ── REWARD ── */
.reward-section{background:var(--surface)}
.reward-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:1px;background:var(--border);
  border:1px solid var(--border);border-radius:12px;overflow:hidden;
  margin-bottom:2rem;
}
@media(max-width:768px){.reward-grid{grid-template-columns:1fr 1fr}}
.rdim{
  background:var(--card);padding:1.75rem 1.5rem;
  position:relative;overflow:hidden;
}
.rdim::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--cyan),transparent);
}
.rdim:nth-child(2)::before{background:linear-gradient(90deg,var(--green),transparent)}
.rdim:nth-child(3)::before{background:linear-gradient(90deg,var(--yellow),transparent)}
.rdim:nth-child(4)::before{background:linear-gradient(90deg,var(--cyan2),transparent)}
.rdim:nth-child(5)::before{background:linear-gradient(90deg,var(--orange),transparent)}
.rdim:nth-child(6)::before{background:linear-gradient(90deg,var(--red),transparent)}

.rdim-pct{
  font-family:var(--mono);font-size:2.2rem;font-weight:700;
  color:var(--cyan);line-height:1.1;margin-bottom:0.5rem;
}
.rdim:nth-child(2) .rdim-pct{color:var(--green)}
.rdim:nth-child(3) .rdim-pct{color:var(--yellow)}
.rdim:nth-child(4) .rdim-pct{color:var(--cyan2)}
.rdim:nth-child(5) .rdim-pct{color:var(--orange)}
.rdim:nth-child(6) .rdim-pct{color:var(--red)}

.rdim-name{font-size:0.9rem;font-weight:700;margin-bottom:0.3rem}
.rdim-sub{font-size:0.75rem;color:var(--muted);line-height:1.4}

/* ── TERMINAL ── */
.terminal-section{background:var(--bg)}
.terminal-layout{display:grid;grid-template-columns:1fr 1fr;gap:2rem}
@media(max-width:768px){.terminal-layout{grid-template-columns:1fr}}

.term{
  border-radius:10px;overflow:hidden;
  border:1px solid var(--border);
  box-shadow:0 0 40px rgba(0,212,255,0.06);
}
.term-bar{
  display:flex;align-items:center;gap:0.5rem;
  padding:0.7rem 1rem;
  background:var(--surface);
  border-bottom:1px solid var(--border);
}
.term-dots{display:flex;gap:5px}
.term-dots span{width:10px;height:10px;border-radius:50%}
.term-dots span:nth-child(1){background:#ff5f56}
.term-dots span:nth-child(2){background:#ffbd2d}
.term-dots span:nth-child(3){background:#27c93f}
.term-title{font-family:var(--mono);font-size:0.72rem;color:var(--muted);margin-left:6px}
.term-status{
  margin-left:auto;font-family:var(--mono);font-size:0.65rem;
  padding:0.15rem 0.5rem;border-radius:4px;
}
.status-ok{background:rgba(0,255,157,0.1);border:1px solid rgba(0,255,157,0.3);color:var(--green)}

.term-body{
  background:#020608;
  padding:1.25rem 1.5rem;
  font-family:var(--mono);font-size:0.78rem;
  line-height:2;overflow-x:auto;min-height:340px;
}
.p1{color:var(--green)} /* prompt */
.p2{color:var(--cyan)}  /* command */
.p3{color:var(--muted2)} /* comment */
.p4{color:var(--yellow)} /* string value */
.p5{color:var(--orange)} /* key */
.p6{color:var(--red)}    /* error/warn */
.ln{color:var(--muted);margin-right:1rem;user-select:none}

/* ── ENDPOINTS ── */
.ep-list{display:flex;flex-direction:column;gap:3px}
.ep{
  display:grid;grid-template-columns:60px 170px 1fr;
  gap:1.25rem;align-items:center;
  padding:1rem 1.25rem;
  background:var(--card);border:1px solid var(--border);
  border-radius:8px;transition:all 0.2s;
}
.ep:hover{border-color:var(--border2);background:rgba(0,212,255,0.03)}
.meth{
  font-family:var(--mono);font-size:0.68rem;font-weight:700;
  padding:0.25rem 0.5rem;border-radius:4px;text-align:center;letter-spacing:0.05em;
}
.mget {background:rgba(0,255,157,0.1);border:1px solid rgba(0,255,157,0.25);color:var(--green)}
.mpost{background:rgba(0,212,255,0.1);border:1px solid rgba(0,212,255,0.25);color:var(--cyan)}
.ep-path{font-family:var(--mono);font-size:0.88rem;color:var(--cyan)}
.ep-desc{font-size:0.82rem;color:var(--muted2)}

/* ── PIPELINE ── */
.pipeline{
  display:flex;align-items:center;gap:0;
  overflow-x:auto;padding-bottom:1rem;
}
.pipe-step{
  background:var(--card);border:1px solid var(--border);
  border-radius:10px;padding:1.5rem 1.25rem;
  text-align:center;min-width:160px;flex-shrink:0;
  transition:border-color 0.2s,box-shadow 0.2s;
}
.pipe-step:hover{border-color:var(--cyan);box-shadow:0 0 20px rgba(0,212,255,0.15)}
.pipe-icon{font-size:1.6rem;margin-bottom:0.75rem;display:block}
.pipe-step h4{font-size:0.85rem;font-weight:700;margin-bottom:0.4rem;font-family:var(--mono)}
.pipe-step p{font-size:0.75rem;color:var(--muted2);line-height:1.5}
.pipe-arrow{
  font-family:var(--mono);color:var(--border2);
  font-size:1.5rem;padding:0 0.5rem;flex-shrink:0;
}

/* ── FOOTER ── */
footer{
  z-index:2;position:relative;
  border-top:1px solid var(--border);
  padding:3rem 2rem;
  background:var(--surface);
}
.footer-inner{
  max-width:1100px;margin:0 auto;
  display:flex;justify-content:space-between;align-items:center;
  flex-wrap:wrap;gap:1rem;
}
.footer-brand{font-family:var(--mono);font-size:0.8rem;color:var(--muted2)}
.footer-brand strong{color:var(--cyan)}
.footer-links{display:flex;gap:1.5rem}
.footer-links a{font-family:var(--mono);font-size:0.75rem;color:var(--muted);text-decoration:none;transition:color 0.2s}
.footer-links a:hover{color:var(--cyan)}

/* scrollbar */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}

@media(max-width:600px){
  .metrics-row{grid-template-columns:repeat(3,1fr)}
  .task-panel{grid-template-columns:1fr;gap:1rem}
  .task-chips{flex-direction:row;flex-wrap:wrap}
  nav{padding:0.75rem 1.25rem}
  .nav-links .nav-link:not(.primary){display:none}
}
</style>
</head>
<body>

<!-- NAV -->
<nav>
  <div class="nav-logo">
    <div class="nav-logo-icon">🎫</div>
    IT_TRIAGE_ENV
  </div>
  <div class="nav-links">
    <a class="nav-link" href="/tasks">TASKS</a>
    <a class="nav-link" href="/health">HEALTH</a>
    <a class="nav-link primary" href="/docs">API_DOCS</a>
  </div>
</nav>

<!-- HERO -->
<div class="hero">
  <div class="corner corner-tl"></div>
  <div class="corner corner-tr"></div>
  <div class="corner corner-bl"></div>
  <div class="corner corner-br"></div>

  <div class="sys-label">OpenEnv Environment v1.0.0</div>

  <h1>
    <span class="w1">IT Helpdesk </span><span class="w2">Triage</span><br>
    <span class="w3">&amp; Incident </span><span class="w4">Management</span>
  </h1>

  <p class="hero-sub">
    Production-grade RL environment where AI agents triage enterprise IT tickets —
    classifying, routing, escalating, and detecting cascading major incidents
    with dense multi-dimensional reward shaping.
  </p>

  <div class="prompt-bar">
    <span class="ps">agent@openenv:~$</span>
    <span class="cmd">curl -X POST /reset -d '{"task_id":"incident_escalation"}'</span>
    <span class="cursor"></span>
  </div>

  <div class="hero-btns">
    <a class="btn-cyber btn-cyber-primary" href="/docs">▶ LAUNCH API DOCS</a>
    <a class="btn-cyber btn-cyber-green" href="/reset" onclick="event.preventDefault();fetch('/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:'basic_triage'})}).then(r=>r.json()).then(d=>alert('✅ Reset OK\nTicket: '+d.current_ticket.id+'\n'+d.current_ticket.subject))">⚡ TEST RESET LIVE</a>
    <a class="btn-cyber btn-cyber-ghost" href="/health">◉ HEALTH CHECK</a>
  </div>

  <div class="metrics-row">
    <div class="metric"><span class="metric-val">3</span><span class="metric-label">TASKS</span></div>
    <div class="metric"><span class="metric-val">17</span><span class="metric-label">TICKETS</span></div>
    <div class="metric"><span class="metric-val">6</span><span class="metric-label">REWARD DIMS</span></div>
    <div class="metric"><span class="metric-val">35</span><span class="metric-label">MAX STEPS</span></div>
    <div class="metric"><span class="metric-val">1.0</span><span class="metric-label">MAX SCORE</span></div>
  </div>
</div>

<div class="divider"></div>

<!-- TASKS -->
<section>
  <div class="container">
    <div class="section-eyebrow">Task Registry</div>
    <h2>Three Difficulty Tiers</h2>
    <p class="section-sub">Each task exposes progressively deeper reasoning requirements — from basic ITIL classification to live production crisis management.</p>

    <div class="tasks-col">

      <div class="task-panel easy">
        <div class="task-num">01</div>
        <div class="task-body">
          <h3>Basic Triage</h3>
          <p>Classify 5 standalone IT tickets: a jammed printer, a locked Salesforce account, 45-user Wi-Fi outage, a live phishing attempt, and a broken Excel macro. Agent learns to map real-world descriptions to ITIL categories and P1–P4 priorities.</p>
        </div>
        <div class="task-chips">
          <span class="chip chip-diff easy">EASY</span>
          <span class="chip chip-info">5 tickets</span>
          <span class="chip chip-info">10 steps</span>
          <span class="chip chip-info">3 grader dims</span>
        </div>
      </div>

      <div class="task-panel medium">
        <div class="task-num">02</div>
        <div class="task-body">
          <h3>Priority Routing</h3>
          <p>5 high-stakes enterprise tickets arriving simultaneously: SAP payroll degrading with bank ACH cut-off at risk (1,200 staff), e-commerce 503s at $800/min loss, VPN dropping for 15 remote engineers, and a SIEM alert showing possible lateral movement in the customer DB.</p>
        </div>
        <div class="task-chips">
          <span class="chip chip-diff medium">MEDIUM</span>
          <span class="chip chip-info">5 tickets</span>
          <span class="chip chip-info">10 steps</span>
          <span class="chip chip-info">5 grader dims</span>
        </div>
      </div>

      <div class="task-panel hard">
        <div class="task-num">03</div>
        <div class="task-body">
          <h3>Incident Escalation</h3>
          <p>PostgreSQL WAL-corruption takes down db-prod-primary at 14:32. 7 tickets flood in: auth failures, $2,400/min checkout collapse, frozen Metabase dashboards, exec report failures — plus 2 noise tickets (a cert renewal and a lunch reminder). Agent must identify the 5 linked tickets, declare INC-MAJOR-01, and provide ordered failover remediation steps for each P1.</p>
        </div>
        <div class="task-chips">
          <span class="chip chip-diff hard">HARD</span>
          <span class="chip chip-info">7 tickets</span>
          <span class="chip chip-info">15 steps</span>
          <span class="chip chip-info">6 grader dims</span>
        </div>
      </div>

    </div>
  </div>
</section>

<div class="divider"></div>

<!-- REWARD -->
<section class="reward-section">
  <div class="container">
    <div class="section-eyebrow">Reward Function</div>
    <h2>Dense. Shaped. 6 Dimensions.</h2>
    <p class="section-sub">Every step returns partial credit across independent axes — no sparse end-of-episode binary signal.</p>

    <div class="reward-grid">
      <div class="rdim">
        <div class="rdim-pct">40%</div>
        <div class="rdim-name">Category</div>
        <div class="rdim-sub">ITIL classification — hardware, software, network, security, access, database, performance, other</div>
      </div>
      <div class="rdim">
        <div class="rdim-pct">35%</div>
        <div class="rdim-name">Priority</div>
        <div class="rdim-sub">P1–P4 assignment with partial credit for ±1 level miss — agents learn from near-misses</div>
      </div>
      <div class="rdim">
        <div class="rdim-pct">25%</div>
        <div class="rdim-name">Team Routing</div>
        <div class="rdim-sub">6 specialist teams: infrastructure, app_support, network_ops, security_ops, dba, helpdesk</div>
      </div>
      <div class="rdim">
        <div class="rdim-pct">20%</div>
        <div class="rdim-name">Incident Link</div>
        <div class="rdim-sub">Medium + Hard only. Partial for correct boolean, full for correct incident ID declaration</div>
      </div>
      <div class="rdim">
        <div class="rdim-pct">14%</div>
        <div class="rdim-name">Escalation</div>
        <div class="rdim-sub">Binary escalation flag with penalty (−0.15) for over-escalating P4 low-priority tickets</div>
      </div>
      <div class="rdim">
        <div class="rdim-pct">16%</div>
        <div class="rdim-name">Remediation</div>
        <div class="rdim-sub">Hard only. NLP-scored on keyword recall (35%) + ordered step matching (65%)</div>
      </div>
    </div>
  </div>
</section>

<div class="divider"></div>

<!-- TERMINAL DEMO -->
<section class="terminal-section">
  <div class="container">
    <div class="section-eyebrow">Live Demo</div>
    <h2>See It In Action</h2>
    <p class="section-sub">Standard curl commands. Works with any HTTP client or agent framework.</p>

    <div class="terminal-layout">
      <div class="term">
        <div class="term-bar">
          <div class="term-dots"><span></span><span></span><span></span></div>
          <span class="term-title">bash — agent session</span>
        </div>
        <div class="term-body">
<span class="p3"># Step 1 — reset for hardest task</span>
<span class="p1">$</span> <span class="p2">curl</span> -X POST \
    https://hyperlinken-triage.hf.space/reset \
    -d <span class="p4">'{"task_id":"incident_escalation"}'</span>

<span class="p3"># Step 2 — triage the DB ticket</span>
<span class="p1">$</span> <span class="p2">curl</span> -X POST \
    https://hyperlinken-triage.hf.space/step \
    -d <span class="p4">'{
  "ticket_id": "TKT-H001",
  "category":  "database",
  "priority":  "P1",
  "assigned_team": "database_admin",
  "is_part_of_incident": true,
  "incident_id": "INC-MAJOR-01",
  "escalate_to_management": true,
  "resolution_steps": [
    "Promote db-prod-replica-01 using pg_promote()",
    "Update all app DB_HOST configs",
    "Open bridge call with DBA team"
  ]
}'</span>

<span class="p3"># Step 3 — check accumulated score</span>
<span class="p1">$</span> <span class="p2">curl</span> https://hyperlinken-triage.hf.space/state
        </div>
      </div>

      <div class="term">
        <div class="term-bar">
          <div class="term-dots"><span></span><span></span><span></span></div>
          <span class="term-title">response — POST /step</span>
          <span class="term-status status-ok">200 OK</span>
        </div>
        <div class="term-body">
{
  <span class="p5">"observation"</span>: {
    <span class="p5">"task_id"</span>: <span class="p4">"incident_escalation"</span>,
    <span class="p5">"current_ticket"</span>: {
      <span class="p5">"id"</span>:      <span class="p4">"TKT-H002"</span>,
      <span class="p5">"subject"</span>: <span class="p4">"Auth service 500s — all logins failing"</span>,
      <span class="p5">"sla_hours"</span>: <span class="p4">1</span>
    },
    <span class="p5">"queue_remaining"</span>:  <span class="p4">5</span>,
    <span class="p5">"cumulative_score"</span>: <span class="p4">0.9800</span>,
    <span class="p5">"active_incidents"</span>: [<span class="p4">"INC-MAJOR-01"</span>],
    <span class="p5">"action_feedback"</span>:  <span class="p4">"category=correct(database)
  priority=correct(P1)
  team=correct(database_admin)
  incident=correct(INC-MAJOR-01)
  escalation=correct
  reward=0.980"</span>
  },
  <span class="p5">"reward"</span>: <span class="p4">0.9800</span>,
  <span class="p5">"done"</span>:   <span class="p6">false</span>,
  <span class="p5">"info"</span>: {
    <span class="p5">"reward_breakdown"</span>: {
      <span class="p5">"category_score"</span>:   <span class="p4">1.0</span>,
      <span class="p5">"priority_score"</span>:   <span class="p4">1.0</span>,
      <span class="p5">"routing_score"</span>:    <span class="p4">1.0</span>,
      <span class="p5">"incident_score"</span>:   <span class="p4">1.0</span>,
      <span class="p5">"resolution_score"</span>: <span class="p4">0.88</span>
    }
  }
}
        </div>
      </div>
    </div>
  </div>
</section>

<div class="divider"></div>

<!-- ENDPOINTS -->
<section>
  <div class="container">
    <div class="section-eyebrow">API Reference</div>
    <h2>OpenEnv Spec Endpoints</h2>
    <p class="section-sub">Typed Pydantic models. Full Swagger docs at <code style="color:var(--cyan)">/docs</code>.</p>

    <div class="ep-list">
      <div class="ep"><span class="meth mget">GET</span><span class="ep-path">/health</span><span class="ep-desc">JSON health check — automated validation gate, returns 200 + task metadata</span></div>
      <div class="ep"><span class="meth mpost">POST</span><span class="ep-path">/reset</span><span class="ep-desc">Start new episode — body: <code>{"task_id": "basic_triage"}</code> — returns typed <code>Observation</code></span></div>
      <div class="ep"><span class="meth mpost">POST</span><span class="ep-path">/step</span><span class="ep-desc">Submit <code>TriageAction</code> — returns <code>(Observation, reward∈[0,1], done, info{reward_breakdown})</code></span></div>
      <div class="ep"><span class="meth mget">GET</span><span class="ep-path">/state</span><span class="ep-desc">Full <code>EnvironmentState</code> — action history, reward history, declared incidents, episode progress</span></div>
      <div class="ep"><span class="meth mget">GET</span><span class="ep-path">/tasks</span><span class="ep-desc">All 3 tasks with difficulty, ticket count, max_steps, and per-dimension grader weights</span></div>
      <div class="ep"><span class="meth mget">GET</span><span class="ep-path">/docs</span><span class="ep-desc">Interactive Swagger UI — try every endpoint live with real payloads in browser</span></div>
    </div>
  </div>
</section>

<div class="divider"></div>

<!-- PIPELINE -->
<section style="background:var(--surface)">
  <div class="container">
    <div class="section-eyebrow">RL Loop</div>
    <h2>The Agent Pipeline</h2>
    <p class="section-sub">Compatible with TRL GRPO, SkyRL, Unsloth, and any OpenAI-client-based agent.</p>

    <div class="pipeline">
      <div class="pipe-step">
        <span class="pipe-icon">🔄</span>
        <h4>POST /reset</h4>
        <p>Choose task_id, get first Observation</p>
      </div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step">
        <span class="pipe-icon">📄</span>
        <h4>Read Ticket</h4>
        <p>Subject, description, systems, SLA, dept</p>
      </div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step">
        <span class="pipe-icon">🤖</span>
        <h4>LLM Decides</h4>
        <p>Category, priority, team, incident, steps</p>
      </div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step">
        <span class="pipe-icon">⚡</span>
        <h4>POST /step</h4>
        <p>Submit TriageAction JSON</p>
      </div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step">
        <span class="pipe-icon">📊</span>
        <h4>Reward Signal</h4>
        <p>Dense [0–1] across 6 dims</p>
      </div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step">
        <span class="pipe-icon">🔁</span>
        <h4>Repeat</h4>
        <p>Until queue empty or max_steps</p>
      </div>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div class="footer-inner">
    <div class="footer-brand">
      <strong>IT_TRIAGE_ENV</strong> &nbsp;//&nbsp; v1.0.0 &nbsp;//&nbsp;
      Meta × Hugging Face AI Hackathon
    </div>
    <div class="footer-links">
      <a href="/docs">SWAGGER</a>
      <a href="/redoc">REDOC</a>
      <a href="/health">HEALTH</a>
      <a href="/tasks">TASKS</a>
    </div>
  </div>
</footer>

</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing():
    return HTMLResponse(content=LANDING_HTML)

@app.get("/health", summary="Health check")
def health_check():
    return {"status": "ok", "environment": "IT Helpdesk Triage & Incident Management", "version": "1.0.0", "tasks": env.list_tasks()}

@app.post("/reset", response_model=Observation, summary="Reset environment")
def reset(request: ResetRequest):
    try:
        obs = env.reset(task_id=request.task_id)
        logger.info("Episode reset | task=%s", request.task_id)
        return obs
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/step", response_model=StepResult, summary="Execute triage action")
def step(action: TriageAction):
    try:
        result = env.step(action)
        logger.info("Step %d | ticket=%s | reward=%.4f | done=%s", result.observation.step_number, action.ticket_id, result.reward, result.done)
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/state", response_model=EnvironmentState, summary="Get environment state")
def state():
    return env.state()

@app.get("/tasks", summary="List available tasks")
def list_tasks():
    return env.list_tasks()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False, log_level="info")
