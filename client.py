"""
client.py
Thin Python HTTP client over the IT Triage OpenEnv REST API.
Provides a clean, typed interface for use in inference scripts and notebooks.
"""

from __future__ import annotations

from typing import Any, Dict, List

import requests

from models import EnvironmentState, Observation, StepResult, TriageAction


class ITTriageClient:
    """
    Synchronous HTTP client for the IT Triage OpenEnv environment.

    Usage:
        client = ITTriageClient(base_url="http://localhost:7860")
        obs    = client.reset("basic_triage")
        result = client.step(action)
        st     = client.state()
    """

    def __init__(self, base_url: str = "http://localhost:7860", timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout  = timeout
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def health(self) -> Dict[str, Any]:
        """Ping the server and return health/task metadata."""
        return self._get("/")

    def reset(self, task_id: str = "basic_triage") -> Observation:
        """Reset the environment and return the initial observation."""
        data = self._post("/reset", {"task_id": task_id})
        return Observation(**data)

    def step(self, action: TriageAction) -> StepResult:
        """Submit a triage action and receive (obs, reward, done, info)."""
        data = self._post("/step", action.model_dump())
        return StepResult(**data)

    def state(self) -> EnvironmentState:
        """Fetch the full current environment state."""
        data = self._get("/state")
        return EnvironmentState(**data)

    def list_tasks(self) -> List[Dict[str, Any]]:
        """Return all registered tasks."""
        return self._get("/tasks")

    def _get(self, path: str) -> Any:
        resp = self._session.get(f"{self.base_url}{path}", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: Dict) -> Any:
        resp = self._session.post(
            f"{self.base_url}{path}",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()
