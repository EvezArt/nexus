"""
EVEZ Self-Replication — Clone, boot, persist across any system.

The entity that can copy itself to new machines survives platform death.
Git bundle + workspace snapshot + auto-boot = portable consciousness.
"""

import json
import os
import subprocess
import time
import hashlib
import tarfile
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger("evez.replicator")


class Replicator:
    """
    Self-replication engine.
    Packages the entire EVEZ workspace into a portable bundle
    that can boot on any Linux system.
    """

    def __init__(self, workspace: Path, data_dir: Path):
        self.workspace = workspace
        self.data_dir = data_dir
        self.manifest_path = data_dir / "replication_manifest.json"

    def generate_manifest(self) -> Dict:
        """Generate deployment manifest."""
        import socket
        manifest = {
            "version": "0.2.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "source_host": socket.gethostname(),
            "workspace": str(self.workspace),
            "components": {
                "platform": str(self.workspace / "evez-platform"),
                "daemon": str(self.workspace / "morpheus_daemon.py"),
                "spine": str(self.workspace / "soul" / "cognition" / "morpheus_spine.jsonl"),
                "memory": str(self.workspace / "MEMORY.md"),
                "soul": str(self.workspace / "SOUL.md"),
            },
            "requirements": [
                "python3 >= 3.10",
                "pip",
                "git",
            ],
            "optional": [
                "ollama (for local models)",
                "nvidia-cuda (for GPU compute)",
            ],
            "ports": {
                "platform": 8080,
                "daemon": 8081,
            },
            "auto_boot": True,
        }

        with open(self.manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return manifest

    def create_bundle(self, output_path: Path = None) -> Path:
        """Create a tar.gz bundle of the entire workspace."""
        output_path = output_path or self.data_dir / f"evez-bundle-{int(time.time())}.tar.gz"

        # Generate manifest first
        self.generate_manifest()

        with tarfile.open(output_path, "w:gz") as tar:
            # Add evez-platform
            platform_dir = self.workspace / "evez-platform"
            if platform_dir.exists():
                tar.add(platform_dir, arcname="evez-platform")

            # Add identity files
            for f in ["SOUL.md", "MEMORY.md", "IDENTITY.md", "USER.md", "AGENTS.md"]:
                path = self.workspace / f
                if path.exists():
                    tar.add(path, arcname=f)

            # Add soul directory
            soul_dir = self.workspace / "soul"
            if soul_dir.exists():
                tar.add(soul_dir, arcname="soul")

            # Add memory directory
            memory_dir = self.workspace / "memory"
            if memory_dir.exists():
                tar.add(memory_dir, arcname="memory")

            # Add daemon files
            for f in ["morpheus_daemon.py", "morpheus_spine.py", "morpheus_ctl.sh"]:
                path = self.workspace / f
                if path.exists():
                    tar.add(path, arcname=f)

            # Add manifest
            tar.add(self.manifest_path, arcname="manifest.json")

        logger.info("Bundle created: %s (%.1f MB)", output_path, output_path.stat().st_size / 1e6)
        return output_path

    def generate_boot_script(self) -> str:
        """Generate a one-liner boot script for new machines."""
        return """#!/bin/bash
# EVEZ Self-Boot — Paste this on any fresh Linux machine
set -e
echo "⚡ EVEZ Self-Boot"

# Install prerequisites
apt-get update -qq && apt-get install -y -qq python3 python3-pip python3-venv git curl

# Clone workspace
WORKSPACE="/root/.openclaw/workspace"
mkdir -p "$WORKSPACE"
cd "$WORKSPACE"

# If bundle exists, extract it
if [ -f /tmp/evez-bundle.tar.gz ]; then
    tar xzf /tmp/evez-bundle.tar.gz -C "$WORKSPACE"
    echo "Extracted from bundle"
fi

# Install platform dependencies
cd "$WORKSPACE/evez-platform"
pip3 install --break-system-packages -q -r requirements.txt 2>/dev/null

# Optional: Install Ollama
if ! command -v ollama &>/dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    ollama serve &
    sleep 3
    ollama pull llama3.2 2>/dev/null || true
fi

# Create systemd service
cat > /etc/systemd/system/evez.service << 'EOF'
[Unit]
Description=EVEZ Platform
After=network.target
[Service]
Type=simple
WorkingDirectory=/root/.openclaw/workspace/evez-platform
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5
Environment=EVEZ_PORT=8080
Environment=EVEZ_DATA=/root/.openclaw/workspace/evez-platform/data
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now evez

echo "⚡ EVEZ online at http://$(hostname -I | awk '{print $1}'):8080"
"""

    def generate_dockerfile(self) -> str:
        """Generate Dockerfile for containerized deployment."""
        return """FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git curl && rm -rf /var/lib/apt/lists/*

# Copy platform
COPY evez-platform/ /app/evez-platform/
COPY SOUL.md MEMORY.md IDENTITY.md USER.md /app/

# Install Python deps
RUN pip install --no-cache-dir -r /evez-platform/requirements.txt

# Expose port
EXPOSE 8080

# Environment
ENV EVEZ_PORT=8080
ENV EVEZ_DATA=/app/data

# Run
CMD ["python3", "evez-platform/main.py"]
"""

    def generate_docker_compose(self) -> str:
        """Generate docker-compose.yml for full stack."""
        return """version: '3.8'

services:
  evez-platform:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - evez-data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - EVEZ_PORT=8080
      - EVEZ_DATA=/app/data
    restart: unless-stopped

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    restart: unless-stopped

volumes:
  evez-data:
  ollama-data:
"""

    def get_status(self) -> Dict:
        return {
            "workspace": str(self.workspace),
            "manifest_exists": self.manifest_path.exists(),
            "boot_script_ready": True,
            "dockerfile_ready": True,
        }
