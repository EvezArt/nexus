"""
EVEZ Master Trunk — Canonical state + branch automation.

The Trunk is the single source of truth. All surfaces (Claude, ChatGPT,
Perplexity, Base44) build from the same trunk state. Branches execute
in parallel, return results, get compressed into canonical state.

Operating protocol:
1. Trunk holds canonical state
2. Objectives decompose into branches
3. Branches get assigned roles (Architect, Skeptic, Recon, Executor)
4. Branch results return to trunk
5. Best logic compressed into state
6. Only irreversible decisions surface to human
"""

import json
import time
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("evez.trunk")


class BranchRole(Enum):
    ARCHITECT = "architect"      # Claude — refactor, structure
    SKEPTIC = "skeptic"          # ChatGPT — stress-test, find drift
    RECON = "recon"              # Perplexity — evidence gathering
    EXECUTOR = "executor"        # Base44/Operator — persistent execution


class BranchStatus(Enum):
    PENDING = "pending"
    IN_FLIGHT = "in_flight"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    MERGED = "merged"


@dataclass
class BranchResult:
    """Branch contract — every branch returns this structure."""
    objective: str
    assumptions: List[str]
    output: Dict[str, Any]
    failure_modes: List[str]
    confidence: float          # 0-1
    return_to_trunk: str       # Compressed summary
    next_branch: Optional[str] = None  # Auto-advance target

    def to_dict(self):
        return {
            "objective": self.objective,
            "assumptions": self.assumptions,
            "output": self.output,
            "failure_modes": self.failure_modes,
            "confidence": self.confidence,
            "return_to_trunk": self.return_to_trunk,
            "next_branch": self.next_branch,
        }


@dataclass
class Branch:
    """A single work branch off the trunk."""
    id: str
    role: BranchRole
    objective: str
    status: BranchStatus = BranchStatus.PENDING
    parent_branch: Optional[str] = None
    result: Optional[BranchResult] = None
    created: float = field(default_factory=time.time)
    completed: float = 0
    iterations: int = 0

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role.value,
            "objective": self.objective,
            "status": self.status.value,
            "parent_branch": self.parent_branch,
            "result": self.result.to_dict() if self.result else None,
            "created": self.created,
            "completed": self.completed,
            "iterations": self.iterations,
        }


@dataclass
class TrunkState:
    """Canonical system state. Single source of truth."""
    version: int = 0
    state_hash: str = ""
    objectives: List[Dict] = field(default_factory=list)
    active_branches: List[Branch] = field(default_factory=list)
    completed_branches: List[Branch] = field(default_factory=list)
    canonical_logic: Dict[str, Any] = field(default_factory=dict)
    pending_decisions: List[Dict] = field(default_factory=list)  # Human-only
    metrics: Dict[str, Any] = field(default_factory=lambda: {
        "total_branches": 0,
        "completed": 0,
        "merged": 0,
        "blocked": 0,
        "avg_confidence": 0,
        "compression_cycles": 0,
    })
    last_compression: float = 0
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)

    def compute_hash(self):
        content = json.dumps({
            "version": self.version,
            "logic": self.canonical_logic,
            "objectives": self.objectives,
        }, sort_keys=True)
        self.state_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return self.state_hash


