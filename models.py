"""
models.py
Pydantic v2 typed models for the IT Helpdesk Triage OpenEnv environment.
Defines the complete Action / Observation / State interface contracts.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# Domain Enums
# ──────────────────────────────────────────────────────────────────────────────

class TicketCategory(str, Enum):
    """ITIL-aligned classification categories for IT support tickets."""
    HARDWARE    = "hardware"
    SOFTWARE    = "software"
    NETWORK     = "network"
    SECURITY    = "security"
    ACCESS      = "access"
    DATABASE    = "database"
    PERFORMANCE = "performance"
    OTHER       = "other"


class TicketPriority(str, Enum):
    """
    Priority levels following ITIL P1-P4 convention.
    P1 = Critical (complete outage / business-stopping).
    P4 = Low (cosmetic, informational, no business impact).
    """
    P1 = "P1"   # Critical  – SLA: 1 h
    P2 = "P2"   # High      – SLA: 4 h
    P3 = "P3"   # Medium    – SLA: 8 h
    P4 = "P4"   # Low       – SLA: 48 h


class AssignedTeam(str, Enum):
    """Available support teams for ticket routing."""
    INFRASTRUCTURE      = "infrastructure"
    APPLICATION_SUPPORT = "application_support"
    NETWORK_OPS         = "network_ops"
    SECURITY_OPS        = "security_ops"
    DATABASE_ADMIN      = "database_admin"
    HELPDESK            = "helpdesk"


# ──────────────────────────────────────────────────────────────────────────────
# Action Space
# ──────────────────────────────────────────────────────────────────────────────

class TriageAction(BaseModel):
    """
    The complete action an agent submits to triage one ticket.
    Used as the primary Action type across all three tasks.
    """
    ticket_id: str = Field(
        ...,
        description="Exact ID of the ticket being triaged (e.g. 'TKT-E001')."
    )
    category: TicketCategory = Field(
        ...,
        description="Issue classification category."
    )
    priority: TicketPriority = Field(
        ...,
        description="Assigned ITIL priority level (P1-P4)."
    )
    assigned_team: AssignedTeam = Field(
        ...,
        description="Resolver team responsible for this ticket."
    )
    is_part_of_incident: bool = Field(
        default=False,
        description="True when this ticket is a symptom of a declared major incident."
    )
    incident_id: Optional[str] = Field(
        default=None,
        description="Major-incident identifier if applicable (e.g. 'INC-MAJOR-01')."
    )
    resolution_steps: Optional[List[str]] = Field(
        default=None,
        description=(
            "Ordered list of remediation steps. "
            "Required for P1 tickets in the 'incident_escalation' task."
        )
    )
    escalate_to_management: bool = Field(
        default=False,
        description="Whether to page senior management / C-suite for this ticket."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Observation Space
# ──────────────────────────────────────────────────────────────────────────────

class Ticket(BaseModel):
    """A single IT support ticket as seen by the agent."""
    id: str                          = Field(..., description="Unique ticket identifier.")
    subject: str                     = Field(..., description="One-line summary of the issue.")
    description: str                 = Field(..., description="Full free-text description from the reporter.")
    reporter: str                    = Field(..., description="Full name of the person who raised the ticket.")
    reporter_department: str         = Field(..., description="Business department of the reporter.")
    timestamp: str                   = Field(..., description="ISO-8601 creation timestamp.")
    affected_systems: List[str]      = Field(..., description="Hostnames / service identifiers impacted.")
    affected_users_count: int        = Field(default=1, description="Number of end-users affected.")
    sla_hours: int                   = Field(..., description="SLA resolution target in hours.")


class Observation(BaseModel):
    """
    Returned after every reset() and step() call.
    Contains the next ticket to triage plus episode-level metadata.
    """
    task_id: str                        = Field(..., description="Active task identifier.")
    current_ticket: Optional[Ticket]    = Field(
        default=None,
        description="Ticket awaiting triage. None when the queue is exhausted."
    )
    queue_remaining: int                = Field(..., description="Tickets still waiting in the queue.")
    processed_count: int                = Field(..., description="Tickets triaged so far this episode.")
    step_number: int                    = Field(..., description="Current step index (0-based).")
    action_feedback: Optional[str]      = Field(
        default=None,
        description="Human-readable correctness feedback on the previous action."
    )
    cumulative_score: float             = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Running mean reward across all completed steps."
    )
    episode_done: bool                  = Field(default=False, description="True when the episode has ended.")
    active_incidents: List[str]         = Field(
        default_factory=list,
        description="Incident IDs declared so far in this episode."
    )
    hints: List[str]                    = Field(
        default_factory=list,
        description="Task-level guidance hints for the agent."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Step Result
# ──────────────────────────────────────────────────────────────────────────────

class StepResult(BaseModel):
    """Full return value of the /step endpoint (OpenEnv convention)."""
    observation: Observation
    reward: float                       = Field(..., ge=0.0, le=1.0, description="Per-step reward.")
    done: bool
    info: Dict[str, Any]                = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Reward Breakdown (internal / surfaced in info)
# ──────────────────────────────────────────────────────────────────────────────

class RewardBreakdown(BaseModel):
    """Granular per-dimension reward decomposition returned inside StepResult.info."""
    category_score:          float = Field(0.0, ge=0.0, le=1.0)
    priority_score:          float = Field(0.0, ge=0.0, le=1.0)
    routing_score:           float = Field(0.0, ge=0.0, le=1.0)
    incident_score:          float = Field(0.0, ge=0.0, le=1.0)
    escalation_score:        float = Field(0.0, ge=0.0, le=1.0)
    resolution_score:        float = Field(0.0, ge=0.0, le=1.0)
    penalty:                 float = Field(0.0, ge=0.0, le=1.0)
    total:                   float = Field(0.0, ge=0.0, le=1.0)


# ──────────────────────────────────────────────────────────────────────────────
# Environment State (for /state endpoint)
# ──────────────────────────────────────────────────────────────────────────────

class EnvironmentState(BaseModel):
    """Complete serialisable snapshot of the environment (returned by state())."""
    task_id:             str
    step_number:         int
    episode_complete:    bool
    tickets_total:       int
    tickets_processed:   int
    tickets_remaining:   int
    cumulative_score:    float
    reward_history:      List[float]
    declared_incidents:  List[str]
    action_history:      List[Dict[str, Any]]
