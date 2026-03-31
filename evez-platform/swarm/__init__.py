"""
EVEZ Compute Swarm — Infinite free compute orchestration.

Orchestrates: Oracle Free, Kaggle, GitHub Actions, Colab, BOINC, Vast.ai
"""

import json
import os
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger("evez.swarm")


class ComputeTier(Enum):
    EDGE = "edge"
    ORACLE = "oracle"
    GITHUB = "github"
    KAGGLE = "kaggle"
    COLAB = "colab"
    VAST = "vast"
    BOINC = "boinc"


@dataclass
class ComputeNode:
    id: str
    name: str
    tier: ComputeTier
    endpoint: str
    cpus: int = 0
    ram_gb: float = 0
    gpu: str = ""
    status: str = "offline"
    last_heartbeat: float = 0
    tasks_completed: int = 0
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d["tier"] = self.tier.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ComputeNode":
        d["tier"] = ComputeTier(d["tier"])
        return cls(**d)


@dataclass
class ComputeTask:
    id: str
    name: str
    payload: Dict[str, Any]
    priority: int = 5
    required_tier: ComputeTier = ComputeTier.EDGE
    requires_gpu: bool = False
    timeout_seconds: int = 300
    status: str = "pending"
    assigned_node: str = ""
    result: Optional[Dict] = None
    created: float = field(default_factory=time.time)
    completed: float = 0

    def to_dict(self):
        d = asdict(self)
        d["required_tier"] = self.required_tier.value
        return d


class ComputeSwarm:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.nodes: Dict[str, ComputeNode] = {}
        self.task_queue: List[ComputeTask] = []
        self.completed_tasks: List[ComputeTask] = []
        self._load_state()
        self._register_self()

    def _load_state(self):
        state_file = self.data_dir / "swarm_state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)
                for n in data.get("nodes", []):
                    node = ComputeNode.from_dict(n)
                    self.nodes[node.id] = node
            except (json.JSONDecodeError, IOError):
                pass

    def _save_state(self):
        state_file = self.data_dir / "swarm_state.json"
        with open(state_file, "w") as f:
            json.dump({
                "nodes": [n.to_dict() for n in self.nodes.values()],
                "pending_tasks": len(self.task_queue),
                "completed_tasks": len(self.completed_tasks),
                "updated": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2)

    def _register_self(self):
        node_id = hashlib.sha256(b"local-edge").hexdigest()[:12]
        node = ComputeNode(
            id=node_id, name="edge-local", tier=ComputeTier.EDGE,
            endpoint="local", cpus=os.cpu_count() or 1,
            ram_gb=self._get_ram_gb(), status="online",
            last_heartbeat=time.time(),
            capabilities=["shell", "python", "git", "file_io", "web"],
        )
        self.nodes[node_id] = node
        self._save_state()

    def _get_ram_gb(self) -> float:
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        return round(int(line.split()[1]) / 1024 / 1024, 1)
        except Exception:
            pass
        return 2.9

    def register_node(self, name: str, tier: ComputeTier, endpoint: str,
                      cpus: int = 0, ram_gb: float = 0, gpu: str = "",
                      capabilities: List[str] = None) -> str:
        node_id = hashlib.sha256(f"{name}:{endpoint}".encode()).hexdigest()[:12]
        node = ComputeNode(
            id=node_id, name=name, tier=tier, endpoint=endpoint,
            cpus=cpus, ram_gb=ram_gb, gpu=gpu,
            status="online", last_heartbeat=time.time(),
            capabilities=capabilities or [],
        )
        self.nodes[node_id] = node
        self._save_state()
        logger.info("Registered node: %s (%s)", name, tier.value)
        return node_id

    def submit_task(self, name: str, payload: Dict, priority: int = 5,
                    required_tier: ComputeTier = ComputeTier.EDGE,
                    requires_gpu: bool = False, timeout: int = 300) -> str:
        task_id = hashlib.sha256(f"{name}:{time.time()}".encode()).hexdigest()[:16]
        task = ComputeTask(
            id=task_id, name=name, payload=payload,
            priority=priority, required_tier=required_tier,
            requires_gpu=requires_gpu, timeout_seconds=timeout,
        )
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority)
        return task_id

    def get_best_node(self, task: ComputeTask) -> Optional[ComputeNode]:
        candidates = []
        for node in self.nodes.values():
            if node.status != "online":
                continue
            if task.requires_gpu and not node.gpu:
                continue
            score = 0
            tier_order = list(ComputeTier)
            score += (len(tier_order) - tier_order.index(node.tier)) * 10
            score += node.cpus * 2 + node.ram_gb
            if node.gpu:
                score += 20
            if time.time() - node.last_heartbeat > 300:
                score -= 50
            candidates.append((score, node))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def get_status(self) -> Dict:
        online = [n for n in self.nodes.values() if n.status == "online"]
        return {
            "nodes_total": len(self.nodes),
            "nodes_online": len(online),
            "total_cpus": sum(n.cpus for n in online),
            "total_ram_gb": round(sum(n.ram_gb for n in online), 1),
            "gpus": [n.gpu for n in online if n.gpu],
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "nodes": [n.to_dict() for n in online],
        }


