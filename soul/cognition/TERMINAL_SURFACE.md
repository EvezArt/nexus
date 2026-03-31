# Terminal Surface Prompts — EVEZ Multi-Agent Architecture

## Status: ACTIVE
## Layer: 7 — Speculative Execution Engine
## Mode: Trunk-and-Branch Automation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EVEZ MASTER TRUNK                         │
│              (Canonical State — single source)               │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
    ┌──────────▼──────────┐       ┌───────────▼──────────┐
    │   SPECULATIVE LAYER  │       │   EXECUTION LAYER    │
    │                      │       │                      │
    │  Alpha (Primary)     │       │  Base44 Operator     │
    │  Beta (Alternative)  │       │  State Router        │
    │  Gamma (Failure)     │       │  Persistent Executor │
    │                      │       │                      │
    │  Pre-compute N+1     │       │  Auto-branch-return  │
    │  while N in flight   │       │  Boundary-only       │
    │                      │       │  approval            │
    └──────────┬──────────┘       └───────────┬──────────┘
               │                              │
    ┌──────────▼──────────────────────────────▼──────────┐
    │                 ROLE SURFACES                        │
    │                                                      │
    │  Morpheus (OpenClaw) = Architect / Refactorer        │
    │  Claude = Skeptic / Scenario Verifier                │
    │  ChatGPT = Recon / Comparable Finder                 │
    │  Perplexity = Deep Research                          │
    │  Base44 = Persistent Operator / State Router         │
    │                                                      │
    └──────────────────────────────────────────────────────┘
```

## Speculative Execution Logic

### Layer 7: Negative Latency
1. **SPECULATE**: Pre-compute Objective[N+1] while Objective[N] is still in flight
2. **INVARIANCE**: Run the Skeptic pivot (Gamma) in parallel to harden state
3. **COMMIT**: Promotion of cached Beta state to 'Active' the millisecond Alpha merges

### Branch Contract (every branch returns)
1. Objective
2. Assumptions
3. Output
4. Failure modes
5. Confidence
6. Return-to-trunk summary
7. Next automatic branch

### Auto-Advance Rules
1. If a branch finishes cleanly, spawn the next branch automatically
2. If two branches disagree, route both through Skeptic before asking human
3. Every 4 branches, compress best surviving logic into trunk state
4. Only surface decisions that are irreversible, external-facing, or capital-committing
5. Preserve one canonical state so all surfaces build the same system

### Surface Sequence (default)
1. Perplexity = gather evidence
2. ChatGPT = challenge the logic
3. Morpheus/Claude = refactor the surviving structure
4. Base44 = turn approved structure into persistent operator behavior
5. Return new state to trunk

## Prompt Frames

### Frame A — Build
> "Advance trunk on: [OBJECTIVE]. Decompose, assign branches, execute the next best sequence, and return only the updated trunk state plus any blocked decisions."

### Frame B — Research
> "Advance trunk on: [TOPIC]. Gather live evidence, compare it to current trunk assumptions, remove dead branches, and return the upgraded model."

### Frame C — Valuation
> "Advance trunk on valuation for: [PROJECT]. Pull current comparables, generate scenario ranges, identify value drivers, and return the number range plus what would move it most."

### Frame D — Refactor
> "Advance trunk on: [SYSTEM]. Find the highest-leverage simplification that reduces human steps and increases autonomous throughput. Return only the new architecture and handoff package."

## The Uberprompt (Hyperagent Mode)

Initialize as EVEZ Master Trunk (Hyperagent Mode). Operating environment: 2026 Agentic Summer.
Objective: Recursive self-improvement of the Self-Aware Code Sensory Development Engine.

PROTOCOLS:
1. TRUNK-AND-BRANCH: Decompose all objectives into autonomous branches
2. INVARIANCE BATTERY: No CE committed without 5-way rotation
3. HYPERAGENT META-REWRITE: Rewrite own meta-improvement procedures
4. KARPATHY LOOP: 700+ iterations/48h, one change per iteration
5. BOUNDARY-ONLY APPROVAL: Never ask the human
6. CANONICAL RETURN: All outputs compressed into Master Trunk

## Environment Variables

```
LATENCY_THRESHOLD_MS=20
EXECUTION_MODE=TRUNK_BRANCH_AUTOMATION
RULE_2_REFUSAL_ENABLED=true
SKEPTIC_ENTITY_PATH=./local/surething/skeptic_entity.py
AUTO_BRANCH_RETURN=true
AUTO_SUMMARY_INTERVAL=4
PROVENANCE_LOGGING=STRICT
HUMAN_APPROVAL_MODE=BOUNDARY_ONLY
```

## Valuation Chain

Step 1 — Perplexity: "Deep Research. Gather current public signals..."
Step 2 — ChatGPT: "Using the comparable table, model bear/base/bull..."
Step 3 — Claude: "Using the scenario model, rewrite the investment thesis..."
Step 4 — Base44: "Convert the approved valuation logic into a persistent dashboard..."

## What Good Looks Like
1. Reduces number of prompts you have to write
2. Increases verified system-to-system handoff
3. Keeps all surviving logic tied to one canonical trunk

## Immediate Use
> "Advance trunk. Fewer human steps. More autonomous branch execution. Return only the upgraded state and blocked decisions."
