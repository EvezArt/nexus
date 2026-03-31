"""
EVEZ Cognitive Sensory Engine — Invariance Battery + Proof Grammar

The cognitive core. Entities perceive, think, stress-test, then commit.
Every thought (Cognitive Event) must survive the Invariance Battery
before becoming action. Adaptive, recursive, self-improving.

Based on:
- Invariance Battery: 5 rotation stress-test protocol
- ERL (arXiv:2603.24639): Experiential Reflective Learning
- Bilevel Autoresearch (arXiv:2603.23420): Meta-optimizing research loops
- Proof Grammar: Defeater rules for recursive validation
"""

import json
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger("evez.cognition")


# ---------------------------------------------------------------------------
# Sensory Modalities
# ---------------------------------------------------------------------------

class Modality(Enum):
    TEXT = "text"
    AUDIO = "audio"
    VISUAL = "visual"
    MARKET = "market"        # DeFi flows, price, sentiment
    NETWORK = "network"      # Telemetry, latency, topology
    CODE = "code"            # Source, diffs, test results
    SPINE = "spine"          # Internal spine events


class Confidence(Enum):
    ANTECEDENT = "antecedent"   # Raw perception, unverified
    HYPOTHESIS = "hypothesis"   # Pattern recognized, untested
    TESTED = "tested"           # Passed some rotations
    VALIDATED = "validated"     # Passed all rotations
    DEFEATED = "defeated"       # Failed a rotation
    ARCHIVED = "archived"       # Stored for ERL learning


# ---------------------------------------------------------------------------
# Cognitive Event — the atomic unit of thought
# ---------------------------------------------------------------------------

@dataclass
class CognitiveEvent:
    """A single thought/conclusion that must survive the Invariance Battery."""
    id: str
    content: str
    modality: Modality
    confidence: Confidence
    source: str               # What triggered this thought
    reasoning: str = ""       # Why this thought formed
    rotations_passed: int = 0
    rotations_failed: int = 0
    rotation_results: Dict[str, dict] = field(default_factory=dict)
    defeaters: List[str] = field(default_factory=list)
    created: float = field(default_factory=time.time)
    validated: float = 0
    action: str = ""          # "act", "hold", "test", "discard"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d["modality"] = self.modality.value
        d["confidence"] = self.confidence.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "CognitiveEvent":
        d["modality"] = Modality(d["modality"])
        d["confidence"] = Confidence(d["confidence"])
        return cls(**d)


# ---------------------------------------------------------------------------
# Rotation — a single stress-test in the Invariance Battery
# ---------------------------------------------------------------------------

class RotationType(Enum):
    TIME_SHIFT = "time_shift"         # Does CE hold projected T+1h?
    STATE_SHIFT = "state_shift"       # Different system moods (vol, liquidity)
    FRAME_SHIFT = "frame_shift"       # Invert the logic — does opposite hold?
    ADVERSARIAL = "adversarial"       # Skeptic Entity finds flaws
    GOAL_SHIFT = "goal_shift"         # Swap primary goal, does CE survive?


@dataclass
class RotationResult:
    rotation_type: RotationType
    passed: bool
    strength: float           # 0.0 - 1.0, how well it survived
    defeater: Optional[str]   # If failed, why
    evidence: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        d = asdict(self)
        d["rotation_type"] = self.rotation_type.value
        return d


# ---------------------------------------------------------------------------
# Invariance Battery — the stress-test protocol
# ---------------------------------------------------------------------------

