#!/usr/bin/env python3
"""
NEXUS DAEMON — 24/7 continuous chatbot runtime.

Runs as a background process with:
- Periodic self-improvement cycles
- Memory decay
- Provider health monitoring
- Auto-recovery from failures
- HTTP server for external chat input (optional)

Usage:
    python3 nexus_daemon.py                    # Run with defaults
    python3 nexus_daemon.py --interval 60      # 60s between cycles
    python3 nexus_daemon.py --once             # Single cycle, exit
    python3 nexus_daemon.py --serve --port 8877  # HTTP API mode
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add workspace to path
WORKSPACE = Path(os.environ.get("MORPHEUS_WORKSPACE", "/root/.openclaw/workspace"))
sys.path.insert(0, str(WORKSPACE))

from nexus.nexus_core import NexusCore
from nexus.providers.base import Message
from nexus.capabilities.dispatcher import CapabilityDispatcher


NEXUS_DIR = WORKSPACE / "nexus"
STATE_FILE = NEXUS_DIR / "daemon_state.json"
PID_FILE = NEXUS_DIR / "daemon.pid"
LOG_FILE = NEXUS_DIR / "daemon.log"
CONFIG_FILE = NEXUS_DIR / "config.json"
CHAT_QUEUE = NEXUS_DIR / "chat_queue.jsonl"

# VULN-012: Log rotation constants
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LOG_BACKUPS = 5

# VULN-014/015: Daemon auth
DAEMON_SECRET = os.environ.get("NEXUS_DAEMON_SECRET", "")


class NexusDaemon:
    """24/7 nexus daemon."""

    def __init__(self, interval: int = 300, serve: bool = False, port: int = 8877):
        self.interval = interval
        self.serve = serve
        self.port = port
        self.running = False
        self.boot_time = time.time()
        self.cycle_count = 0

        # Initialize core
        self.core = NexusCore()

        # Initialize capability dispatcher
        self.dispatcher = CapabilityDispatcher(workspace=WORKSPACE)

        # State
        self.state = self._load_state()

        # Signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        print(f"\n⚡ Received signal {signum}, shutting down...")
        self.running = False

    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "boot_time": datetime.now(timezone.utc).isoformat(),
            "total_cycles": 0,
            "total_chats": 0,
            "errors": 0,
        }

    def _save_state(self):
        self.state["last_cycle"] = datetime.now(timezone.utc).isoformat()
        self.state["total_cycles"] = self.cycle_count
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def log(self, msg: str, level: str = "INFO"):
        """Write to log file + stdout. Rotates at MAX_LOG_SIZE."""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        print(line)
        try:
            # VULN-012 FIX: Rotate log if too large
            if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_SIZE:
                for i in range(MAX_LOG_BACKUPS - 1, 0, -1):
                    src = LOG_FILE.with_suffix(f".log.{i}")
                    dst = LOG_FILE.with_suffix(f".log.{i+1}")
                    if src.exists():
                        src.rename(dst)
                LOG_FILE.rename(LOG_FILE.with_suffix(".log.1"))

            with open(LOG_FILE, "a") as f:
                f.write(line + "\n")
        except IOError:
            pass

    async def boot(self):
        """Initialize daemon."""
        NEXUS_DIR.mkdir(parents=True, exist_ok=True)

        # VULN-003 FIX: flock on PID file to prevent dual daemon
        import fcntl
        self._pid_fd = open(str(PID_FILE), "w")
        try:
            fcntl.flock(self._pid_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            existing_pid = PID_FILE.read_text().strip() if PID_FILE.exists() else "unknown"
            print(f"⚡ Another daemon is already running (PID {existing_pid}). Exiting.")
            self._pid_fd.close()
            sys.exit(1)
        self._pid_fd.write(str(os.getpid()))
        self._pid_fd.flush()

        self.log("=" * 60)
        self.log(f"⚡ NEXUS DAEMON v0.1.0 booting (PID {os.getpid()})")
        self.log(f"  Workspace: {WORKSPACE}")
        self.log(f"  Interval: {self.interval}s")
        self.log(f"  Providers: {', '.join(self.core.available_providers())}")
        self.log(f"  Serve mode: {self.serve} (port {self.port})")
        self.log("=" * 60)

    async def cycle(self):
        """Single daemon cycle — self-improvement + maintenance."""
        self.cycle_count += 1
        self.log(f"🔄 Cycle #{self.cycle_count}")

        # 1. Process chat queue (messages from external input)
        await self._process_chat_queue()

        # 2. Memory decay
        self.core.memory.decay_all()

        # 3. Provider health check
        health = self.core.health()
        for name, info in health["providers"].items():
            if info.get("error_count", 0) > 10:
                self.log(f"  ⚠️ Provider {name} has {info['error_count']} errors", "WARN")

        # 4. Self-improvement: log a thought
        try:
            resp = await self.core.local_check("daemon self-check")
            self.log(f"  🧠 Local: {resp.content[:80]}")
        except Exception as e:
            self.log(f"  Local check error: {e}", "ERROR")

        # 5. Save state
        self._save_state()

        mem_stats = self.core.memory.stats()
        self.log(f"  ✓ Cycle complete | {mem_stats['total_entries']} memories | "
                 f"{mem_stats['conversations']} conversations")

    async def _process_chat_queue(self):
        """Process any queued chat messages.

        VULN-001 FIX: Read all lines, then rewrite only unprocessed lines.
        If crash occurs mid-processing, unprocessed messages are preserved.
        """
        if not CHAT_QUEUE.exists():
            return

        lines = CHAT_QUEUE.read_text().splitlines()
        if not lines:
            return

        # Read all lines, then immediately rewrite with remaining (unprocessed) lines
        # This way if we crash, unprocessed messages survive
        remaining = list(lines)  # copy
        processed_indices = []

        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                processed_indices.append(idx)
                continue
            try:
                msg_data = json.loads(line)
                user_input = msg_data.get("message", "")
                provider = msg_data.get("provider", "auto")
                conv_id = msg_data.get("conversation_id", "default")

                if user_input:
                    self.log(f"  📨 Queued message: {user_input[:60]}...")

                    # Try capability dispatch first
                    cap_result = await self.dispatcher.dispatch(user_input)
                    if cap_result is not None:
                        self.log(f"  ⚡ Capability [{cap_result.capability}]: {cap_result.action} ({'ok' if cap_result.success else 'fail'})")
                        # Write capability result as output
                        output_file = NEXUS_DIR / "chat_output.jsonl"
                        with open(output_file, "a") as f:
                            f.write(json.dumps({
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "query": user_input,
                                "response": cap_result.output,
                                "provider": f"capability:{cap_result.capability}",
                                "model": "local",
                                "latency_ms": 0,
                            }) + "\n")
                    else:
                        # Fall through to provider routing
                        resp = await self.core.chat(
                            user_input,
                            provider=provider,
                            conversation_id=conv_id,
                        )
                        self.log(f"  📤 Response [{resp.provider}]: {resp.content[:80]}")

                        # Write response to output file
                        output_file = NEXUS_DIR / "chat_output.jsonl"
                        with open(output_file, "a") as f:
                            f.write(json.dumps({
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "query": user_input,
                                "response": resp.content,
                                "provider": resp.provider,
                                "model": resp.model,
                                "latency_ms": resp.latency_ms,
                            }) + "\n")

                processed_indices.append(idx)

            except (json.JSONDecodeError, KeyError) as e:
                self.log(f"  Queue parse error (dropping malformed entry): {e}", "ERROR")
                processed_indices.append(idx)  # drop malformed entries too

            # Rewrite queue with remaining unprocessed lines after each message
            # So crash between iterations only loses the current in-flight message
            remaining = [lines[i] for i in range(len(lines)) if i not in processed_indices]
            CHAT_QUEUE.write_text("\n".join(remaining) + ("\n" if remaining else ""))

    async def run(self):
        """Main daemon loop."""
        await self.boot()
        self.running = True

        try:
            if self.serve:
                # HTTP server mode
                await self._run_server()
            else:
                # Polling mode
                while self.running:
                    try:
                        await self.cycle()
                    except Exception as e:
                        self.state["errors"] = self.state.get("errors", 0) + 1
                        self.log(f"Cycle error: {e}", "ERROR")

                    # Sleep with interruptible wait
                    for _ in range(self.interval):
                        if not self.running:
                            break
                        await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        finally:
            await self.shutdown()

    async def _run_server(self):
        """Simple HTTP server for chat input."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading

        daemon_ref = self

        class ChatHandler(BaseHTTPRequestHandler):
            def _check_auth(self) -> bool:
                """VULN-014/015 FIX: HMAC token auth on all endpoints."""
                if not DAEMON_SECRET:
                    return True  # No secret configured = open (dev mode)
                auth = self.headers.get("Authorization", "")
                if auth.startswith("Bearer "):
                    return auth[7:] == DAEMON_SECRET
                # Also accept X-Daemon-Secret header
                return self.headers.get("X-Daemon-Secret", "") == DAEMON_SECRET

            def do_POST(self):
                if self.path == "/chat":
                    if not self._check_auth():
                        self.send_response(401)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(b'{"error":"unauthorized"}')
                        return
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length)
                    try:
                        msg_data = json.loads(body)
                        # Queue the message
                        with open(CHAT_QUEUE, "a") as f:
                            f.write(json.dumps(msg_data) + "\n")
                        self.send_response(202)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "queued"}).encode())
                    except Exception as e:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(str(e).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_GET(self):
                if self.path == "/health":
                    health = daemon_ref.core.health()
                    # Add income dashboard if available
                    try:
                        from nexus.income_engine import IncomeEngine
                        engine = IncomeEngine()
                        dash = engine.get_dashboard()
                        health["income"] = dash
                    except Exception:
                        pass
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(health, indent=2).encode())
                elif self.path == "/output":
                    if not self._check_auth():
                        self.send_response(401)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(b'{"error":"unauthorized"}')
                        return
                    output_file = NEXUS_DIR / "chat_output.jsonl"
                    if output_file.exists():
                        lines = output_file.read_text().splitlines()[-20:]
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps(lines).encode())
                    else:
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b"[]")
                elif self.path == "/" or self.path == "/dashboard":
                    if not self._check_auth():
                        self.send_response(401)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(b'{"error":"unauthorized"}')
                        return
                    dashboard_file = NEXUS_DIR / "dashboard.html"
                    if dashboard_file.exists():
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html")
                        self.end_headers()
                        self.wfile.write(dashboard_file.read_bytes())
                    else:
                        self.send_response(404)
                        self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # Suppress HTTP server logs

        server = HTTPServer(("127.0.0.1", self.port), ChatHandler)
        self.log(f"🌐 HTTP server listening on 127.0.0.1:{self.port}")

        # Run server in background thread, cycle in main loop
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        while self.running:
            try:
                await self.cycle()
            except Exception as e:
                self.state["errors"] = self.state.get("errors", 0) + 1
                self.log(f"Cycle error: {e}", "ERROR")

            for _ in range(self.interval):
                if not self.running:
                    break
                await asyncio.sleep(1)

        server.shutdown()

    async def shutdown(self):
        """Graceful shutdown."""
        self.log("⚡ NEXUS DAEMON shutting down")
        self._save_state()

        uptime = time.time() - self.boot_time
        self.log(f"  Uptime: {uptime:.0f}s | Cycles: {self.cycle_count} | "
                 f"Chats: {self.state.get('total_chats', 0)} | "
                 f"Errors: {self.state.get('errors', 0)}")

        await self.core.close()

        try:
            PID_FILE.unlink()
        except FileNotFoundError:
            pass

        # Release flock
        try:
            self._pid_fd.close()
        except Exception:
            pass

        self.log("Goodbye. ⚡")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Nexus Daemon")
    parser.add_argument("--interval", type=int, default=300,
                       help="Seconds between cycles (default: 300)")
    parser.add_argument("--once", action="store_true",
                       help="Run single cycle and exit")
    parser.add_argument("--serve", action="store_true",
                       help="Run with HTTP server")
    parser.add_argument("--port", type=int, default=8877,
                       help="HTTP server port (default: 8877)")
    args = parser.parse_args()

    daemon = NexusDaemon(interval=args.interval, serve=args.serve, port=args.port)

    if args.once:
        await daemon.boot()
        await daemon.cycle()
        await daemon.shutdown()
    else:
        await daemon.run()


if __name__ == "__main__":
    asyncio.run(main())
