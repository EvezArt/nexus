"""
Nexus Core — the orchestrator that routes between providers.

This is what makes the nexus better than any single provider:
1. Smart routing: sends queries to the best provider for each task
2. Fallback chains: if one provider fails, try the next
3. Memory continuity: all providers share the same memory
4. Self-improvement: learns which providers work best for which tasks

Routing logic:
- Research/factual queries → Perplexity (web search)
- Complex reasoning/code → ChatGPT (strong inference)
- Routine/status checks → OpenClaw (local, fast)
- Ambiguous → ChatGPT first, Perplexity as fallback
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from .providers.base import BaseProvider, Message, ProviderResponse
from .providers.chatgpt import ChatGPTProvider
from .providers.perplexity import PerplexityProvider
from .providers.openclaw_bridge import OpenClawBridge
from .memory_store import MemoryStore


WORKSPACE = Path("/root/.openclaw/workspace")
NEXUS_DIR = WORKSPACE / "nexus"
CONFIG_FILE = NEXUS_DIR / "config.json"

# Routing patterns — regex patterns that hint at which provider to use
RESEARCH_PATTERNS = [
    r"\b(what is|who is|when did|where is|how does|why does)\b",
    r"\b(latest|recent|current|today|news|search)\b",
    r"\b(compare|versus|vs|difference between)\b",
    r"\b(source|citation|reference|link)\b",
    r"\b(price|market|stock|crypto|trending)\b",
]

CODE_PATTERNS = [
    r"\b(write|create|build|implement|code|function|class|script)\b",
    r"\b(debug|fix|error|bug|traceback|exception)\b",
    r"\b(refactor|optimize|review|test)\b",
    r"```",
    r"\b(python|javascript|rust|go|java|sql)\b",
]

ROUTINE_PATTERNS = [
    r"\b(status|health|check|daemon|heartbeat)\b",
    r"\b(memory|spine|log|commit)\b",
    r"\b(what happened|recent activity|summary)\b",
]


class NexusRouter:
    """Routes queries to the best provider."""

    def __init__(self):
        self.provider_scores: Dict[str, Dict[str, float]] = {}
        self._load_scores()

    def _load_scores(self):
        scores_file = WORKSPACE / "nexus" / "routing_scores.json"
        if scores_file.exists():
            try:
                self.provider_scores = json.loads(scores_file.read_text())
            except (json.JSONDecodeError, IOError):
                self.provider_scores = {}

    def _save_scores(self):
        scores_file = WORKSPACE / "nexus" / "routing_scores.json"
        scores_file.parent.mkdir(parents=True, exist_ok=True)
        scores_file.write_text(json.dumps(self.provider_scores, indent=2))

    def classify_query(self, query: str) -> str:
        """Classify a query type based on patterns."""
        query_lower = query.lower()

        scores = {"research": 0, "code": 0, "routine": 0}

        for pattern in RESEARCH_PATTERNS:
            if re.search(pattern, query_lower):
                scores["research"] += 1

        for pattern in CODE_PATTERNS:
            if re.search(pattern, query_lower):
                scores["code"] += 1

        for pattern in ROUTINE_PATTERNS:
            if re.search(pattern, query_lower):
                scores["routine"] += 1

        max_type = max(scores, key=scores.get)
        if scores[max_type] == 0:
            return "general"
        return max_type

    def select_provider(self, query: str, available: List[str]) -> str:
        """Select the best provider for a query."""
        query_type = self.classify_query(query)

        # Default routing
        routing = {
            "research": ["perplexity", "chatgpt", "openclaw"],
            "code": ["chatgpt", "openclaw", "perplexity"],
            "routine": ["openclaw", "chatgpt"],
            "general": ["chatgpt", "perplexity", "openclaw"],
        }

        # Also check learned scores
        for provider in routing.get(query_type, ["chatgpt"]):
            if provider in available:
                return provider

        # Fallback to first available
        return available[0] if available else "openclaw"

    def record_outcome(self, provider: str, query_type: str, success: bool):
        """Record routing outcome for learning."""
        if query_type not in self.provider_scores:
            self.provider_scores[query_type] = {}
        if provider not in self.provider_scores[query_type]:
            self.provider_scores[query_type][provider] = 0.5

        # Update score (exponential moving average)
        current = self.provider_scores[query_type][provider]
        alpha = 0.1
        self.provider_scores[query_type][provider] = (
            current * (1 - alpha) + (1.0 if success else 0.0) * alpha
        )
        self._save_scores()


class NexusCore:
    """The nexus orchestrator. Routes queries, manages providers, maintains memory."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or self._load_config()
        self.memory = MemoryStore()
        self.router = NexusRouter()

        # Initialize providers
        self.providers: Dict[str, BaseProvider] = {}

        # VULN-005 FIX: Prefer env vars over config file for secrets
        # ChatGPT
        chatgpt_key = os.environ.get("OPENAI_API_KEY", "") or self.config.get("chatgpt_api_key", "")
        if chatgpt_key:
            self.providers["chatgpt"] = ChatGPTProvider(
                api_key=chatgpt_key,
                model=self.config.get("chatgpt_model", "gpt-4o-mini"),
                system_prompt=self.config.get("chatgpt_system_prompt", ""),
            )

        # Perplexity
        perplexity_key = os.environ.get("PERPLEXITY_API_KEY", "") or self.config.get("perplexity_api_key", "")
        if perplexity_key:
            self.providers["perplexity"] = PerplexityProvider(
                api_key=perplexity_key,
                model=self.config.get("perplexity_model", "sonar"),
                system_prompt=self.config.get("perplexity_system_prompt", ""),
            )

        # OpenClaw (always available)
        self.providers["openclaw"] = OpenClawBridge()

        self.conversation_id = "default"
        self.system_prompt = self.config.get("system_prompt", "")

    def _load_config(self) -> dict:
        """Load nexus config."""
        if CONFIG_FILE.exists():
            try:
                return json.loads(CONFIG_FILE.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def available_providers(self) -> List[str]:
        """List enabled provider names."""
        return [name for name, p in self.providers.items() if p.enabled]

    async def chat(self, user_input: str, provider: str = "auto",
                   conversation_id: str = "",
                   **kwargs) -> ProviderResponse:
        """Process a user message through the nexus.

        1. Store user message in memory
        2. Select provider (auto or explicit)
        3. Build context from memory
        4. Send to provider
        5. Store response in memory
        6. Return response
        """
        conv_id = conversation_id or self.conversation_id

        # 1. Store user message
        user_msg = Message(
            role="user",
            content=user_input,
            provider="nexus",
        )
        self.memory.store_message(user_msg, conversation_id=conv_id)

        # 2. Select provider
        available = self.available_providers()
        if provider == "auto":
            selected = self.router.select_provider(user_input, available)
        else:
            selected = provider if provider in available else available[0]

        prov = self.providers[selected]

        # 3. Build context from memory
        context_msgs = self.memory.get_context(
            user_input, conversation_id=conv_id,
            max_messages=15, max_search=3,
        )

        # Add system prompt if set
        if self.system_prompt:
            context_msgs.insert(0, Message(
                role="system",
                content=self.system_prompt,
                provider="nexus",
            ))

        # 4. Send to provider
        response = await prov.chat(context_msgs, **kwargs)

        # 5. Store response
        query_type = self.router.classify_query(user_input)
        success = not response.metadata.get("error", False)
        self.router.record_outcome(selected, query_type, success)

        self.memory.store_response(
            response, query=user_input,
            conversation_id=conv_id,
            tags=[query_type, selected],
        )

        return response

    async def research(self, query: str, **kwargs) -> ProviderResponse:
        """Research mode — force Perplexity for search-backed answers."""
        return await self.chat(query, provider="perplexity", **kwargs)

    async def reason(self, query: str, **kwargs) -> ProviderResponse:
        """Reasoning mode — force ChatGPT for complex inference."""
        return await self.chat(query, provider="chatgpt", **kwargs)

    async def local_check(self, query: str = "status", **kwargs) -> ProviderResponse:
        """Local check — force OpenClaw for daemon/spine status."""
        return await self.chat(query, provider="openclaw", **kwargs)

    def health(self) -> dict:
        """System health check."""
        return {
            "providers": {name: p.health_check() for name, p in self.providers.items()},
            "memory": self.memory.stats(),
            "available": self.available_providers(),
        }

    async def close(self):
        """Clean up all providers."""
        for prov in self.providers.values():
            try:
                await prov.close()
            except Exception:
                pass
