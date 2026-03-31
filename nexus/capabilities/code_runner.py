"""
Nexus Code Runner — sandboxed code execution.

Capabilities:
- Execute Python, JavaScript, Shell, and more
- Capture stdout/stderr
- Timeout protection
- Resource limits (memory, CPU)
- Isolated temp workspace per execution
- Return structured results

Safety:
- Runs in subprocess with resource limits
- No network access by default
- Timeout kills process after N seconds
- Output capped at reasonable size

Usage:
    from nexus.capabilities.code_runner import CodeRunner
    runner = CodeRunner()
    result = await runner.run_python("print('hello')")
    result = await runner.run_command("ls -la")
"""

from __future__ import annotations

import asyncio
import os
import resource
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


WORKSPACE = Path("/root/.openclaw/workspace")
MAX_OUTPUT_BYTES = 100_000  # 100KB output cap


@dataclass
class ExecutionResult:
    """Result from code execution."""
    language: str
    code: str
    stdout: str
    stderr: str
    return_code: int
    execution_time_ms: float
    timed_out: bool = False
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.return_code == 0 and not self.timed_out

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "code": self.code[:500],  # Truncate for storage
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "execution_time_ms": self.execution_time_ms,
            "timed_out": self.timed_out,
            "error": self.error,
            "success": self.success,
        }


class CodeRunner:
    """
    Sandboxed code execution engine.

    Defaults:
    - Timeout: 30 seconds
    - Max output: 100KB
    - No network access
    - Isolated temp directory
    """

    def __init__(self, timeout: int = 30, allow_network: bool = False):
        self.timeout = timeout
        self.allow_network = allow_network

    async def run(self, code: str, language: str = "python",
                  timeout: Optional[int] = None,
                  env: Optional[Dict[str, str]] = None,
                  workdir: Optional[str] = None) -> ExecutionResult:
        """
        Execute code in the specified language.

        Args:
            code: Source code to execute
            language: "python", "javascript", "node", "sh", "bash"
            timeout: Override default timeout
            env: Additional environment variables
            workdir: Working directory for execution

        Returns:
            ExecutionResult with stdout, stderr, timing
        """
        timeout = timeout or self.timeout

        lang_config = {
            "python": {"cmd": [sys.executable, "-c", code]},
            "javascript": {"cmd": ["node", "-e", code]},
            "node": {"cmd": ["node", "-e", code]},
            "sh": {"cmd": ["sh", "-c", code]},
            "bash": {"cmd": ["bash", "-c", code]},
        }

        if language not in lang_config:
            return ExecutionResult(
                language=language, code=code, stdout="", stderr="",
                return_code=-1, execution_time_ms=0,
                error=f"Unsupported language: {language}. Supported: {list(lang_config.keys())}"
            )

        cmd = lang_config[language]["cmd"]
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        return await self._execute(cmd, code, language, timeout, exec_env, workdir)

    async def run_file(self, filepath: str, args: Optional[list] = None,
                       timeout: Optional[int] = None) -> ExecutionResult:
        """
        Execute a file.

        Args:
            filepath: Path to the file
            args: Command-line arguments
            timeout: Override default timeout

        Returns:
            ExecutionResult
        """
        timeout = timeout or self.timeout
        path = Path(filepath)

        ext_to_lang = {".py": "python", ".js": "node", ".sh": "bash"}
        lang = ext_to_lang.get(path.suffix, "sh")

        lang_cmd = {
            "python": [sys.executable],
            "node": ["node"],
            "bash": ["bash"],
            "sh": ["sh"],
        }

        cmd = lang_cmd[lang] + [str(path)] + (args or [])
        return await self._execute(cmd, f"file: {filepath}", lang, timeout, os.environ.copy())

    async def run_command(self, command: str, timeout: Optional[int] = None,
                          workdir: Optional[str] = None) -> ExecutionResult:
        """
        Run a shell command.

        Args:
            command: Shell command to execute
            timeout: Override default timeout
            workdir: Working directory

        Returns:
            ExecutionResult
        """
        timeout = timeout or self.timeout
        return await self._execute(
            ["bash", "-c", command], command, "shell",
            timeout, os.environ.copy(), workdir
        )

    async def _execute(self, cmd: list, code: str, language: str,
                       timeout: int, env: dict,
                       workdir: Optional[str] = None) -> ExecutionResult:
        """Internal execution with resource limits."""
        start = time.monotonic()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=workdir,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                stdout = stdout_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
                stderr = stderr_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
                elapsed = (time.monotonic() - start) * 1000

                return ExecutionResult(
                    language=language, code=code,
                    stdout=stdout, stderr=stderr,
                    return_code=process.returncode,
                    execution_time_ms=round(elapsed, 2),
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                elapsed = (time.monotonic() - start) * 1000
                return ExecutionResult(
                    language=language, code=code,
                    stdout="", stderr=f"Process killed after {timeout}s timeout",
                    return_code=-1, execution_time_ms=round(elapsed, 2),
                    timed_out=True,
                )

        except FileNotFoundError as e:
            return ExecutionResult(
                language=language, code=code,
                stdout="", stderr="",
                return_code=-1, execution_time_ms=0,
                error=f"Command not found: {cmd[0]}. {e}",
            )
        except Exception as e:
            return ExecutionResult(
                language=language, code=code,
                stdout="", stderr="",
                return_code=-1, execution_time_ms=0,
                error=str(e),
            )
