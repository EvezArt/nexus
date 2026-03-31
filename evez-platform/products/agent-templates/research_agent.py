"""
EVEZ Research Agent Template — Free

Autonomous research agent that:
1. Searches the web
2. Synthesizes findings
3. Generates reports with citations
4. Stores results in memory

Deploy: python3 research_agent.py --topic "your research topic"
"""

import json
import sys
import time
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add parent to import EVEZ core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import EveZCore, Spine
from search import SearchEngine
from agent import ModelProvider


class ResearchAgent:
    """Autonomous research agent."""

    def __init__(self, workspace: Path = None):
        self.workspace = workspace or Path("/root/.openclaw/workspace/evez-platform")
        self.core = EveZCore(self.workspace / "data" / "research")
        self.models = ModelProvider()
        self.search = SearchEngine(self.models)

    async def research(self, topic: str, depth: int = 3) -> Dict:
        """
        Deep research on a topic.

        1. Search for initial sources
        2. Read and analyze top results
        3. Generate synthesis with citations
        4. Store in memory
        """
        print(f"🔬 Researching: {topic}")
        print(f"   Depth: {depth} rounds")
        print()

        findings = []
        all_sources = []

        for round_num in range(1, depth + 1):
            print(f"  Round {round_num}/{depth}...")

            # Vary the query for deeper research
            if round_num == 1:
                query = topic
            elif round_num == 2:
                query = f"{topic} latest developments 2026"
            else:
                query = f"{topic} expert analysis detailed"

            results = await self.search.search(query, max_results=5)
            all_sources.extend(results)

            for r in results:
                findings.append({
                    "round": round_num,
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                })
                print(f"    📄 {r.title[:60]}")

        # Synthesize
        print(f"\n  📝 Synthesizing {len(findings)} sources...")
        report = await self.search.research(topic, max_results=8)

        # Store in spine
        self.core.spine.write("research.complete", {
            "topic": topic,
            "sources_found": len(all_sources),
            "depth": depth,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, tags=["research", "agent"])

        # Store in memory
        self.core.memory.store(
            f"research_{topic[:50]}",
            report.get("answer", "")[:1000],
            source="research_agent",
            tags=["research", topic[:20]],
        )

        result = {
            "topic": topic,
            "depth": depth,
            "sources": len(all_sources),
            "answer": report.get("answer", ""),
            "citations": report.get("citations", []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        print(f"\n  ✅ Research complete: {len(all_sources)} sources analyzed")
        return result

    async def run(self, topic: str, depth: int = 3, output: str = None):
        """Run research and save results."""
        result = await self.research(topic, depth)

        # Save to file
        output_path = output or f"research_{int(time.time())}.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Saved to: {output_path}")

        # Print summary
        print(f"\n{'='*60}")
        print(f"RESEARCH REPORT: {topic}")
        print(f"{'='*60}")
        print(f"\n{result['answer'][:2000]}")
        if result['citations']:
            print(f"\n📚 Sources:")
            for i, c in enumerate(result['citations'][:10], 1):
                print(f"  [{i}] {c['title']}")
                print(f"      {c['url']}")

        return result


async def main():
    parser = argparse.ArgumentParser(description="EVEZ Research Agent")
    parser.add_argument("--topic", required=True, help="Research topic")
    parser.add_argument("--depth", type=int, default=3, help="Research depth (1-5)")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    agent = ResearchAgent()
    await agent.run(args.topic, args.depth, args.output)


if __name__ == "__main__":
    asyncio.run(main())
