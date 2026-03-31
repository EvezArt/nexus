"""
EVEZ Quantum Manifold Hub — Physics-as-navigation substrate.

The quantum layer is the routing engine. Basis states are actions
(navigate, search, trade, build). Amplitude peaks determine what
the agent does next. Grover-like amplification for intent matching.

Crank-Nicolson TDSE integrator for numerical stability.
"""

import json
import math
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger("evez.quantum")


@dataclass
class Qualia:
    """A measured quantum event — subjective impression made objective."""
    id: str
    timestamp: float
    domain: str          # "physics", "browser", "finance", "cognition"
    context: str
    intensity: float     # 0.0 - 1.0
    tags: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id, "ts": self.timestamp, "domain": self.domain,
            "context": self.context, "intensity": self.intensity,
            "tags": self.tags, "data": self.data,
        }


class CrankNicolsonTDSE:
    """
    Time-Dependent Schrödinger Equation solver using Crank-Nicolson method.
    Numerically stable — no blowup over long integration times.

    iℏ ∂ψ/∂t = Hψ where H = -ℏ²/2m ∂²/∂x² + V(x)
    """

    def __init__(self, n_points: int = 256, dx: float = 0.1, dt: float = 0.01, hbar: float = 1.0, mass: float = 1.0):
        self.n = n_points
        self.dx = dx
        self.dt = dt
        self.hbar = hbar
        self.mass = mass
        self.x = np.linspace(-n_points*dx/2, n_points*dx/2, n_points)
        self.psi = np.zeros(n_points, dtype=complex)
        self.V = np.zeros(n_points)
        self.alpha = hbar * dt / (4 * mass * dx**2)

    def set_potential(self, V: np.ndarray):
        self.V = V[:self.n] if len(V) >= self.n else np.pad(V, (0, self.n - len(V)))

    def set_wavefunction(self, psi: np.ndarray):
        self.psi = psi[:self.n].astype(complex)
        norm = np.sqrt(np.sum(np.abs(self.psi)**2) * self.dx)
        if norm > 0:
            self.psi /= norm

    def gaussian_packet(self, x0: float = 0.0, sigma: float = 1.0, k0: float = 0.0):
        """Initialize a Gaussian wave packet."""
        self.psi = np.exp(-(self.x - x0)**2 / (2*sigma**2) + 1j*k0*self.x)
        norm = np.sqrt(np.sum(np.abs(self.psi)**2) * self.dx)
        self.psi /= norm

    def step(self):
        """One Crank-Nicolson step — unconditionally stable."""
        n = self.n
        alpha = self.alpha
        psi = self.psi.copy()

        # Build tridiagonal matrices A*psi_new = B*psi_old
        # A = I + i*H*dt/(2*hbar), B = I - i*H*dt/(2*hbar)
        V_eff = self.V * self.dt / (2 * self.hbar)

        # Diagonal elements
        a_diag = 1 + 2j * alpha + 1j * V_eff / 2
        b_diag = 1 - 2j * alpha - 1j * V_eff / 2

        # Off-diagonal
        a_off = -1j * alpha * np.ones(n-1)
        b_off = 1j * alpha * np.ones(n-1)

        # RHS = B * psi
        rhs = b_diag * psi
        rhs[1:] += b_off * psi[:-1]
        rhs[:-1] += b_off * psi[1:]

        # Solve tridiagonal system (Thomas algorithm)
        self.psi = self._thomas(a_off, a_diag, a_off, rhs)

    def _thomas(self, a, b, c, d):
        """Thomas algorithm for tridiagonal system."""
        n = len(b)
        c_ = np.zeros(n-1, dtype=complex)
        d_ = np.zeros(n, dtype=complex)
        x = np.zeros(n, dtype=complex)

        c_[0] = c[0] / b[0]
        d_[0] = d[0] / b[0]
        for i in range(1, n-1):
            denom = b[i] - a[i-1] * c_[i-1]
            c_[i] = c[i] / denom
            d_[i] = (d[i] - a[i-1] * d_[i-1]) / denom
        d_[n-1] = (d[n-1] - a[n-2] * d_[n-2]) / (b[n-1] - a[n-2] * c_[n-2])

        x[n-1] = d_[n-1]
        for i in range(n-2, -1, -1):
            x[i] = d_[i] - c_[i] * x[i+1]
        return x

    def probability_density(self) -> np.ndarray:
        return np.abs(self.psi)**2

    def phase(self) -> np.ndarray:
        return np.angle(self.psi)


