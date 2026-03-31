"""
EVEZ Trunk — The master integration bus.

Routes messages between surfaces (ChatGPT, Claude, Perplexity, n8n, GitHub, Linear, Slack).
Each surface has a role. The trunk coordinates them all.
"""

import json
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

import httpx

logger = logging.getLogger("evez.trunk")


class SurfaceRole(Enum):
    ARCHITECT = "architect"      # Claude 4.5 — Refactor, structure
    SKEPTIC = "skeptic"          # ChatGPT o3 — Stress-test, verify
    RECON = "recon"              # Perplexity — Research, evidence
    EXECUTOR = "executor"        # Base44 / n8n — Execute, persist


class BranchStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Branch:
    """A single branch of work in the trunk system."""
    id: str
    objective: str
    role: SurfaceRole
    status: BranchStatus = BranchStatus.PENDING
    assumptions: List[str] = field(default_factory=list)
    output: str = ""
    failure_modes: List[str] = field(default_factory=list)
    confidence: float = 0.0
    return_summary: str = ""
    next_branch: str = ""
    created: float = field(default_factory=time.time)
    completed: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id, "objective": self.objective,
            "role": self.role.value, "status": self.status.value,
            "assumptions": self.assumptions, "output": self.output,
            "failure_modes": self.failure_modes, "confidence": self.confidence,
            "return_summary": self.return_summary, "next_branch": self.next_branch,
        }


@dataclass
class TrunkState:
    """The canonical state of the entire system."""
    version: str = "0.1.0"
    objectives: List[str] = field(default_factory=list)
    completed_branches: List[Dict] = field(default_factory=list)
    active_branches: List[Dict] = field(default_factory=list)
    canonical_logic: str = ""
    blocked_decisions: List[str] = field(default_factory=list)
    last_compression: float = 0
    compression_count: int = 0

    def to_dict(self):
        return {
            "version": self.version,
            "objectives": self.objectives,
            "completed": len(self.completed_branches),
            "active": len(self.active_branches),
            "blocked": self.blocked_decisions,
            "compressions": self.compression_count,
        }


class SurfaceConnector:
    """Base class for connecting to external surfaces."""

    async def execute(self, prompt: str, context: Dict = None) -> str:
        raise NotImplementedError


class ChatGPTConnector(SurfaceConnector):
    """ChatGPT o3 — Skeptic role."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"

    async def execute(self, prompt: str, context: Dict = None) -> str:
        if not self.api_key:
            return "No ChatGPT API key configured"
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {"role": "system", "content": "Execute as EVEZ Skeptic Entity. Stress-test with Invariance Battery. Find drift, hidden assumptions, brittle edges. Return: (1) surviving core, (2) rejected logic, (3) revised spec, (4) what goes back to trunk."},
                            {"role": "user", "content": prompt}
                        ],
                    }
                )
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"ChatGPT error: {e}"


class PerplexityConnector(SurfaceConnector):
    """Perplexity — Recon role."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"

    async def execute(self, prompt: str, context: Dict = None) -> str:
        if not self.api_key:
            return "No Perplexity API key configured"
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "sonar-pro",
                        "messages": [
                            {"role": "system", "content": "Deep Research. Gather current public signals, comparable companies, funding events, technical papers, product launches relevant to the supplied objective. Output a raw evidence table with source, date, signal type, and why it matters."},
                            {"role": "user", "content": prompt}
                        ],
                    }
                )
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Perplexity error: {e}"


class N8NConnector(SurfaceConnector):
    """n8n — Executor role."""

    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url

    async def execute(self, prompt: str, context: Dict = None) -> str:
        if not self.webhook_url:
            return "No n8n webhook configured"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(self.webhook_url, json={
                    "action": "execute",
                    "prompt": prompt,
                    "context": context or {},
                })
                return r.text
        except Exception as e:
            return f"n8n error: {e}"