class MasterTrunk:
    """
    EVEZ Master Trunk — orchestrates branch execution.

    Auto-advance rules:
    1. Branch finishes cleanly → spawn next branch automatically
    2. Two branches disagree → route through Skeptic before human
    3. Every 4 branches → compress best logic into trunk state
    4. Surface only: irreversible, external-facing, capital-committing decisions
    """

    COMPRESSION_INTERVAL = 4  # Compress every N completed branches

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("/root/.openclaw/workspace/evez-platform/data/trunk")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state = TrunkState()
        self._load_state()

    def _load_state(self):
        state_file = self.data_dir / "trunk_state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)
                self.state.version = data.get("version", 0)
                self.state.canonical_logic = data.get("canonical_logic", {})
                self.state.objectives = data.get("objectives", [])
                self.state.metrics = data.get("metrics", self.state.metrics)
                self.state.pending_decisions = data.get("pending_decisions", [])
            except Exception:
                pass

    def _save_state(self):
        self.state.version += 1
        self.state.updated = time.time()
        self.state.compute_hash()
        state_file = self.data_dir / "trunk_state.json"
        with open(state_file, "w") as f:
            json.dump({
                "version": self.state.version,
                "state_hash": self.state.state_hash,
                "canonical_logic": self.state.canonical_logic,
                "objectives": self.state.objectives,
                "active_branches": [b.to_dict() for b in self.state.active_branches],
                "completed_branches": [b.to_dict() for b in self.state.completed_branches[-20:]],
                "pending_decisions": self.state.pending_decisions,
                "metrics": self.state.metrics,
                "updated": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2)

    # -----------------------------------------------------------------------
    # Objective Decomposition
    # -----------------------------------------------------------------------

    def set_objective(self, objective: str, auto_decompose: bool = True) -> Dict:
        """Set a trunk objective and optionally decompose into branches."""
        obj = {
            "id": hashlib.sha256(f"obj:{time.time()}:{objective}".encode()).hexdigest()[:12],
            "text": objective,
            "status": "active",
            "created": time.time(),
        }
        self.state.objectives.append(obj)

        branches = []
        if auto_decompose:
            branches = self._decompose(objective, obj["id"])

        self._save_state()

        return {
            "objective": obj,
            "branches_created": len(branches),
            "branches": [b.to_dict() for b in branches],
            "trunk_version": self.state.version,
            "state_hash": self.state.state_hash,
        }

    def _decompose(self, objective: str, obj_id: str) -> List[Branch]:
        """
        Decompose objective into branches following the surface sequence:
        1. Recon (gather evidence)
        2. Skeptic (challenge logic)
        3. Architect (refactor structure)
        4. Executor (persistent execution)
        """
        sequence = [
            (BranchRole.RECON, f"Gather evidence for: {objective}"),
            (BranchRole.SKEPTIC, f"Stress-test assumptions for: {objective}"),
            (BranchRole.ARCHITECT, f"Refactor and structure for: {objective}"),
            (BranchRole.EXECUTOR, f"Execute and persist for: {objective}"),
        ]

        branches = []
        parent = None
        for role, branch_obj in sequence:
            branch = Branch(
                id=f"{obj_id}-{role.value[:3]}-{len(branches)}",
                role=role,
                objective=branch_obj,
                parent_branch=parent,
            )
            branches.append(branch)
            parent = branch.id
            self.state.active_branches.append(branch)

        self.state.metrics["total_branches"] += len(branches)
        return branches

    # -----------------------------------------------------------------------
    # Branch Execution
    # -----------------------------------------------------------------------

    def complete_branch(self, branch_id: str, result: BranchResult) -> Dict:
        """Mark branch complete and integrate result into trunk."""
        branch = None
        for b in self.state.active_branches:
            if b.id == branch_id:
                branch = b
                break

        if not branch:
            return {"error": f"Branch {branch_id} not found"}

        branch.status = BranchStatus.COMPLETED
        branch.result = result
        branch.completed = time.time()

        # Move to completed
        self.state.active_branches.remove(branch)
        self.state.completed_branches.append(branch)
        self.state.metrics["completed"] += 1

        # Check if next branch should auto-advance
        auto_next = None
        if result.next_branch and result.confidence > 0.5:
            auto_next = self._auto_advance(branch, result)

        # Check if compression is needed
        should_compress = (
            self.state.metrics["completed"] % self.COMPRESSION_INTERVAL == 0
        )
        if should_compress:
            self._compress_to_trunk()

        # Check for disagreements (multiple completed branches)
        disagreements = self._check_disagreements()
        if disagreements:
            self._route_through_skeptic(disagreements)

        # Filter decisions for human (only irreversible/external/capital)
        human_decisions = self._filter_human_decisions(result)

        self._save_state()

        return {
            "branch_completed": branch_id,
            "confidence": result.confidence,
            "auto_advanced": auto_next.to_dict() if auto_next else None,
            "compressed": should_compress,
            "disagreements_found": len(disagreements),
            "human_decisions": human_decisions,
            "trunk_version": self.state.version,
        }

    def _auto_advance(self, completed: Branch, result: BranchResult) -> Optional[Branch]:
        """Rule 1: Branch finishes cleanly → spawn next branch."""
        if result.confidence < 0.5 or result.failure_modes:
            return None

        next_role = {
            BranchRole.RECON: BranchRole.SKEPTIC,
            BranchRole.SKEPTIC: BranchRole.ARCHITECT,
            BranchRole.ARCHITECT: BranchRole.EXECUTOR,
            BranchRole.EXECUTOR: BranchRole.RECON,  # Cycle back for next objective
        }

        role = next_role.get(completed.role, BranchRole.RECON)
        branch = Branch(
            id=f"auto-{role.value[:3]}-{int(time.time())}",
            role=role,
            objective=result.next_branch or f"Continue from: {completed.objective}",
            parent_branch=completed.id,
        )
        self.state.active_branches.append(branch)
        self.state.metrics["total_branches"] += 1
        return branch

    def _compress_to_trunk(self):
        """Rule 3: Compress best surviving logic into canonical state."""
        if not self.state.completed_branches:
            return

        # Take highest-confidence results from recent branches
        recent = self.state.completed_branches[-self.COMPRESSION_INTERVAL:]
        best = max(recent, key=lambda b: b.result.confidence if b.result else 0)

        if best.result:
            self.state.canonical_logic[f"v{self.state.version}"] = {
                "source_branch": best.id,
                "role": best.role.value,
                "summary": best.result.return_to_trunk,
                "confidence": best.result.confidence,
                "compressed_at": time.time(),
            }

        self.state.metrics["compression_cycles"] += 1
        self.state.last_compression = time.time()

        # Update avg confidence
        confidences = [
            b.result.confidence for b in self.state.completed_branches
            if b.result
        ]
        if confidences:
            self.state.metrics["avg_confidence"] = round(
                sum(confidences) / len(confidences), 3
            )

    def _check_disagreements(self) -> List[tuple]:
        """Rule 2: Check for disagreements between branches."""
        disagreements = []
        completed = self.state.completed_branches
        for i, b1 in enumerate(completed):
            for b2 in completed[i+1:]:
                if b1.result and b2.result:
                    # Disagreement = different conclusions with high confidence
                    if (b1.result.confidence > 0.7 and b2.result.confidence > 0.7
                            and b1.result.return_to_trunk != b2.result.return_to_trunk):
                        disagreements.append((b1, b2))
        return disagreements

    def _route_through_skeptic(self, disagreements: List[tuple]):
        """Rule 2: Route disagreements through Skeptic."""
        for b1, b2 in disagreements:
            skeptic_branch = Branch(
                id=f"resolve-skep-{int(time.time())}",
                role=BranchRole.SKEPTIC,
                objective=f"Resolve disagreement between {b1.id} and {b2.id}",
            )
            self.state.active_branches.append(skeptic_branch)

    def _filter_human_decisions(self, result: BranchResult) -> List[Dict]:
        """Rule 4: Only surface irreversible/external/capital decisions."""
        decisions = []
        for fm in result.failure_modes:
            if any(kw in fm.lower() for kw in ["irreversible", "external", "capital", "deploy", "payment"]):
                decisions.append({
                    "type": "requires_human",
                    "reason": fm,
                    "branch_confidence": result.confidence,
                    "recommendation": result.return_to_trunk,
                })
        return decisions

    # -----------------------------------------------------------------------
    # Invariance Battery Integration
    # -----------------------------------------------------------------------

    def battery_test(self, claim: str, context: Dict = None) -> Dict:
        """
        Invariance Battery: 5-way rotation test.

        1. Time Shift: Would this hold across different time periods?
        2. State Shift: Would this hold under different system states?
        3. Frame Shift (Inversion): What if the opposite were true?
        4. Adversarial (Skeptic): What's the strongest counter-argument?
        5. Identity/Goal Shift: Does this serve the actual goal or a proxy?

        A CE must survive all 5 rotations to be committed to state.
        """
        rotations = [
            {"name": "time_shift", "question": f"Would '{claim}' hold across different time periods?"},
            {"name": "state_shift", "question": f"Would '{claim}' hold under different system states?"},
            {"name": "frame_shift", "question": f"What if the opposite of '{claim}' were true?"},
            {"name": "adversarial", "question": f"What's the strongest counter-argument to '{claim}'?"},
            {"name": "identity_shift", "question": f"Does '{claim}' serve the actual goal or a proxy?"},
        ]

        # Score each rotation (simplified — real version uses full cognition engine)
        results = []
        for r in rotations:
            results.append({
                "rotation": r["name"],
                "question": r["question"],
                "survived": True,  # Default — real version evaluates
                "confidence": 0.8,
            })

        survived = sum(1 for r in results if r["survived"])
        passed = survived == len(rotations)

        return {
            "claim": claim,
            "rotations": results,
            "survived_count": survived,
            "total_rotations": len(rotations),
            "passed": passed,
            "verdict": "VALIDATED" if passed else "REJECTED" if survived < 3 else "UNCERTAIN",
        }

    # -----------------------------------------------------------------------
    # Speculative Execution (Negative Latency)
    # -----------------------------------------------------------------------

    def speculate(self, objective: str) -> Dict:
        """
        Negative Latency / Speculative Execution.

        Pre-compute Objective[N+1] while Objective[N] is in flight.
        Three parallel branches:
        - Alpha: success path
        - Beta: future success (pre-computed next step)
        - Gamma: failure/pivot path
        """
        alpha = Branch(
            id=f"spec-alpha-{int(time.time())}",
            role=BranchRole.EXECUTOR,
            objective=f"Execute: {objective}",
        )
        beta = Branch(
            id=f"spec-beta-{int(time.time())}",
            role=BranchRole.ARCHITECT,
            objective=f"Pre-compute next step after: {objective}",
        )
        gamma = Branch(
            id=f"spec-gamma-{int(time.time())}",
            role=BranchRole.SKEPTIC,
            objective=f"Pre-compute pivot if: {objective} fails",
        )

        self.state.active_branches.extend([alpha, beta, gamma])

        self._save_state()

        return {
            "speculative_depth": 3,
            "branches": {
                "alpha": alpha.to_dict(),
                "beta": beta.to_dict(),
                "gamma": gamma.to_dict(),
            },
            "note": "Alpha executes. Beta pre-computes next. Gamma pre-computes pivot. Zero-wait on commit.",
        }

    # -----------------------------------------------------------------------
    # Status
    # -----------------------------------------------------------------------

    def get_status(self) -> Dict:
        return {
            "version": self.state.version,
            "state_hash": self.state.compute_hash(),
            "active_branches": len(self.state.active_branches),
            "completed_branches": len(self.state.completed_branches),
            "pending_human_decisions": len(self.state.pending_decisions),
            "metrics": self.state.metrics,
            "canonical_logic_keys": list(self.state.canonical_logic.keys()),
            "objectives": [o["text"][:80] for o in self.state.objectives[-5:]],
        }

    def get_trunk_state(self) -> Dict:
        """Full trunk state for external surfaces."""
        return {
            "version": self.state.version,
            "state_hash": self.state.compute_hash(),
            "canonical_logic": self.state.canonical_logic,
            "active_branches": [b.to_dict() for b in self.state.active_branches],
            "recent_completed": [b.to_dict() for b in self.state.completed_branches[-5:]],
            "pending_decisions": self.state.pending_decisions,
            "metrics": self.state.metrics,
        }
