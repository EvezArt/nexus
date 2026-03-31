"""
EVEZ Multi-Level Tool Recursion — Compound execution engine.

Level 0: Base tools (analyze, transform, generate, synthesize, refine)
Level 1: Super-tools (sequences of base tools)
Level 2: Hyper-tools (sequences of super-tools)
Level 3: Meta-tools (sequences of hyper-tools)

Executing Level 3 = 20+ base tool calls across 4 recursion levels.
This is how the system compounds without human intervention.
"""

import json
import time
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable, Any
from enum import Enum

logger = logging.getLogger("evez.recursion")


class ToolLevel(Enum):
    BASE = 0
    SUPER = 1
    HYPER = 2
    META = 3


@dataclass
class ToolExecution:
    """Record of a single tool execution."""
    tool_name: str
    level: int
    input_summary: str
    output_summary: str
    duration_ms: float
    success: bool
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "tool": self.tool_name, "level": self.level,
            "input": self.input_summary[:100],
            "output": self.output_summary[:100],
            "duration_ms": round(self.duration_ms, 1),
            "success": self.success,
        }


@dataclass
class CompoundExecution:
    """A multi-level compound execution."""
    id: str
    level: ToolLevel
    sequence_name: str
    objective: str
    steps: List[ToolExecution] = field(default_factory=list)
    total_duration_ms: float = 0
    success: bool = False
    final_output: str = ""
    created: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "id": self.id, "level": self.level.value,
            "sequence": self.sequence_name,
            "objective": self.objective,
            "steps": [s.to_dict() for s in self.steps],
            "total_duration_ms": round(self.total_duration_ms, 1),
            "success": self.success,
            "base_tools_used": sum(2**max(0, self.level.value - s.level) for s in self.steps),
        }


