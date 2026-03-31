"""
EVEZ MetaROM Bridge — Connect emulator cognition to the platform.

MetaROM trains from ROMs. This bridge feeds ROM-derived patterns
into the cognitive engine as a sensory modality.
"""

import json
import hashlib
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger("evez.metarom")


@dataclass
class ROMEvent:
    """A cognitive event derived from ROM emulation."""
    rom_name: str
    frame: int
    pc: int           # Program counter
    opcode: str
    registers: Dict[str, int]
    memory_reads: List[int]
    memory_writes: List[int]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "rom": self.rom_name,
            "frame": self.frame,
            "pc": self.pc,
            "opcode": self.opcode,
            "registers": self.registers,
            "reads": self.memory_reads[:10],
            "writes": self.memory_writes[:10],
            "ts": self.timestamp,
        }


class MetaROMBridge:
    """
    Bridge between MetaROM emulator output and EVEZ cognition.

    Converts emulation traces into cognitive events:
    - ROM execution patterns → text descriptions
    - Memory access patterns → market/network analogies
    - CPU state transitions → temporal patterns

    The emulator becomes a training ground for the cognitive engine.
    """

    def __init__(self, spine=None, rom_dir: Path = None):
        self.spine = spine
        self.rom_dir = rom_dir or Path("/root/.openclaw/workspace")
        self.traces: List[ROMEvent] = []
        self.patterns_found: int = 0

    def process_trace(self, event: ROMEvent) -> Dict:
        """Convert a ROM trace event into a cognitive input."""
        # Convert to text representation for the cognition engine
        text = self._trace_to_text(event)

        # Detect patterns
        pattern = self._detect_pattern(event)

        result = {
            "text": text,
            "pattern": pattern,
            "rom_event": event.to_dict(),
            "cognitive_input": f"[ROM:{event.rom_name}] Frame {event.frame}: {text}",
        }

        self.traces.append(event)
        if pattern:
            self.patterns_found += 1

        # Write to spine
        if self.spine:
            self.spine.write("metarom.trace", {
                "rom": event.rom_name,
                "frame": event.frame,
                "pattern": pattern,
            }, tags=["metarom", "trace"])

        return result

    def _trace_to_text(self, event: ROMEvent) -> str:
        """Convert ROM trace to natural language description."""
        parts = []

        # Describe the instruction
        if event.opcode.startswith("LD"):
            parts.append(f"Loading data into {event.opcode[3:]}")
        elif event.opcode.startswith("ST"):
            parts.append(f"Storing data from {event.opcode[3:]}")
        elif event.opcode.startswith("J"):
            parts.append(f"Jumping to address {event.pc:04x}")
        elif event.opcode.startswith("CALL"):
            parts.append(f"Calling subroutine at {event.pc:04x}")
        elif event.opcode == "NOP":
            parts.append("Idle cycle")
        elif event.opcode == "HALT":
            parts.append("Execution halted")
        else:
            parts.append(f"Executing {event.opcode}")

        # Describe memory activity
        if event.memory_reads:
            parts.append(f"Reading {len(event.memory_reads)} memory locations")
        if event.memory_writes:
            parts.append(f"Writing to {len(event.memory_writes)} memory locations")

        # Describe register state
        active_regs = {k: v for k, v in event.registers.items() if v != 0}
        if active_regs:
            reg_desc = ", ".join(f"{k}={v:02x}" for k, v in list(active_regs.items())[:4])
            parts.append(f"Registers: {reg_desc}")

        return ". ".join(parts)

    def _detect_pattern(self, event: ROMEvent) -> Optional[str]:
        """Detect interesting patterns in ROM execution."""
        # Tight loop detection
        if len(self.traces) > 2:
            recent_pcs = [t.pc for t in self.traces[-5:]]
            if len(set(recent_pcs)) <= 2:
                return "tight_loop"

        # Memory access pattern
        if len(event.memory_reads) > 5:
            reads_sorted = sorted(event.memory_reads)
            diffs = [reads_sorted[i+1] - reads_sorted[i] for i in range(len(reads_sorted)-1)]
            if len(set(diffs)) == 1:
                return f"sequential_read_stride_{diffs[0]}"

        # Register manipulation pattern
        non_zero_regs = sum(1 for v in event.registers.values() if v != 0)
        if non_zero_regs >= 4:
            return "multi_register_compute"

        return None

    def get_stats(self) -> Dict:
        return {
            "traces_processed": len(self.traces),
            "patterns_found": self.patterns_found,
            "rom_dir": str(self.rom_dir),
        }