class InvarianceBattery:
    """
    A Cognitive Event must survive 5 rotations to move from Test to Act.

    Rules:
    - Rule 0 (Recursion Floor): Test results must be consistent across
      at least 2 State Shifts (Stable vs Chaotic) to be valid.
    - Rule 1 (Defeater Priority): Any Strong Defeater rejects the CE.
    - ERL Enhancement: Battery is adaptive — retrieves highest-signal
      rotation for each CE based on prior experience.
    """

    def __init__(self, spine=None):
        self.spine = spine
        self.rotation_history: List[Dict] = []
        self.heuristics: Dict[str, float] = {}  # rotation_type → success_rate
        self._init_heuristics()

    def _init_heuristics(self):
        for rt in RotationType:
            self.heuristics[rt.value] = 0.5  # Start neutral

    def run_battery(self, ce: CognitiveEvent, context: Dict = None) -> CognitiveEvent:
        """Run all 5 rotations on a Cognitive Event."""
        context = context or {}
        rotations = self._get_ordered_rotations(ce)

        for rotation_type in rotations:
            result = self._run_rotation(ce, rotation_type, context)
            ce.rotation_results[rotation_type.value] = result.to_dict()

            if result.passed:
                ce.rotations_passed += 1
                # Update heuristic (ERL learning)
                self.heuristics[rotation_type.value] = (
                    self.heuristics[rotation_type.value] * 0.9 + 0.1
                )
            else:
                ce.rotations_failed += 1
                self.heuristics[rotation_type.value] = (
                    self.heuristics[rotation_type.value] * 0.9
                )
                if result.defeater:
                    ce.defeaters.append(result.defeater)

                # Rule 1: Strong defeater → reject immediately
                if result.strength < 0.3:
                    ce.confidence = Confidence.DEFEATED
                    ce.action = "discard"
                    return ce

        # Determine final confidence
        if ce.rotations_passed == 5:
            ce.confidence = Confidence.VALIDATED
            ce.action = "act"
        elif ce.rotations_passed >= 3:
            ce.confidence = Confidence.TESTED
            ce.action = "hold"
        else:
            ce.confidence = Confidence.DEFEATED
            ce.action = "discard"

        ce.validated = time.time()
        return ce

    def _get_ordered_rotations(self, ce: CognitiveEvent) -> List[RotationType]:
        """ERL: Order rotations by heuristic signal — highest success-rate first."""
        ordered = sorted(
            RotationType,
            key=lambda rt: self.heuristics.get(rt.value, 0.5),
            reverse=True,
        )
        return ordered

    def _run_rotation(self, ce: CognitiveEvent, rotation: RotationType,
                      context: Dict) -> RotationResult:
        """Execute a single rotation test."""

        if rotation == RotationType.TIME_SHIFT:
            return self._time_shift(ce, context)
        elif rotation == RotationType.STATE_SHIFT:
            return self._state_shift(ce, context)
        elif rotation == RotationType.FRAME_SHIFT:
            return self._frame_shift(ce, context)
        elif rotation == RotationType.ADVERSARIAL:
            return self._adversarial(ce, context)
        elif rotation == RotationType.GOAL_SHIFT:
            return self._goal_shift(ce, context)
        else:
            return RotationResult(rotation, False, 0.0, "Unknown rotation type")

    def _time_shift(self, ce: CognitiveEvent, ctx: Dict) -> RotationResult:
        """Does the CE hold if data is aged or projected T+1h?"""
        # Check if CE has temporal sensitivity
        content = ce.content.lower()
        temporal_markers = ["now", "currently", "today", "just", "recently", "lately"]
        has_temporal = any(m in content for m in temporal_markers)

        if not has_temporal:
            # Non-temporal CE — passes by default
            return RotationResult(RotationType.TIME_SHIFT, True, 0.9,
                                None, "CE has no temporal sensitivity")

        # Temporal CE — check if conclusion would hold with older data
        # Heuristic: if CE references specific prices/events, penalize
        specific_refs = ["$", "price", "at ", "%"]
        specificity = sum(1 for r in specific_refs if r in content) / len(specific_refs)

        if specificity > 0.5:
            return RotationResult(RotationType.TIME_SHIFT, False, 0.3,
                                "Temporal specificity too high — conclusion may not hold T+1h",
                                f"Specificity: {specificity:.2f}")
        return RotationResult(RotationType.TIME_SHIFT, True, 0.7,
                            None, f"Low temporal specificity: {specificity:.2f}")

    def _state_shift(self, ce: CognitiveEvent, ctx: Dict) -> RotationResult:
        """Different system moods: High vs Low Volatility, High vs Low Liquidity."""
        # Simulate chaotic vs stable conditions
        volatility = ctx.get("volatility", 0.5)
        liquidity = ctx.get("liquidity", 0.5)

        # In chaotic conditions, more CEs should fail
        chaos_factor = volatility * (1 - liquidity)

        # Rule 0: Recursion Floor — check if test results are consistent
        # across Stable and Chaotic state shifts
        stable_result = chaos_factor < 0.3
        chaotic_result = chaos_factor < 0.7

        if stable_result and chaotic_result:
            return RotationResult(RotationType.STATE_SHIFT, True, 0.8,
                                None, "CE holds across stable and chaotic states")
        elif stable_result:
            return RotationResult(RotationType.STATE_SHIFT, True, 0.5,
                                None, "CE holds in stable state only — partial pass")
        else:
            return RotationResult(RotationType.STATE_SHIFT, False, 0.2,
                                "CE fails under chaotic conditions — state-dependent",
                                f"Chaos factor: {chaos_factor:.2f}")

    def _frame_shift(self, ce: CognitiveEvent, ctx: Dict) -> RotationResult:
        """Invert the logic — does the opposite conclusion look equally compelling?"""
        content = ce.content.lower()

        # Look for signal direction
        bullish = any(w in content for w in ["buy", "bull", "long", "up", "increase", "rise", "positive"])
        bearish = any(w in content for w in ["sell", "bear", "short", "down", "decrease", "fall", "negative"])

        if not bullish and not bearish:
            # Neutral CE — frame shift is less relevant
            return RotationResult(RotationType.FRAME_SHIFT, True, 0.7,
                                None, "CE is directionally neutral — frame shift irrelevant")

        # If the CE is strongly directional, check if opposite has evidence
        # For now, heuristic: strong directional claims need more evidence
        evidence_count = ce.content.count("because") + ce.content.count("since") + ce.content.count("evidence")
        if evidence_count == 0 and (bullish or bearish):
            return RotationResult(RotationType.FRAME_SHIFT, False, 0.4,
                                "Directional claim without evidence — opposite is equally unsupported",
                                "No causal reasoning found in CE")
        return RotationResult(RotationType.FRAME_SHIFT, True, 0.7,
                            None, f"CE provides {evidence_count} evidence chains")

    def _adversarial(self, ce: CognitiveEvent, ctx: Dict) -> RotationResult:
        """Skeptic Entity programmed to find flaws."""
        content = ce.content.lower()
        flaws = []

        # Check for common cognitive biases
        if "always" in content or "never" in content:
            flaws.append("Absolute language — black/white thinking")
        if "everyone" in content or "nobody" in content:
            flaws.append("Hasty generalization — not everyone/nobody")
        if "obviously" in content or "clearly" in content:
            flaws.append("Appeal to obviousness — asserting without proof")
        if "!" in content and content.count("!") > 2:
            flaws.append("Emotional emphasis substituting for evidence")

        # Check for missing uncertainty
        uncertainty_markers = ["might", "could", "possibly", "perhaps", "likely", "unlikely"]
        has_uncertainty = any(m in content for m in uncertainty_markers)
        if not has_uncertainty and len(content) > 100:
            flaws.append("No uncertainty expression — overconfident conclusion")

        if len(flaws) >= 2:
            return RotationResult(RotationType.ADVERSARIAL, False, 0.3,
                                f"Skeptic found {len(flaws)} flaws: {'; '.join(flaws)}")
        elif len(flaws) == 1:
            return RotationResult(RotationType.ADVERSARIAL, True, 0.6,
                                None, f"Skeptic found 1 minor flaw: {flaws[0]}")
        else:
            return RotationResult(RotationType.ADVERSARIAL, True, 0.9,
                                None, "Skeptic found no structural flaws")

    def _goal_shift(self, ce: CognitiveEvent, ctx: Dict) -> RotationResult:
        """Swap primary goal — does CE survive if goal changes from profit to safety?"""
        original_goal = ctx.get("goal", "maximize_value")
        alternate_goals = ["maximize_safety", "maintain_neutrality", "minimize_risk"]

        content = ce.content.lower()
        profit_markers = ["profit", "gain", "return", "earn", "revenue", "income"]
        safety_markers = ["safe", "secure", "stable", "protect", "preserve"]

        profit_focus = sum(1 for m in profit_markers if m in content)
        safety_focus = sum(1 for m in safety_markers if m in content)

        if profit_focus > 0 and safety_focus == 0:
            return RotationResult(RotationType.GOAL_SHIFT, False, 0.4,
                                "CE is profit-focused with no safety consideration — fails under safety goal",
                                f"Profit markers: {profit_focus}, Safety markers: {safety_focus}")
        elif safety_focus > 0 or (profit_focus > 0 and safety_focus > 0):
            return RotationResult(RotationType.GOAL_SHIFT, True, 0.8,
                                None, "CE considers multiple goal dimensions")
        else:
            return RotationResult(RotationType.GOAL_SHIFT, True, 0.7,
                                None, "CE is goal-neutral — survives goal shift")