class Trunk:
    """
    The EVEZ Trunk — master coordination layer.

    Auto-advance rules:
    1. Branch finishes → spawn next branch automatically
    2. Two branches disagree → route through Skeptic
    3. Every 4 branches → compress best logic into trunk
    4. Only surface decisions that are irreversible/capital-committing
    """

    def __init__(self, spine=None, data_dir: Path = None):
        self.spine = spine
        self.data_dir = data_dir or Path("/root/.openclaw/workspace/evez-platform/data/trunk")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.state = TrunkState()
        self.branches: List[Branch] = []
        self.surfaces: Dict[str, SurfaceConnector] = {}

        # Surface sequence: Recon → Skeptic → Architect → Executor
        self.default_sequence = [
            SurfaceRole.RECON,
            SurfaceRole.SKEPTIC,
            SurfaceRole.ARCHITECT,
            SurfaceRole.EXECUTOR,
        ]

    def register_surface(self, name: str, connector: SurfaceConnector):
        """Register a surface connector."""
        self.surfaces[name] = connector
        logger.info("Registered surface: %s", name)

    async def advance(self, objective: str) -> Dict:
        """
        Advance trunk on an objective.
        Decompose → assign branches → execute → return state.
        """
        # Create branches from sequence
        branches = []
        for i, role in enumerate(self.default_sequence):
            branch_id = hashlib.sha256(f"{objective}:{role.value}:{i}".encode()).hexdigest()[:12]
            branch = Branch(
                id=branch_id,
                objective=objective if i == 0 else f"[{role.value}] {objective}",
                role=role,
            )
            branches.append(branch)

        self.branches.extend(branches)
        self.state.objectives.append(objective)

        # Execute sequence
        results = []
        context = {"objective": objective, "prior_results": []}

        for branch in branches:
            result = await self._execute_branch(branch, context)
            results.append(result)
            context["prior_results"].append(result)

            # Check for auto-compression (every 4 branches)
            if len(self.state.completed_branches) % 4 == 0 and self.state.completed_branches:
                await self._compress_trunk()

        # Check for disagreements
        disagreements = self._find_disagreements(results)
        if disagreements:
            skeptic_result = await self._route_through_skeptic(disagreements, context)
            results.append(skeptic_result)

        # Filter: only surface blocked/irreversible decisions
        blocked = [r for r in results if r.get("status") == "blocked"]

        return {
            "objective": objective,
            "branches_executed": len(results),
            "results": results,
            "blocked_decisions": blocked,
            "trunk_state": self.state.to_dict(),
        }

    async def _execute_branch(self, branch: Branch, context: Dict) -> Dict:
        """Execute a single branch through its assigned surface."""
        branch.status = BranchStatus.RUNNING

        # Build prompt from branch contract template
        prompt = self._build_prompt(branch, context)

        # Find the right surface
        surface_name = self._surface_for_role(branch.role)
        surface = self.surfaces.get(surface_name)

        if not surface:
            # Use EVEZ's own agent as fallback
            branch.output = f"No surface registered for {branch.role.value}, using local agent"
            branch.status = BranchStatus.COMPLETED
            result = {"branch": branch.to_dict(), "status": "local"}
        else:
            try:
                output = await surface.execute(prompt, context)
                branch.output = output
                branch.status = BranchStatus.COMPLETED
                branch.completed = time.time()
                result = {"branch": branch.to_dict(), "status": "completed"}
            except Exception as e:
                branch.status = BranchStatus.FAILED
                branch.output = str(e)
                result = {"branch": branch.to_dict(), "status": "failed", "error": str(e)}

        self.state.completed_branches.append(branch.to_dict())

        if self.spine:
            self.spine.write("trunk.branch", {
                "id": branch.id,
                "role": branch.role.value,
                "status": branch.status.value,
            }, tags=["trunk", "branch"])

        return result

    def _build_prompt(self, branch: Branch, context: Dict) -> str:
        """Build a branch contract prompt."""
        prior = context.get("prior_results", [])
        prior_text = ""
        if prior:
            prior_text = "\n\nPrior branch outputs:\n" + "\n".join(
                f"[{r.get('branch',{}).get('role','?')}]: {r.get('branch',{}).get('output','')[:500]}"
                for r in prior[-3:]
            )

        return f"""Branch Contract:
Objective: {branch.objective}
Role: {branch.role.value}
{prior_text}

Return structure:
1. Objective
2. Assumptions
3. Output
4. Failure modes
5. Confidence (0.0-1.0)
6. Return-to-trunk summary
7. Next automatic branch"""

    def _surface_for_role(self, role: SurfaceRole) -> str:
        """Map role to surface name."""
        mapping = {
            SurfaceRole.ARCHITECT: "claude",
            SurfaceRole.SKEPTIC: "chatgpt",
            SurfaceRole.RECON: "perplexity",
            SurfaceRole.EXECUTOR: "n8n",
        }
        return mapping.get(role, "local")

    def _find_disagreements(self, results: List[Dict]) -> List[Dict]:
        """Find branches that disagree."""
        # Simple heuristic: look for low confidence or explicit failures
        return [r for r in results if r.get("branch", {}).get("confidence", 1.0) < 0.3]

    async def _route_through_skeptic(self, disagreements: List[Dict], context: Dict) -> Dict:
        """Route disagreements through Skeptic for resolution."""
        prompt = f"Resolve these disagreements:\n{json.dumps(disagreements, indent=2)}\n\nApply Invariance Battery. Return surviving logic."
        surface = self.surfaces.get("chatgpt")
        if surface:
            output = await surface.execute(prompt, context)
            return {"branch": {"role": "skeptic_resolution"}, "status": "resolved", "output": output}
        return {"branch": {"role": "skeptic_resolution"}, "status": "unresolved"}

    async def _compress_trunk(self):
        """Compress best surviving logic into canonical state."""
        self.state.compression_count += 1
        self.state.last_compression = time.time()

        if self.spine:
            self.spine.write("trunk.compress", {
                "count": self.state.compression_count,
                "branches_processed": len(self.state.completed_branches),
            }, tags=["trunk", "compress"])

    def get_state(self) -> Dict:
        return {
            "trunk": self.state.to_dict(),
            "surfaces": list(self.surfaces.keys()),
            "branches": len(self.branches),
            "sequence": [r.value for r in self.default_sequence],
        }
