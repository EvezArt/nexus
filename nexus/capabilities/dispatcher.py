"""
Nexus Capability Dispatcher — routes chat messages to local capability modules
before falling through to provider routing.

This is what makes the nexus actually DO things instead of just chatting.

Detection order:
1. File operations (read, list, search, write files)
2. Code execution (run code, run commands)
3. Scheduler (set reminders, schedule tasks)
4. Fall through to provider routing
"""

from __future__ import annotations

import json
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, Any
from dataclasses import dataclass

from ..capabilities.code_runner import CodeRunner, ExecutionResult
from ..capabilities.file_manager import FileManager, FileInfo


@dataclass
class CapabilityResult:
    """Result from a capability dispatch."""
    capability: str
    action: str
    success: bool
    output: str
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CapabilityDispatcher:
    """Detects and dispatches capability-triggering messages."""

    def __init__(self, workspace: Path = None):
        self.workspace = workspace or Path("/root/.openclaw/workspace")
        self.code_runner = CodeRunner(workspace=self.workspace)
        self.file_manager = FileManager(root=self.workspace)

        # Pattern matchers (compiled once)
        self._patterns = self._compile_patterns()

    def _compile_patterns(self) -> list:
        """Compile dispatch patterns. Each is (compiled_regex, handler_method)."""
        patterns = [
            # Code execution
            (re.compile(r"^run\s+(python|py)\s*[:>]\s*(.+)", re.DOTALL | re.IGNORECASE),
             self._handle_run_python),
            (re.compile(r"^run\s+(bash|sh|shell|command|cmd)\s*[:>]\s*(.+)", re.DOTALL | re.IGNORECASE),
             self._handle_run_command),
            (re.compile(r"^run\s+this\s*[:>]\s*(.+)", re.DOTALL | re.IGNORECASE),
             self._handle_run_python),
            (re.compile(r"^execute\s*[:>]\s*(.+)", re.DOTALL | re.IGNORECASE),
             self._handle_run_python),
            # Code blocks
            (re.compile(r"^```(?:python|py)\s*\n(.+?)```$", re.DOTALL),
             self._handle_run_python_block),
            (re.compile(r"^```(?:bash|sh|shell)\s*\n(.+?)```$", re.DOTALL),
             self._handle_run_command_block),

            # File operations
            (re.compile(r"^list\s+(?:files?|dir|directory)\s*(?:in\s+)?(.+)?$", re.IGNORECASE),
             self._handle_list_files),
            (re.compile(r"^read\s+file\s+(.+)$", re.IGNORECASE),
             self._handle_read_file),
            (re.compile(r"^show\s+(?:me\s+)?(?:the\s+)?(?:file|contents?\s+of)\s+(.+)$", re.IGNORECASE),
             self._handle_read_file),
            (re.compile(r"^cat\s+(.+)$", re.IGNORECASE),
             self._handle_read_file),
            (re.compile(r"^search\s+(?:for\s+)?['\"](.+?)['\"](?:\s+in\s+(.+))?$", re.IGNORECASE),
             self._handle_search_content),
            (re.compile(r"^find\s+files?\s+(.+)$", re.IGNORECASE),
             self._handle_find_files),

            # System info
            (re.compile(r"^(?:what'?s|show)\s+(?:the\s+)?(?:system\s+)?(?:status|health|uptime)$", re.IGNORECASE),
             self._handle_system_status),
        ]
        return patterns

    async def dispatch(self, message: str) -> Optional[CapabilityResult]:
        """Try to dispatch a message to a capability. Returns None if no match."""
        message = message.strip()

        for pattern, handler in self._patterns:
            match = pattern.match(message)
            if match:
                try:
                    return await handler(match)
                except Exception as e:
                    return CapabilityResult(
                        capability="dispatcher",
                        action="error",
                        success=False,
                        output=f"Capability error: {e}",
                    )

        return None  # No capability match — fall through to provider

    # === Code Execution Handlers ===

    async def _handle_run_python(self, match) -> CapabilityResult:
        code = match.group(match.lastindex).strip()  # last captured group
        result = await self.code_runner.run_python(code)
        return self._format_execution_result("python", code, result)

    async def _handle_run_python_block(self, match) -> CapabilityResult:
        code = match.group(1).strip()
        result = await self.code_runner.run_python(code)
        return self._format_execution_result("python", code, result)

    async def _handle_run_command(self, match) -> CapabilityResult:
        cmd = match.group(match.lastindex).strip()
        result = await self.code_runner.run_command(cmd)
        return self._format_execution_result("bash", cmd, result)

    async def _handle_run_command_block(self, match) -> CapabilityResult:
        cmd = match.group(1).strip()
        result = await self.code_runner.run_command(cmd)
        return self._format_execution_result("bash", cmd, result)

    def _format_execution_result(self, lang: str, code: str, result: ExecutionResult) -> CapabilityResult:
        output_parts = []
        if result.stdout:
            output_parts.append(f"**stdout:**\n```\n{result.stdout[:2000]}\n```")
        if result.stderr:
            output_parts.append(f"**stderr:**\n```\n{result.stderr[:1000]}\n```")
        if result.timed_out:
            output_parts.append("⚠️ Execution timed out")
        output_parts.append(f"⏱️ {result.execution_time_ms:.0f}ms | exit {result.return_code}")

        return CapabilityResult(
            capability="code_runner",
            action=f"run_{lang}",
            success=result.success,
            output="\n\n".join(output_parts) if output_parts else "No output",
            metadata={"return_code": result.return_code, "timed_out": result.timed_out},
        )

    # === File Operation Handlers ===

    async def _handle_list_files(self, match) -> CapabilityResult:
        path_str = match.group(1) if match.lastindex >= 1 else "."
        if path_str:
            path_str = path_str.strip()
        path = self.workspace / path_str if path_str and not path_str.startswith("/") else Path(path_str or str(self.workspace))
        files = await self.file_manager.list_dir(path)

        if not files:
            return CapabilityResult("file_manager", "list", True, f"No files found in {path}")

        lines = [f"📁 **{path}** ({len(files)} items):"]
        for f in sorted(files, key=lambda x: (not x.is_dir, x.name)):
            icon = "📁" if f.is_dir else "📄"
            size = f" ({f.size:,} bytes)" if not f.is_dir else ""
            lines.append(f"  {icon} {f.name}{size}")

        return CapabilityResult("file_manager", "list", True, "\n".join(lines))

    async def _handle_read_file(self, match) -> CapabilityResult:
        path_str = match.group(1).strip()
        path = self.workspace / path_str if not path_str.startswith("/") else Path(path_str)
        content = await self.file_manager.read_file(path)

        if content is None:
            return CapabilityResult("file_manager", "read", False, f"File not found: {path_str}")

        # Truncate for display
        display = content[:5000]
        if len(content) > 5000:
            display += f"\n\n... ({len(content):,} bytes total, truncated)"

        return CapabilityResult(
            "file_manager", "read", True,
            f"📄 **{path.name}** ({len(content):,} bytes):\n```\n{display}\n```",
            {"size": len(content)},
        )

    async def _handle_search_content(self, match) -> CapabilityResult:
        query = match.group(1).strip()
        path_str = match.group(2).strip() if match.lastindex >= 2 and match.group(2) else "."
        base = self.workspace / path_str if not path_str.startswith("/") else Path(path_str)

        results = await self.file_manager.search(query=query, path=base)

        if not results:
            return CapabilityResult("file_manager", "search", True, f"No files containing '{query}' found")

        lines = [f"🔍 Found {len(results)} files containing '{query}':"]
        for r in results[:20]:
            lines.append(f"  📄 {r.path}")

        return CapabilityResult("file_manager", "search", True, "\n".join(lines))

    async def _handle_find_files(self, match) -> CapabilityResult:
        pattern = match.group(1).strip()
        results = await self.file_manager.search(pattern=pattern)

        if not results:
            return CapabilityResult("file_manager", "find", True, f"No files matching '{pattern}' found")

        lines = [f"🔍 Found {len(results)} files matching '{pattern}':"]
        for r in results[:30]:
            icon = "📁" if r.is_dir else "📄"
            lines.append(f"  {icon} {r.path}")

        return CapabilityResult("file_manager", "find", True, "\n".join(lines))

    # === System Handlers ===

    async def _handle_system_status(self, match) -> CapabilityResult:
        import os
        import time

        uptime_file = Path("/proc/uptime")
        load_file = Path("/proc/loadavg")
        mem_file = Path("/proc/meminfo")

        parts = ["⚡ **System Status:**"]

        if uptime_file.exists():
            uptime_s = float(uptime_file.read_text().split()[0])
            days = int(uptime_s // 86400)
            hours = int((uptime_s % 86400) // 3600)
            parts.append(f"  Uptime: {days}d {hours}h")

        if load_file.exists():
            load = load_file.read_text().split()[:3]
            parts.append(f"  Load: {load[0]} / {load[1]} / {load[2]}")

        if mem_file.exists():
            for line in mem_file.read_text().splitlines():
                if line.startswith("MemTotal:"):
                    total_kb = int(line.split()[1])
                    parts.append(f"  RAM: {total_kb // 1024} MB total")
                elif line.startswith("MemAvailable:"):
                    avail_kb = int(line.split()[1])
                    parts.append(f"  RAM available: {avail_kb // 1024} MB")

        disk = os.statvfs("/")
        disk_total = (disk.f_blocks * disk.f_frisk) // (1024**3) if hasattr(disk, 'f_frisk') else 0
        disk_free = (disk.f_bfree * disk.f_frisk) // (1024**3) if hasattr(disk, 'f_frisk') else 0
        if disk_total:
            parts.append(f"  Disk: {disk_free}GB free / {disk_total}GB total")

        return CapabilityResult("system", "status", True, "\n".join(parts))