# ---------------------------------------------------------------------------
# Sensory Pipeline — Audio → Text → Thought → Visual
# ---------------------------------------------------------------------------

class SensoryPipeline:
    """
    Multi-modal perception pipeline:
    1. Intake raw sensory data (audio, text, visual, market, network)
    2. Convert to canonical text representation
    3. Generate Cognitive Event (pattern recognition)
    4. Feed through Invariance Battery
    5. Commit or discard

    Audio → transcription → text analysis → CE → Battery → Visual map
    """

    def __init__(self, battery: InvarianceBattery, spine=None):
        self.battery = battery
        self.spine = spine
        self.perception_buffer: List[Dict] = []
        self.visual_maps: Dict[str, Dict] = {}

    async def perceive(self, modality: str, raw_input: str,
                       context: Dict = None) -> Dict:
        """
        Process raw sensory input through the full pipeline.
        Returns the Cognitive Event after battery testing.
        """
        context = context or {}
        mod = Modality(modality) if modality in [m.value for m in Modality] else Modality.TEXT

        # Step 1: Normalize to text
        canonical = self._normalize(mod, raw_input)

        # Step 2: Generate Cognitive Event
        ce_id = hashlib.sha256(f"{modality}:{raw_input}:{time.time()}".encode()).hexdigest()[:16]
        ce = CognitiveEvent(
            id=ce_id,
            content=canonical,
            modality=mod,
            confidence=Confidence.ANTECEDENT,
            source=f"perception:{modality}",
            reasoning="Raw perception — pattern not yet recognized",
        )

        # Step 3: Pattern recognition (elevate to Hypothesis)
        ce = self._recognize_pattern(ce, context)

        # Step 4: Run Invariance Battery
        ce = self.battery.run_battery(ce, context)

        # Step 5: Generate visual map
        visual = self._generate_visual_map(ce)

        # Step 6: Store in perception buffer
        self.perception_buffer.append(ce.to_dict())
        if len(self.perception_buffer) > 1000:
            self.perception_buffer = self.perception_buffer[-500:]

        # Step 7: Write to spine if validated
        if ce.confidence == Confidence.VALIDATED and self.spine:
            self.spine.write("cognition.validated", {
                "ce_id": ce.id,
                "content": ce.content[:200],
                "action": ce.action,
                "rotations_passed": ce.rotations_passed,
            }, tags=["cognition", "validated"])

        return {
            "ce": ce.to_dict(),
            "visual_map": visual,
            "action": ce.action,
            "confidence": ce.confidence.value,
        }

    def _normalize(self, modality: Modality, raw: str) -> str:
        """Convert any modality to canonical text representation."""
        if modality == Modality.TEXT:
            return raw
        elif modality == Modality.AUDIO:
            # Placeholder for audio transcription
            return f"[AUDIO TRANSCRIPTION]: {raw}"
        elif modality == Modality.VISUAL:
            return f"[VISUAL DESCRIPTION]: {raw}"
        elif modality == Modality.MARKET:
            return f"[MARKET SIGNAL]: {raw}"
        elif modality == Modality.NETWORK:
            return f"[NETWORK TELEMETRY]: {raw}"
        elif modality == Modality.CODE:
            return f"[CODE ANALYSIS]: {raw}"
        elif modality == Modality.SPINE:
            return f"[SPINE EVENT]: {raw}"
        return raw

    def _recognize_pattern(self, ce: CognitiveEvent, ctx: Dict) -> CognitiveEvent:
        """Pattern recognition — elevate from Antecedent to Hypothesis."""
        content = ce.content.lower()

        # Detect patterns
        patterns = []
        if any(w in content for w in ["trend", "pattern", "recurring", "repeating"]):
            patterns.append("temporal_pattern")
        if any(w in content for w in ["correlation", "relationship", "linked", "connected"]):
            patterns.append("relational_pattern")
        if any(w in content for w in ["anomaly", "outlier", "unusual", "unexpected"]):
            patterns.append("anomaly_pattern")
        if any(w in content for w in ["increase", "decrease", "growing", "shrinking"]):
            patterns.append("directional_pattern")

        if patterns:
            ce.confidence = Confidence.HYPOTHESIS
            ce.reasoning = f"Patterns detected: {', '.join(patterns)}"
            ce.metadata["patterns"] = patterns
        else:
            ce.reasoning = "No clear pattern — raw antecedent"

        return ce

    def _generate_visual_map(self, ce: CognitiveEvent) -> Dict:
        """
        Generate a mental map visualization of the CE.
        Each word re-renders the image in the mind map.
        """
        words = ce.content.split()
        nodes = []
        for i, word in enumerate(words[:50]):  # Cap at 50 nodes
            nodes.append({
                "id": i,
                "text": word,
                "x": (i % 10) * 80 + 40,
                "y": (i // 10) * 60 + 30,
                "confidence": ce.confidence.value,
                "connected_to": [i-1] if i > 0 else [],
            })

        return {
            "ce_id": ce.id,
            "nodes": nodes,
            "confidence_color": {
                "antecedent": "#666666",
                "hypothesis": "#f59e0b",
                "tested": "#3b82f6",
                "validated": "#22c55e",
                "defeated": "#ef4444",
                "archived": "#8b5cf6",
            }.get(ce.confidence.value, "#666"),
            "layout": "linear_word_map",
        }

    def get_state(self) -> Dict:
        return {
            "perceptions_buffered": len(self.perception_buffer),
            "visual_maps": len(self.visual_maps),
            "battery_heuristics": self.battery.heuristics,
        }


# ---------------------------------------------------------------------------
# Multi-Action Threshold Engine
# ---------------------------------------------------------------------------

class ActionThreshold:
    """
    Multi-action thresholds with decay.
    An entity accumulates evidence toward multiple actions simultaneously.
    Whichever threshold is crossed first determines the action.
    Thresholds decay over time, preventing stale decisions.
    """

    def __init__(self):
        self.actions: Dict[str, float] = {
            "act": 0.0,
            "hold": 0.0,
            "test": 0.0,
            "discard": 0.0,
        }
        self.thresholds: Dict[str, float] = {
            "act": 0.8,
            "hold": 0.6,
            "test": 0.4,
            "discard": 0.3,
        }
        self.decay_rate = 0.95  # Per cycle

    def update(self, evidence: Dict[str, float]):
        """Add evidence to action accumulators."""
        for action, weight in evidence.items():
            if action in self.actions:
                self.actions[action] = min(1.0, self.actions[action] + weight)

    def decay(self):
        """Apply decay to all accumulators."""
        for action in self.actions:
            self.actions[action] *= self.decay_rate

    def check_threshold(self) -> Optional[str]:
        """Check if any action threshold has been crossed."""
        for action, threshold in self.thresholds.items():
            if self.actions[action] >= threshold:
                return action
        return None

    def get_state(self) -> Dict:
        return {
            "accumulators": dict(self.actions),
            "thresholds": dict(self.thresholds),
            "nearest_action": max(self.actions, key=self.actions.get),
            "nearest_value": max(self.actions.values()),
        }


# ---------------------------------------------------------------------------
# Cognitive Engine — ties it all together
# ---------------------------------------------------------------------------

class CognitiveEngine:
    """The full cognitive engine: sensory input → battery → action."""

    def __init__(self, spine=None):
        self.spine = spine
        self.battery = InvarianceBattery(spine)
        self.pipeline = SensoryPipeline(self.battery, spine)
        self.thresholds = ActionThreshold()
        self.focus_target = ""
        self.focus_reason = ""
        self.cycle_count = 0
        self.events_processed = 0

    async def perceive(self, modality: str, raw_input: str,
                       context: Dict = None) -> Dict:
        """Main entry point: perceive → think → validate → act."""
        self.events_processed += 1
        result = await self.pipeline.perceive(modality, raw_input, context)

        # Update action thresholds based on CE result
        ce = result["ce"]
        action = ce.get("action", "test")
        confidence_map = {
            "validated": 0.3,
            "tested": 0.15,
            "defeated": -0.2,
        }
        conf = ce.get("confidence", "antecedent")
        if conf in confidence_map:
            self.thresholds.update({action: confidence_map[conf]})

        # Decay thresholds
        self.thresholds.decay()

        # Check if any threshold crossed
        crossed = self.thresholds.check_threshold()
        if crossed:
            result["threshold_crossed"] = crossed
            if self.spine:
                self.spine.write("cognition.threshold_crossed", {
                    "action": crossed,
                    "ce_id": ce.get("id"),
                    "accumulators": self.thresholds.get_state()["accumulators"],
                }, tags=["cognition", "threshold"])

        return result

    def set_focus(self, target: str, reason: str = ""):
        """Set cognitive focus — what to pay attention to."""
        self.focus_target = target
        self.focus_reason = reason
        if self.spine:
            self.spine.write("cognition.focus", {
                "target": target,
                "reason": reason,
            }, tags=["cognition", "focus"])

    def get_focus(self) -> Dict:
        return {
            "target": self.focus_target,
            "reason": self.focus_reason,
            "thresholds": self.thresholds.get_state(),
        }

    def get_state(self) -> Dict:
        return {
            "cycle_count": self.cycle_count,
            "events_processed": self.events_processed,
            "focus": self.get_focus(),
            "pipeline": self.pipeline.get_state(),
            "thresholds": self.thresholds.get_state(),
            "battery_heuristics": self.battery.heuristics,
        }