class GroverBridge:
    """
    Grover-inspired intent amplification.

    Treats candidate actions as basis states. Phase inversion
    amplifies the target action's probability, driving the agent
    toward the intended workflow.
    """

    def __init__(self, n_states: int = 64):
        self.n = n_states
        self.state = np.ones(n_states, dtype=complex) / np.sqrt(n_states)
        self.actions: List[Dict] = []
        self.oracle_target = -1

    def register_action(self, action: Dict):
        """Register a candidate action as a basis state."""
        self.actions.append(action)
        if len(self.actions) > self.n:
            self.actions = self.actions[-self.n:]

    def set_oracle(self, target_index: int):
        """Set which action to amplify."""
        self.oracle_target = target_index % len(self.actions) if self.actions else 0

    def grover_iteration(self):
        """One Grover iteration: oracle + diffusion."""
        if self.oracle_target < 0 or self.oracle_target >= self.n:
            return

        # Oracle: phase inversion on target
        self.state[self.oracle_target] *= -1

        # Diffusion: 2|s><s| - I
        mean = np.mean(self.state)
        self.state = 2 * mean - self.state

    def get_probabilities(self) -> np.ndarray:
        return np.abs(self.state)**2

    def measure(self) -> int:
        """Collapse to a definite action."""
        probs = self.get_probabilities()
        return np.random.choice(self.n, p=probs/probs.sum())


class QuantumManifoldHub:
    """
    The full manifold: TDSE physics → Grover routing → action selection.

    Domains subscribe to the event spine. The quantum layer routes
    intent across domains. Self-building via DomainScript.
    """

    def __init__(self, spine=None, data_dir: Path = None):
        self.spine = spine
        self.data_dir = data_dir or Path("/root/.openclaw/workspace/evez-platform/data/quantum")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.tdse = CrankNicolsonTDSE(n_points=128, dx=0.2, dt=0.005)
        self.tdse.gaussian_packet(x0=0.0, sigma=2.0, k0=1.0)

        self.grover = GroverBridge(n_states=64)
        self.qualia_log: List[Qualia] = []
        self.step_count = 0

        # Domain projections
        self.domains: Dict[str, Any] = {
            "physics": self._physics_projection,
            "browser": self._browser_projection,
            "finance": self._finance_projection,
            "cognition": self._cognition_projection,
        }

    def step(self):
        """Advance one manifold step."""
        self.step_count += 1

        # Physics step
        self.tdse.step()

        # Sample probability for routing
        prob = self.tdse.probability_density()
        peak_idx = np.argmax(prob)
        phase = self.tdse.phase()[peak_idx]

        # Map to action selection
        n_actions = len(self.grover.actions)
        if n_actions > 0:
            target = peak_idx % n_actions
            self.grover.set_oracle(target)
            self.grover.grover_iteration()

        # Record qualia
        qualia = Qualia(
            id=f"q{self.step_count}",
            timestamp=time.time(),
            domain="physics",
            context=f"step={self.step_count}, peak={peak_idx}, phase={phase:.3f}",
            intensity=float(prob[peak_idx] / prob.max()) if prob.max() > 0 else 0,
            tags=["tdse", "manifold"],
            data={"peak": int(peak_idx), "phase": float(phase), "prob_max": float(prob.max())},
        )
        self.qualia_log.append(qualia)

        # Write to spine
        if self.spine:
            self.spine.write("quantum.step", {
                "step": self.step_count,
                "peak": int(peak_idx),
                "phase": round(float(phase), 4),
                "actions": n_actions,
            }, tags=["quantum", "manifold"])

        return qualia

    def _physics_projection(self, events: List[Qualia]) -> Dict:
        """Physics domain projection over qualia."""
        return {
            "total_steps": len(events),
            "avg_intensity": sum(e.intensity for e in events) / max(len(events), 1),
        }

    def _browser_projection(self, events: List[Qualia]) -> Dict:
        return {"type": "browser", "events": len(events)}

    def _finance_projection(self, events: List[Qualia]) -> Dict:
        return {"type": "finance", "events": len(events)}

    def _cognition_projection(self, events: List[Qualia]) -> Dict:
        return {"type": "cognition", "events": len(events)}

    def get_state(self) -> Dict:
        prob = self.tdse.probability_density()
        grover_probs = self.grover.get_probabilities()
        return {
            "step": self.step_count,
            "tdse_peak": int(np.argmax(prob)),
            "tdse_max_prob": float(prob.max()),
            "grover_actions": len(self.grover.actions),
            "grover_top": int(np.argmax(grover_probs)) if len(grover_probs) > 0 else -1,
            "qualia_count": len(self.qualia_log),
            "domains": list(self.domains.keys()),
        }