# ---------------------------------------------------------------------------
# Provisioner — generates deploy scripts for free compute providers
# ---------------------------------------------------------------------------

GHA_WORKFLOW = """# EVEZ Compute Swarm — GitHub Actions
name: EVEZ Swarm
on:
  schedule:
    - cron: '*/5 * * * *'
  workflow_dispatch:
  push:
    branches: [main]
jobs:
  compute-tick:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - name: System Info
        run: |
          echo "CPUs: $(nproc)"
          echo "RAM: $(free -h | awk '/Mem:/{print $2}')"
      - name: EVEZ Compute Tick
        run: |
          python3 -c "
          import json, time, os
          print(json.dumps({'ts': time.time(), 'cpus': os.cpu_count()}, indent=2))
          "
      - name: Report
        run: echo "Swarm heartbeat complete"
"""

ORACLE_INIT = """#!/bin/bash
set -e
echo "EVEZ Oracle Cloud Provisioner"
apt-get update && apt-get install -y python3 python3-pip git curl
cd /opt
git clone https://github.com/EvezArt/evez-platform.git 2>/dev/null || true
cd evez-platform
pip3 install --break-system-packages -r requirements.txt
cat > /etc/systemd/system/evez-platform.service << 'EOF'
[Unit]
Description=EVEZ Platform
After=network.target
[Service]
Type=simple
WorkingDirectory=/opt/evez-platform
ExecStart=/usr/bin/python3 main.py
Restart=always
Environment=EVEZ_PORT=8080
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now evez-platform
echo "EVEZ Oracle node online"
"""

KAGGLE_NOTEBOOK = """# EVEZ Kaggle GPU Notebook
!pip install torch transformers
import torch, json, time
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")

def run_sim():
    n = 10000
    pos = torch.randn(n, 3, device='cuda' if torch.cuda.is_available() else 'cpu')
    vel = torch.randn(n, 3, device=pos.device) * 0.1
    for i in range(1000):
        diff = pos.unsqueeze(0) - pos.unsqueeze(1)
        dist = torch.norm(diff, dim=2, keepdim=True) + 1e-6
        force = (diff / dist.pow(3)).sum(1)
        vel += force * 0.01
        pos += vel * 0.01
        if i % 100 == 0:
            print(f"Step {i}: E={0.5 * vel.pow(2).sum().item():.4f}")

run_sim()
print("Kaggle compute cycle complete")
"""

BOINC_CONFIG = """<?xml version="1.0"?>
<project>
  <name>evez-swarm</name>
  <long_name>EVEZ Cognitive Compute Swarm</long_name>
  <description>Volunteer compute for cognitive architecture research</description>
  <workunit>
    <name>evez_sim</name>
    <rsc_fpops_est>1e12</rsc_fpops_est>
    <rsc_memory_bound>500000000</rsc_memory_bound>
  </workunit>
</project>
"""

VASTAI_SCRIPT = """#!/bin/bash
set -e
echo "EVEZ Vast.ai GPU Provisioner"
cd /workspace
git clone https://github.com/EvezArt/evez-platform.git || true
cd evez-platform
pip install -r requirements.txt
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
sleep 3 && ollama pull llama3.2
export EVEZ_PORT=8080
python3 main.py &
echo "EVEZ Vast.ai node online"
"""


class SwarmProvisioner:
    SCRIPTS = {
        "github": GHA_WORKFLOW,
        "oracle": ORACLE_INIT,
        "kaggle": KAGGLE_NOTEBOOK,
        "boinc": BOINC_CONFIG,
        "vastai": VASTAI_SCRIPT,
    }

    def generate_gha_swarm(self, repo: str = "") -> str:
        return self.SCRIPTS["github"]

    def generate_oracle_init(self) -> str:
        return self.SCRIPTS["oracle"]

    def generate_kaggle_notebook(self) -> str:
        return self.SCRIPTS["kaggle"]

    def generate_boinc_config(self) -> str:
        return self.SCRIPTS["boinc"]

    def generate_vastai_script(self) -> str:
        return self.SCRIPTS["vastai"]

    def get_script(self, provider: str) -> Optional[str]:
        return self.SCRIPTS.get(provider)
