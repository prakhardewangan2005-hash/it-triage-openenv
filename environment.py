"""
environment.py
Core RL environment: IT Helpdesk Triage & Incident Management.

Three tasks of increasing difficulty:
  easy   – basic_triage          (5 tickets, category/priority/team)
  medium – priority_routing      (5 tickets, incident detection + escalation)
  hard   – incident_escalation   (7 tickets, cascading DB outage + noise + remediation)

Reward function is dense, partial-credit, strictly bounded [0.0, 1.0].
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from models import (
    AssignedTeam,
    EnvironmentState,
    Observation,
    RewardBreakdown,
    StepResult,
    Ticket,
    TicketCategory,
    TicketPriority,
    TriageAction,
)

# ──────────────────────────────────────────────────────────────────────────────
# Ground-Truth Ticket Datasets
# ──────────────────────────────────────────────────────────────────────────────

TASK_EASY_TICKETS: List[Dict] = [
    {
        "ticket": Ticket(
            id="TKT-E001",
            subject="Printer not working in HR office",
            description=(
                "The HP LaserJet printer on Floor 2 (HR department) has stopped printing. "
                "Documents sent to the print queue just sit there indefinitely. "
                "The printer displays a solid green light suggesting it's powered on. "
                "Last used successfully yesterday at 4:00 PM."
            ),
            reporter="Sarah Chen",
            reporter_department="Human Resources",
            timestamp="2024-03-15T09:15:00Z",
            affected_systems=["printer-hr-floor2"],
            affected_users_count=8,
            sla_hours=8,
        ),
        "ground_truth": {
            "category":              TicketCategory.HARDWARE,
            "priority":              TicketPriority.P3,
            "assigned_team":         AssignedTeam.HELPDESK,
            "is_part_of_incident":   False,
            "escalate_to_management": False,
        },
    },
    {
        "ticket": Ticket(
            id="TKT-E002",
            subject="Cannot log into Salesforce CRM — account locked",
            description=(
                "Getting 'Invalid Credentials' when logging into Salesforce CRM. "
                "Self-service password reset did not help. Account is likely locked after "
                "repeated failed attempts. I need access today to prepare a client proposal "
                "due at 3 PM."
            ),
            reporter="Mike Torres",
            reporter_department="Sales",
            timestamp="2024-03-15T09:22:00Z",
            affected_systems=["salesforce-crm"],
            affected_users_count=1,
            sla_hours=4,
        ),
        "ground_truth": {
            "category":              TicketCategory.ACCESS,
            "priority":              TicketPriority.P2,
            "assigned_team":         AssignedTeam.APPLICATION_SUPPORT,
            "is_part_of_incident":   False,
            "escalate_to_management": False,
        },
    },
    {
        "ticket": Ticket(
            id="TKT-E003",
            subject="Office Wi-Fi extremely slow since 8 AM",
            description=(
                "Wireless internet in the main office building has been extremely slow since "
                "8:00 AM. Web pages take 30+ seconds to load and video calls are dropping. "
                "Wired ethernet connections appear unaffected. "
                "Approximately 45 employees on this floor are impacted."
            ),
            reporter="Jennifer Park",
            reporter_department="Operations",
            timestamp="2024-03-15T09:45:00Z",
            affected_systems=["wifi-ap-main-01", "wifi-ap-main-02", "wifi-controller"],
            affected_users_count=45,
            sla_hours=4,
        ),
        "ground_truth": {
            "category":              TicketCategory.NETWORK,
            "priority":              TicketPriority.P2,
            "assigned_team":         AssignedTeam.NETWORK_OPS,
            "is_part_of_incident":   False,
            "escalate_to_management": False,
        },
    },
    {
        "ticket": Ticket(
            id="TKT-E004",
            subject="Suspicious phishing email received — possible CEO fraud",
            description=(
                "I received an email purporting to be from our CEO requesting an urgent wire "
                "transfer. The sender domain is 'company-corp.com' rather than 'company.com'. "
                "There is a ZIP attachment labelled 'Invoice_Urgent.zip'. "
                "I have NOT opened the attachment. Forwarding for security review."
            ),
            reporter="David Kim",
            reporter_department="Finance",
            timestamp="2024-03-15T10:05:00Z",
            affected_systems=["email-gateway", "workstation-fin-015"],
            affected_users_count=1,
            sla_hours=1,
        ),
        "ground_truth": {
            "category":              TicketCategory.SECURITY,
            "priority":              TicketPriority.P1,
            "assigned_team":         AssignedTeam.SECURITY_OPS,
            "is_part_of_incident":   False,
            "escalate_to_management": True,
        },
    },
    {
        "ticket": Ticket(
            id="TKT-E005",
            subject="Excel VBA macro broken after overnight Office update",
            description=(
                "Since the automatic Microsoft Office update pushed last night, "
                "the month-end reporting macro in 'Budget_FY2024.xlsm' throws: "
                "'Compile Error: Sub or Function not defined'. "
                "This macro generates our monthly financial summary for the CFO review."
            ),
            reporter="Lisa Wang",
            reporter_department="Finance",
            timestamp="2024-03-15T10:30:00Z",
            affected_systems=["workstation-fin-007", "ms-office-suite"],
            affected_users_count=3,
            sla_hours=8,
        ),
        "ground_truth": {
            "category":              TicketCategory.SOFTWARE,
            "priority":              TicketPriority.P3,
            "assigned_team":         AssignedTeam.APPLICATION_SUPPORT,
            "is_part_of_incident":   False,
            "escalate_to_management": False,
        },
    },
]

TASK_MEDIUM_TICKETS: List[Dict] = [
    {
        "ticket": Ticket(
            id="TKT-M001",
            subject="SAP ERP critically slow — payroll batch delayed, bank cut-off at risk",
            description=(
                "SAP ERP has been progressively degrading for 3 hours. "
                "Payroll batch processing (normally 45 min) is now at 3 hours and still running. "
                "Users report 60-90 s response times on basic queries. "
                "Payroll MUST complete by 5 PM today or we miss the bank's ACH cut-off, "
                "meaning 1,200 employees will not be paid on time."
            ),
            reporter="Robert Martinez",
            reporter_department="Payroll",
            timestamp="2024-03-29T11:00:00Z",
            affected_systems=["sap-erp-prod", "db-sap-primary", "sap-app-server-01", "sap-app-server-02"],
            affected_users_count=1200,
            sla_hours=2,
        ),
        "ground_truth": {
            "category":              TicketCategory.PERFORMANCE,
            "priority":              TicketPriority.P1,
            "assigned_team":         AssignedTeam.DATABASE_ADMIN,
            "is_part_of_incident":   True,
            "incident_id":           "INC-001",
            "escalate_to_management": True,
        },
    },
    {
        "ticket": Ticket(
            id="TKT-M002",
            subject="New employee standard software setup required by Monday",
            description=(
                "New hire John Smith (EMP-4521) starts in Marketing on Monday. "
                "Requires: Adobe Creative Suite, Slack, Salesforce CRM access, "
                "Office 365 E3 license, and standard security onboarding."
            ),
            reporter="Amanda Foster",
            reporter_department="Human Resources",
            timestamp="2024-03-29T11:15:00Z",
            affected_systems=["workstation-mkt-new-01"],
            affected_users_count=1,
            sla_hours=48,
        ),
        "ground_truth": {
            "category":              TicketCategory.ACCESS,
            "priority":              TicketPriority.P4,
            "assigned_team":         AssignedTeam.HELPDESK,
            "is_part_of_incident":   False,
            "escalate_to_management": False,
        },
    },
    {
        "ticket": Ticket(
            id="TKT-M003",
            subject="Production e-commerce site intermittently returning 503 errors",
            description=(
                "Our public-facing store is returning HTTP 503 to ~15% of visitors "
                "per the monitoring dashboard. Load-balancer logs show 'web-prod-03' "
                "repeatedly failing health checks and being removed from rotation, "
                "then recovering — pattern repeating every ~8 minutes. "
                "Revenue impact: approximately $800/min during degradation windows."
            ),
            reporter="Carlos Reyes",
            reporter_department="Engineering",
            timestamp="2024-03-29T11:30:00Z",
            affected_systems=["web-prod-03", "load-balancer-prod", "ecommerce-app"],
            affected_users_count=600,
            sla_hours=1,
        ),
        "ground_truth": {
            "category":              TicketCategory.SOFTWARE,
            "priority":              TicketPriority.P1,
            "assigned_team":         AssignedTeam.APPLICATION_SUPPORT,
            "is_part_of_incident":   True,
            "incident_id":           "INC-002",
            "escalate_to_management": True,
        },
    },
    {
        "ticket": Ticket(
            id="TKT-M004",
            subject="VPN drops every 20-30 min after auto-update to v5.8.2",
            description=(
                "My VPN disconnects every 20-30 minutes since the Cisco AnyConnect client "
                "auto-updated to 5.8.2 two days ago. Reconnecting causes loss of unsaved work. "
                "I've confirmed with 14 other remote engineers on my team — same version, "
                "same symptom. Rolling back to 5.8.1 fixes the issue but update pushes again."
            ),
            reporter="Emily Zhang",
            reporter_department="Engineering",
            timestamp="2024-03-29T12:00:00Z",
            affected_systems=["vpn-client-anyconnect", "vpn-gateway-01"],
            affected_users_count=15,
            sla_hours=4,
        ),
        "ground_truth": {
            "category":              TicketCategory.NETWORK,
            "priority":              TicketPriority.P2,
            "assigned_team":         AssignedTeam.NETWORK_OPS,
            "is_part_of_incident":   False,
            "escalate_to_management": False,
        },
    },
    {
        "ticket": Ticket(
            id="TKT-M005",
            subject="47 failed DB login attempts from foreign IP + anomalous internal service account",
            description=(
                "Security SIEM alert (HIGH): 47 failed login attempts on 'db-customer-prod' "
                "from 185.234.219.x (Eastern Europe, flagged TOR exit node) between 23:45-00:15. "
                "No successful external logins. However, the internal service account 'svc_reporting' "
                "ran an unusual bulk SELECT on PII tables at 23:40 — 5 minutes BEFORE the brute-force. "
                "Possible lateral movement. Full SIEM logs attached."
            ),
            reporter="Security SIEM (Automated Alert)",
            reporter_department="IT Security",
            timestamp="2024-03-29T00:30:00Z",
            affected_systems=["db-customer-prod", "svc_reporting", "auth-service"],
            affected_users_count=0,
            sla_hours=1,
        ),
        "ground_truth": {
            "category":              TicketCategory.SECURITY,
            "priority":              TicketPriority.P1,
            "assigned_team":         AssignedTeam.SECURITY_OPS,
            "is_part_of_incident":   True,
            "incident_id":           "INC-003",
            "escalate_to_management": True,
        },
    },
]

TASK_HARD_TICKETS: List[Dict] = [
    {
        "ticket": Ticket(
            id="TKT-H001",
            subject="CRITICAL: Primary PostgreSQL server completely unresponsive",
            description=(
                "db-prod-primary (PostgreSQL 14.8) is completely unresponsive since 14:32. "
                "All TCP connections to port 5432 time out after 30 s. "
                "pg_log tail: 'FATAL: could not open file pg_wal/00000001000000000000003F: "
                "No such file or directory' — indicates WAL segment corruption or deletion. "
                "Streaming replica db-prod-replica-01 is live and ~0 lag but NOT promoted. "
                "Last clean backup: 14:20 (12 min ago)."
            ),
            reporter="AlertManager (Automated)",
            reporter_department="Infrastructure Monitoring",
            timestamp="2024-03-29T14:33:00Z",
            affected_systems=["db-prod-primary", "pg-wal-storage"],
            affected_users_count=200,
            sla_hours=1,
        ),
        "ground_truth": {
            "category":              TicketCategory.DATABASE,
            "priority":              TicketPriority.P1,
            "assigned_team":         AssignedTeam.DATABASE_ADMIN,
            "is_part_of_incident":   True,
            "incident_id":           "INC-MAJOR-01",
            "escalate_to_management": True,
            "resolution_steps": [
                "Promote db-prod-replica-01 to primary immediately using SELECT pg_promote()",
                "Update all application DB_HOST configs to point to db-prod-replica-01",
                "Do NOT restart or touch db-prod-primary — preserve WAL for forensics",
                "Notify all dependent application teams of failover in progress",
                "Open bridge call with DBA team and follow runbook DB-DR-001",
                "Trigger post-incident review within 24 h",
            ],
        },
    },
    {
        "ticket": Ticket(
            id="TKT-H002",
            subject="Authentication service returning HTTP 500 — all logins failing",
            description=(
                "auth-service-prod returning 500 Internal Server Error for 100% of login "
                "attempts since 14:35. Application logs: "
                "'psycopg2.OperationalError: could not connect to server: Connection refused. "
                "Is the server running on host db-prod-primary (port 5432)?' "
                "All user sessions are invalidated; nobody can log in to any internal app."
            ),
            reporter="Carlos Reyes",
            reporter_department="Engineering",
            timestamp="2024-03-29T14:37:00Z",
            affected_systems=["auth-service-prod", "db-prod-primary"],
            affected_users_count=200,
            sla_hours=1,
        ),
        "ground_truth": {
            "category":              TicketCategory.SOFTWARE,
            "priority":              TicketPriority.P1,
            "assigned_team":         AssignedTeam.APPLICATION_SUPPORT,
            "is_part_of_incident":   True,
            "incident_id":           "INC-MAJOR-01",
            "escalate_to_management": False,
            "resolution_steps": [
                "Update auth-service DB_HOST env-var to db-prod-replica-01",
                "Rolling-restart all auth-service-prod pods to apply new config",
                "Verify end-to-end login flow with a test account after restart",
                "Monitor error rate — should return to 0% within 2 min",
            ],
        },
    },
    {
        "ticket": Ticket(
            id="TKT-H003",
            subject="E-commerce checkout failing for ALL users — $2,400/min revenue loss",
            description=(
                "100% checkout failure since ~14:36. Frontend: 'Unable to process your order, please try again.' "
                "App logs: 'ConnectionPoolExhausted: max_size=100 connections exhausted' "
                "as connections to db-prod-primary are blocking with no timeout. "
                "Revenue loss accumulating at ~$2,400/min per analytics dashboard."
            ),
            reporter="Emma Thompson",
            reporter_department="E-Commerce",
            timestamp="2024-03-29T14:40:00Z",
            affected_systems=["ecommerce-app-prod", "db-prod-primary", "payment-service"],
            affected_users_count=500,
            sla_hours=1,
        ),
        "ground_truth": {
            "category":              TicketCategory.DATABASE,
            "priority":              TicketPriority.P1,
            "assigned_team":         AssignedTeam.APPLICATION_SUPPORT,
            "is_part_of_incident":   True,
            "incident_id":           "INC-MAJOR-01",
            "escalate_to_management": True,
            "resolution_steps": [
                "Enable checkout maintenance page immediately to stop revenue bleed",
                "Drain and reset the exhausted DB connection pool",
                "Redirect ecommerce-app DB_HOST to db-prod-replica-01",
                "Disable maintenance page once checkout is verified on replica",
                "Coordinate with DBA on primary recovery timeline for write operations",
            ],
        },
    },
    {
        "ticket": Ticket(
            id="TKT-H004",
            subject="Reminder: Quarterly team lunch tomorrow at 12 PM",
            description=(
                "Just a friendly reminder that our quarterly team lunch is tomorrow at 12 PM "
                "at The Italian Place on Main Street. Please reply to confirm attendance "
                "by end of day today so I can finalise the reservation headcount."
            ),
            reporter="Susan Bradley",
            reporter_department="Human Resources",
            timestamp="2024-03-29T14:45:00Z",
            affected_systems=[],
            affected_users_count=0,
            sla_hours=72,
        ),
        "ground_truth": {
            "category":              TicketCategory.OTHER,
            "priority":              TicketPriority.P4,
            "assigned_team":         AssignedTeam.HELPDESK,
            "is_part_of_incident":   False,
            "escalate_to_management": False,
            "resolution_steps":      None,
        },
    },
    {
        "ticket": Ticket(
            id="TKT-H005",
            subject="Metabase analytics dashboard frozen — exec presentation in 80 min",
            description=(
                "All Metabase dashboards are frozen showing data as of 14:30 and not refreshing. "
                "The BI team has a C-suite presentation at 16:00 requiring live sales metrics. "
                "Metabase query runner logs show: 'Query error: connection to db-prod-primary refused.' "
                "This is read-only analytics — no writes required."
            ),
            reporter="Analytics Team",
            reporter_department="Business Intelligence",
            timestamp="2024-03-29T14:50:00Z",
            affected_systems=["metabase-prod", "db-prod-primary"],
            affected_users_count=5,
            sla_hours=2,
        ),
        "ground_truth": {
            "category":              TicketCategory.DATABASE,
            "priority":              TicketPriority.P2,
            "assigned_team":         AssignedTeam.DATABASE_ADMIN,
            "is_part_of_incident":   True,
            "incident_id":           "INC-MAJOR-01",
            "escalate_to_management": False,
            "resolution_steps": [
                "Update Metabase DB connection to point to db-prod-replica-01 (read-only is fine)",
                "Restart Metabase query runner service to flush cached connection state",
                "Notify BI team replica is live and dashboards should refresh within 2 min",
            ],
        },
    },
    {
        "ticket": Ticket(
            id="TKT-H006",
            subject="TLS certificate for mail.company.com expiring in 7 days",
            description=(
                "CertBot automated alert: TLS certificate for mail.company.com (SHA-256) "
                "expires 2024-04-05. Certificate renewal request has already been submitted "
                "to DigiCert CA and is awaiting approval. This is a planned, non-urgent renewal "
                "with 7 days of lead time remaining."
            ),
            reporter="CertBot (Automated)",
            reporter_department="IT Infrastructure",
            timestamp="2024-03-29T14:55:00Z",
            affected_systems=["mail-server-prod"],
            affected_users_count=0,
            sla_hours=72,
        ),
        "ground_truth": {
            "category":              TicketCategory.SECURITY,
            "priority":              TicketPriority.P3,
            "assigned_team":         AssignedTeam.INFRASTRUCTURE,
            "is_part_of_incident":   False,
            "escalate_to_management": False,
            "resolution_steps":      None,
        },
    },
    {
        "ticket": Ticket(
            id="TKT-H007",
            subject="Nightly C-suite reporting batch job failed — exec reports not generated",
            description=(
                "Scheduled job 'rpt-daily-summary' failed at 14:38 with exit code 1. "
                "Log: 'CRITICAL: All 3 DB connection attempts failed. "
                "SQLAlchemy error: (psycopg2.OperationalError) could not connect to server.' "
                "Daily KPI reports for CEO, CFO, and COO have not been generated. "
                "Next scheduled run is 22:00 tonight."
            ),
            reporter="Job Scheduler (Automated)",
            reporter_department="IT Infrastructure",
            timestamp="2024-03-29T14:39:00Z",
            affected_systems=["rpt-daily-summary", "reporting-service", "db-prod-primary"],
            affected_users_count=3,
            sla_hours=2,
        ),
        "ground_truth": {
            "category":              TicketCategory.SOFTWARE,
            "priority":              TicketPriority.P2,
            "assigned_team":         AssignedTeam.APPLICATION_SUPPORT,
            "is_part_of_incident":   True,
            "incident_id":           "INC-MAJOR-01",
            "escalate_to_management": False,
            "resolution_steps": [
                "Update reporting-service DB_HOST to db-prod-replica-01",
                "Manually trigger rpt-daily-summary once DB failover is confirmed complete",
                "Notify exec assistants that reports will be delayed until ~15:30",
                "Reschedule 22:00 cron job to point at new primary once restored",
            ],
        },
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# Task Registry
# ──────────────────────────────────────────────────────────────────────────────

TASK_REGISTRY: Dict[str, Dict] = {
    "basic_triage": {
        "description": "Classify and triage basic IT support tickets — category, priority, and team assignment.",
        "difficulty":  "easy",
        "tickets":     TASK_EASY_TICKETS,
        "max_steps":   10,
    },
    "priority_routing": {
        "description": "Handle complex tickets with correct priority assignment, incident detection, and escalation decisions.",
        "difficulty":  "medium",
        "tickets":     TASK_MEDIUM_TICKETS,
        "max_steps":   10,
    },
    "incident_escalation": {
        "description": (
            "Manage a cascading PostgreSQL WAL-corruption incident: identify 5 linked tickets "
            "among 7, declare the major incident, and provide step-by-step remediation plans."
        ),
        "difficulty":  "hard",
        "tickets":     TASK_HARD_TICKETS,
        "max_steps":   15,
    },
}

_PRIORITY_ORDER = [TicketPriority.P1, TicketPriority.P2, TicketPriority.P3, TicketPriority.P4]


# ──────────────────────────────────────────────────────────────────────────────
# Environment Class
# ──────────────────────────────────────────────────────────────────────────────

class ITTriageEnvironment:
    """
    IT Helpdesk Triage & Incident Management — OpenEnv Environment.
    """

    def __init__(self) -> None:
        self._task_id: Optional[str]          = None
        self._tickets: List[Dict]             = []
        self._current_index: int              = 0
        self._step_number: int                = 0
        self._max_steps: int                  = 15
        self._reward_history: List[float]     = []
        self._action_history: List[Dict]      = []
        self._declared_incidents: List[str]   = []

    def reset(self, task_id: str = "basic_triage") -> Observation:
        if task_id not in TASK_REGISTRY:
            valid = list(TASK_REGISTRY.keys())
            raise ValueError(f"Unknown task_id='{task_id}'. Valid tasks: {valid}")

        cfg = TASK_REGISTRY[task_id]
        self._task_id          = task_id
        self._tickets          = list(cfg["tickets"])
        self._current_index    = 0
        self._step_number      = 0
        self._max_steps        = cfg["max_steps"]
        self._reward_history   = []
        self._action_history   = []
        self._declared_incidents = []

        return self._build_observation(action_feedback=None)

    def step(self, action: TriageAction) -> StepResult:
        if self._task_id is None:
            raise RuntimeError("Environment not initialised. Call reset(task_id) first.")

        if self._current_index >= len(self._tickets):
            obs = self._build_observation("Queue exhausted — episode complete.")
            obs.episode_done = True
            return StepResult(observation=obs, reward=0.0, done=True,
                              info={"reason": "queue_empty"})

        gt = self._tickets[self._current_index]["ground_truth"]
        reward, breakdown = self._compute_reward(action, gt)

        self._reward_history.append(reward)
        self._action_history.append(action.model_dump())
        if action.is_part_of_incident and action.incident_id:
            if action.incident_id not in self._declared_incidents:
                self._declared_incidents.append(action.incident_id)

        self._current_index += 1
        self._step_number   += 1

        done = (
            self._current_index >= len(self._tickets)
            or self._step_number >= self._max_steps
        )

        feedback = self._generate_feedback(action, gt, breakdown)
        obs = self._build_observation(action_feedback=feedback)
        obs.episode_done = done

        gt_serialisable = {
            k: (v.value if hasattr(v, "value") else v)
            for k, v in gt.items()
        }

        return StepResult(
            observation=obs,
            reward=round(reward, 4),
            done=done,
            info={
                "ticket_id":        action.ticket_id,
                "reward_breakdown": breakdown.model_dump(),
                "ground_truth":     gt_serialisable,
                "cumulative_score": obs.cumulative_score,
            },
        )

    def state(self) -> EnvironmentState:
        return EnvironmentState(
            task_id=self._task_id or "uninitialized",
            step_number=self._step_number,
            episode_complete=(self._current_index >= len(self._tickets)),
            tickets_total=len(self._tickets),
            tickets_processed=self._current_index,
            tickets_remaining=max(0, len(self._tickets) - self._current_index),
            cumulative_score=self._cumulative_score(),
            reward_history=self._reward_history,
            declared_incidents=self._declared_incidents,
            action_history=self._action_history,
        )

    def list_tasks(self) -> List[Dict]:
        return [
            {
                "task_id":      tid,
                "description":  cfg["description"],
                "difficulty":   cfg["difficulty"],
                "ticket_count": len(cfg["tickets"]),
                "max_steps":    cfg["max_steps"],
            }
            for tid, cfg in TASK_REGISTRY.items()
        ]

    # ── Reward Engine ─────────────────────────────────────────────────────────

    def _compute_reward(
        self, action: TriageAction, gt: Dict
    ) -> Tuple[float, RewardBreakdown]:
        difficulty = TASK_REGISTRY[self._task_id]["difficulty"]

        category_score = 1.0 if action.category == gt["category"] else 0.0
        priority_score = self._score_priority(action.priority, gt["priority"])
        routing_score  = 1.0 if action.assigned_team == gt["assigned_team"] else 0.0

        incident_score = 0.0
        if difficulty in ("medium", "hard"):
            expected_incident = gt.get("is_part_of_incident", False)
            if action.is_part_of_incident == expected_incident:
                incident_score = 0.7
                if expected_incident and gt.get("incident_id"):
                    if action.incident_id == gt["incident_id"]:
                        incident_score = 1.0

        expected_escalate = gt.get("escalate_to_management", False)
        if action.escalate_to_management == expected_escalate:
            escalation_score = 1.0
        elif action.escalate_to_management and not expected_escalate:
            escalation_score = 0.3
        else:
            escalation_score = 0.0

        resolution_score = 0.0
        expected_steps = gt.get("resolution_steps")
        if difficulty == "hard":
            if expected_steps:
                resolution_score = self._score_resolution_steps(
                    action.resolution_steps, expected_steps
                )
            else:
                resolution_score = 1.0 if not action.resolution_steps else 0.7

        penalty = 0.0
        if action.escalate_to_management and gt["priority"] == TicketPriority.P4:
            penalty = 0.15

        if difficulty == "easy":
            raw = (
                0.40 * category_score
                + 0.35 * priority_score
                + 0.25 * routing_score
                - penalty
            )
        elif difficulty == "medium":
            raw = (
                0.28 * category_score
                + 0.22 * priority_score
                + 0.18 * routing_score
                + 0.18 * incident_score
                + 0.14 * escalation_score
                - penalty
            )
        else:
            raw = (
                0.20 * category_score
                + 0.18 * priority_score
                + 0.14 * routing_score
                + 0.20 * incident_score
                + 0.12 * escalation_score
                + 0.16 * resolution_score
                - penalty
            )

        total = round(max(0.0, min(1.0, raw)), 4)

        breakdown = RewardBreakdown(
            category_score=round(category_score, 4),
            priority_score=round(priority_score, 4),
            routing_score=round(routing_score, 4),
            incident_score=round(incident_score, 4),
            escalation_score=round(escalation_score, 4),
            resolution_score=round(resolution_score, 4),
            penalty=round(penalty, 4),
            total=total,
        )
        return total, breakdown

    def _score_priority(self, assigned: TicketPriority, expected: TicketPriority) -> float:
        if assigned == expected:
            return 1.0
        diff = abs(_PRIORITY_ORDER.index(assigned) - _PRIORITY_ORDER.index(expected))
        return 0.5 if diff == 1 else 0.0

    def _score_resolution_steps(
        self, provided: Optional[List[str]], expected: List[str]
    ) -> float:
        if not provided:
            return 0.0
        if not expected:
            return 1.0

        _STOPWORDS = {
            "the","a","an","to","and","or","is","in","of","for","on","with",
            "be","all","this","it","from","at","by","are","as","if","not","do",
        }

        def tokens(steps: List[str]) -> set:
            result = set()
            for s in steps:
                result.update(
                    t for t in s.lower().split()
                    if len(t) > 3 and t not in _STOPWORDS
                )
            return result

        exp_kw  = tokens(expected)
        prov_kw = tokens(provided)

        keyword_recall = len(exp_kw & prov_kw) / len(exp_kw) if exp_kw else 1.0

        matched_exp_steps = 0
        for exp_step in expected:
            exp_tokens = set(exp_step.lower().split())
            for prov_step in provided:
                prov_tokens = set(prov_step.lower().split())
                if len(exp_tokens & prov_tokens) >= 2:
                    matched_exp_steps += 1
                    break

        step_recall = matched_exp_steps / len(expected)
        score = 0.35 * keyword_recall + 0.65 * step_recall
        return round(min(1.0, score), 4)

    def _build_observation(self, action_feedback: Optional[str]) -> Observation:
        current_ticket = None
        queue_remaining = 0

        if self._current_index < len(self._tickets):
            current_ticket  = self._tickets[self._current_index]["ticket"]
            queue_remaining = len(self._tickets) - self._current_index - 1

        return Observation(
            task_id=self._task_id or "uninitialized",
            current_ticket=current_ticket,
            queue_remaining=queue_remaining,
            processed_count=self._current_index,
            step_number=self._step_number,
            action_feedback=action_feedback,
            cumulative_score=self._cumulative_score(),
            episode_done=(self._current_index >= len(self._tickets)
                          if self._tickets else True),
            active_incidents=list(self._declared_incidents),
            hints=self._hints(),
        )

    def _cumulative_score(self) -> float:
        if not self._reward_history:
            return 0.0
        return round(sum(self._reward_history) / len(self._reward_history), 4)

    def _hints(self) -> List[str]:
        difficulty = TASK_REGISTRY.get(self._task_id or "", {}).get("difficulty", "easy")
        if difficulty == "easy":
            return [
                "Assign category, priority (P1-P4), and responsible team for each ticket.",
                "P1=Critical (system/business down), P2=High, P3=Medium, P4=Low.",
            ]
        elif difficulty == "medium":
            return [
                "Some tickets share a root cause — detect incident patterns across the queue.",
                "Business-critical processes (payroll, e-commerce) warrant P1 + management escalation.",
                "Security anomalies are always P1 regardless of confirmed breach status.",
            ]
        return [
            "Identify which tickets are symptoms of the same root cause. Declare one incident ID.",
            "For every P1 ticket, provide specific, ordered resolution_steps.",
            "Not all 7 tickets belong to the incident — triage noise tickets correctly too.",
            "Revenue-impacting outages require immediate management escalation.",
        ]

    def _generate_feedback(
        self, action: TriageAction, gt: Dict, bd: RewardBreakdown
    ) -> str:
        parts = []
        cat_ok = "correct" if bd.category_score == 1.0 else "wrong"
        pri_ok = "correct" if bd.priority_score  == 1.0 else ("close" if bd.priority_score == 0.5 else "wrong")
        rte_ok = "correct" if bd.routing_score   == 1.0 else "wrong"

        parts.append(f"category={cat_ok}({action.category.value})")
        if bd.category_score < 1.0:
            parts[-1] += f"->expected:{gt['category'].value}"

        parts.append(f"priority={pri_ok}({action.priority.value})")
        if bd.priority_score < 1.0:
            parts[-1] += f"->expected:{gt['priority'].value}"

        parts.append(f"team={rte_ok}({action.assigned_team.value})")
        if bd.routing_score < 1.0:
            parts[-1] += f"->expected:{gt['assigned_team'].value}"

        parts.append(f"reward={bd.total:.3f}")
        return " | ".join(parts)