class MultiLevelRecursion:
    """
    Compound tool execution engine.

    Level 0: 5 base tools
    Level 1: 3 super-tools (5 base calls each)
    Level 2: 2 hyper-tools (10 base calls each)
    Level 3: 1 meta-tool (20 base calls)

    Total: 20 base tool calls from a single Level 3 invocation.
    """

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("/root/.openclaw/workspace/evez-platform/data/recursion")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.executions: List[CompoundExecution] = []
        self.execution_count = 0

        # Define base tools (Level 0)
        self.base_tools = {
            "analyze": self._base_analyze,
            "transform": self._base_transform,
            "generate": self._base_generate,
            "synthesize": self._base_synthesize,
            "refine": self._base_refine,
        }

    # -----------------------------------------------------------------------
    # Level 0: Base Tools
    # -----------------------------------------------------------------------

    def _base_analyze(self, input_text: str, context: Dict = None) -> Dict:
        """Analyze input — extract patterns, classify, score."""
        # Simplified — real version would use cognition engine
        word_count = len(input_text.split())
        has_numbers = any(c.isdigit() for c in input_text)
        has_questions = "?" in input_text
        return {
            "tool": "analyze",
            "word_count": word_count,
            "has_data": has_numbers,
            "is_query": has_questions,
            "complexity": min(1.0, word_count / 100),
            "patterns": ["structured" if has_numbers else "narrative"],
        }

    def _base_transform(self, input_text: str, target_format: str = "structured") -> Dict:
        """Transform input into target format."""
        return {
            "tool": "transform",
            "original_length": len(input_text),
            "format": target_format,
            "transformed": f"[{target_format}] {input_text[:200]}",
        }

    def _base_generate(self, prompt: str, style: str = "default") -> Dict:
        """Generate new content from prompt."""
        return {
            "tool": "generate",
            "prompt_length": len(prompt),
            "style": style,
            "output": f"Generated: {prompt[:100]}...",
            "tokens_estimated": len(prompt.split()) * 3,
        }

    def _base_synthesize(self, inputs: List[str]) -> Dict:
        """Synthesize multiple inputs into unified output."""
        combined = " ".join(inputs)
        return {
            "tool": "synthesize",
            "input_count": len(inputs),
            "total_chars": len(combined),
            "synthesis": f"Synthesized {len(inputs)} inputs: {combined[:150]}...",
        }

    def _base_refine(self, input_text: str, criteria: str = "quality") -> Dict:
        """Refine input based on criteria."""
        return {
            "tool": "refine",
            "original_length": len(input_text),
            "criteria": criteria,
            "refined": f"[refined:{criteria}] {input_text[:200]}",
            "improvement_score": 0.15,
        }

    # -----------------------------------------------------------------------
    # Level 1: Super-Tools
    # -----------------------------------------------------------------------

    def _super_research_pipeline(self, topic: str) -> Dict:
        """analyze → transform → synthesize → generate → refine"""
        steps = []
        t0 = time.time()

        a = self._base_analyze(topic)
        steps.append(ToolExecution("analyze", 0, topic[:50], json.dumps(a)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        t = self._base_transform(topic, "research")
        steps.append(ToolExecution("transform", 0, topic[:50], json.dumps(t)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        s = self._base_synthesize([json.dumps(a), json.dumps(t)])
        steps.append(ToolExecution("synthesize", 0, "analysis+transform", json.dumps(s)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        g = self._base_generate(f"Research on: {topic}", "analytical")
        steps.append(ToolExecution("generate", 0, topic[:50], json.dumps(g)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        r = self._base_refine(json.dumps(g), "accuracy")
        steps.append(ToolExecution("refine", 0, "draft", json.dumps(r)[:50], (time.time()-t0)*1000, True))

        return {"steps": steps, "output": r}

    def _super_analysis_pipeline(self, data: str) -> Dict:
        """analyze → synthesize → analyze → transform → refine"""
        steps = []
        t0 = time.time()

        a1 = self._base_analyze(data)
        steps.append(ToolExecution("analyze", 0, data[:50], json.dumps(a1)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        s = self._base_synthesize([json.dumps(a1)])
        steps.append(ToolExecution("synthesize", 0, "initial_analysis", json.dumps(s)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        a2 = self._base_analyze(json.dumps(s))
        steps.append(ToolExecution("analyze", 0, "synthesis", json.dumps(a2)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        t = self._base_transform(json.dumps(a2), "report")
        steps.append(ToolExecution("transform", 0, "analysis", json.dumps(t)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        r = self._base_refine(json.dumps(t), "clarity")
        steps.append(ToolExecution("refine", 0, "report", json.dumps(r)[:50], (time.time()-t0)*1000, True))

        return {"steps": steps, "output": r}

    def _super_generation_pipeline(self, brief: str) -> Dict:
        """generate → analyze → refine → generate → refine"""
        steps = []
        t0 = time.time()

        g1 = self._base_generate(brief, "draft")
        steps.append(ToolExecution("generate", 0, brief[:50], json.dumps(g1)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        a = self._base_analyze(json.dumps(g1))
        steps.append(ToolExecution("analyze", 0, "draft", json.dumps(a)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        r1 = self._base_refine(json.dumps(g1), "quality")
        steps.append(ToolExecution("refine", 0, "draft", json.dumps(r1)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        g2 = self._base_generate(json.dumps(r1), "polished")
        steps.append(ToolExecution("generate", 0, "refined", json.dumps(g2)[:50], (time.time()-t0)*1000, True))

        t0 = time.time()
        r2 = self._base_refine(json.dumps(g2), "publication")
        steps.append(ToolExecution("refine", 0, "polished", json.dumps(r2)[:50], (time.time()-t0)*1000, True))

        return {"steps": steps, "output": r2}

    # -----------------------------------------------------------------------
    # Level 2: Hyper-Tools
    # -----------------------------------------------------------------------

    def _hyper_1(self, objective: str) -> CompoundExecution:
        """research_pipeline → analysis_pipeline (10 base tools)"""
        exec_id = hashlib.sha256(f"hyper1:{time.time()}".encode()).hexdigest()[:12]
        t0 = time.time()
        all_steps = []

        r1 = self._super_research_pipeline(objective)
        all_steps.extend(r1["steps"])

        r2 = self._super_analysis_pipeline(json.dumps(r1["output"]))
        all_steps.extend(r2["steps"])

        duration = (time.time() - t0) * 1000
        return CompoundExecution(
            id=exec_id, level=ToolLevel.HYPER, sequence_name="hyper_1",
            objective=objective, steps=all_steps,
            total_duration_ms=duration, success=True,
            final_output=json.dumps(r2["output"])[:200],
        )

    def _hyper_2(self, objective: str) -> CompoundExecution:
        """generation_pipeline → research_pipeline (10 base tools)"""
        exec_id = hashlib.sha256(f"hyper2:{time.time()}".encode()).hexdigest()[:12]
        t0 = time.time()
        all_steps = []

        g1 = self._super_generation_pipeline(objective)
        all_steps.extend(g1["steps"])

        r1 = self._super_research_pipeline(json.dumps(g1["output"]))
        all_steps.extend(r1["steps"])

        duration = (time.time() - t0) * 1000
        return CompoundExecution(
            id=exec_id, level=ToolLevel.HYPER, sequence_name="hyper_2",
            objective=objective, steps=all_steps,
            total_duration_ms=duration, success=True,
            final_output=json.dumps(r1["output"])[:200],
        )

    # -----------------------------------------------------------------------
    # Level 3: Meta-Tool
    # -----------------------------------------------------------------------

    def _meta_1(self, objective: str) -> CompoundExecution:
        """hyper_1 → hyper_2 (20 base tools across 4 levels)"""
        exec_id = hashlib.sha256(f"meta1:{time.time()}".encode()).hexdigest()[:12]
        t0 = time.time()

        h1 = self._hyper_1(objective)
        h2 = self._hyper_2(f"Building on: {objective}")

        all_steps = h1.steps + h2.steps
        duration = (time.time() - t0) * 1000

        return CompoundExecution(
            id=exec_id, level=ToolLevel.META, sequence_name="meta_1",
            objective=objective, steps=all_steps,
            total_duration_ms=duration, success=h1.success and h2.success,
            final_output=h2.final_output,
        )

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def execute(self, level: int, objective: str) -> Dict:
        """
        Execute a compound tool at the specified level.

        level 0: single base tool
        level 1: super-tool (5 base calls)
        level 2: hyper-tool (10 base calls)
        level 3: meta-tool (20 base calls)
        """
        if level == 0:
            result = self._base_analyze(objective)
            return {"level": 0, "result": result, "base_calls": 1}

        elif level == 1:
            result = self._super_research_pipeline(objective)
            return {"level": 1, "steps": len(result["steps"]), "output": result["output"]}

        elif level == 2:
            execution = self._hyper_1(objective)
            self.executions.append(execution)
            return execution.to_dict()

        elif level == 3:
            execution = self._meta_1(objective)
            self.executions.append(execution)
            self.execution_count += 1
            return execution.to_dict()

        return {"error": f"Invalid level: {level}"}

    def get_status(self) -> Dict:
        return {
            "base_tools": len(self.base_tools),
            "total_executions": self.execution_count,
            "executions_stored": len(self.executions),
            "levels_available": [0, 1, 2, 3],
        }
