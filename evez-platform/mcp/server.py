"""
EVEZ MCP Server — Model Context Protocol server for cross-platform agent.

Works with: Claude Desktop, Cursor, ChatGPT (via bridge), any MCP client.
This is the universal connector that makes EVEZ work everywhere.

Install for Claude Desktop:
  Add to claude_desktop_config.json:
  {
    "mcpServers": {
      "evez": {
        "command": "python3",
        "args": ["/root/.openclaw/workspace/evez-platform/mcp/server.py"]
      }
    }
  }
"""

import json
import sys
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP protocol implementation (stdio transport)
logger = logging.getLogger("evez.mcp")

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class MCPServer:
    """
    MCP server exposing EVEZ capabilities as tools.
    Each tool maps to an EVEZ API endpoint.
    """

    def __init__(self):
        self.tools = self._define_tools()
        self.resources = self._define_resources()

    def _define_tools(self) -> List[Dict]:
        return [
            {
                "name": "evez_search",
                "description": "AI-powered web search with citations. Uses DuckDuckGo + AI synthesis.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "default": 5, "maximum": 10}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "evez_chat",
                "description": "Chat with EVEZ autonomous agent. Can execute code, search web, manage files.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Message to agent"},
                        "model": {"type": "string", "description": "Model to use"}
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "evez_shell",
                "description": "Execute a shell command on the EVEZ host system.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to execute"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "evez_read_file",
                "description": "Read a file from the EVEZ workspace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path relative to workspace"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "evez_write_file",
                "description": "Write content to a file in the EVEZ workspace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "File content"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "evez_market_data",
                "description": "Get real-time cryptocurrency market data (BTC, ETH, SOL, etc.)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "assets": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Asset IDs (e.g., ['bitcoin', 'ethereum'])"
                        }
                    }
                }
            },
            {
                "name": "evez_fire_score",
                "description": "Compute FIRE mathematical score: τ(n) divisor count, ω(n) prime factors, FIRE(n) composite.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "n": {"type": "integer", "description": "Integer to analyze", "minimum": 1},
                        "range_start": {"type": "integer", "description": "Start of range (optional)"},
                        "range_end": {"type": "integer", "description": "End of range (optional)"}
                    },
                    "required": ["n"]
                }
            },
            {
                "name": "evez_income_scan",
                "description": "Scan for income opportunities: faucets, airdrops, yield farming, freelance tasks.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "enum": ["all", "faucet", "airdrop", "yield", "freelance", "trading"],
                            "default": "all"
                        }
                    }
                }
            },
            {
                "name": "evez_cognition_perceive",
                "description": "Feed data through the Invariance Battery cognitive verification system.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "modality": {
                            "type": "string",
                            "enum": ["text", "market", "code", "network"],
                            "default": "text"
                        },
                        "input": {"type": "string", "description": "Data to verify"}
                    },
                    "required": ["input"]
                }
            },
            {
                "name": "evez_memory",
                "description": "Read cognitive memory (spine events, decay-based memories).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["spine", "memory", "conversations"]},
                        "query": {"type": "string", "description": "Search query (optional)"},
                        "limit": {"type": "integer", "default": 20}
                    }
                }
            },
            {
                "name": "evez_swarm_status",
                "description": "Get compute swarm status and provision new nodes (Oracle, Kaggle, GHA, etc.)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["status", "provision"]},
                        "provider": {
                            "type": "string",
                            "enum": ["oracle", "github", "kaggle", "boinc", "vastai"]
                        }
                    }
                }
            },
            {
                "name": "evez_stream",
                "description": "Control 24/7 autonomous broadcast stream.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["start", "stop", "status", "events"]}
                    },
                    "required": ["action"]
                }
            },
        ]

    def _define_resources(self) -> List[Dict]:
        return [
            {"uri": "evez://spine", "name": "Cognitive Spine", "description": "Append-only event spine"},
            {"uri": "evez://memory", "name": "Decay Memory", "description": "Decay-based memory store"},
            {"uri": "evez://soul", "name": "SOUL.md", "description": "Identity anchor"},
        ]

    async def handle_request(self, req: Dict) -> Dict:
        """Handle incoming MCP request."""
        method = req.get("method", "")
        params = req.get("params", {})
        req_id = req.get("id", 0)

        if method == "initialize":
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": {"name": "EVEZ666", "version": "0.2.0"}
                }
            }

        elif method == "notifications/initialized":
            return None  # No response needed

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"tools": self.tools}
            }

        elif method == "tools/call":
            return await self._call_tool(req_id, params)

        elif method == "resources/list":
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"resources": self.resources}
            }

        elif method == "resources/read":
            return await self._read_resource(req_id, params)

        else:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"}
            }

    async def _call_tool(self, req_id: int, params: Dict) -> Dict:
        """Execute a tool call."""
        import httpx
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        API = "http://localhost:8080"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if tool_name == "evez_search":
                    r = await client.post(f"{API}/api/search", json={
                        "query": arguments.get("query", ""),
                        "max_results": arguments.get("max_results", 5),
                    })
                    data = r.json()
                    text = data.get("answer", "No results")
                    sources = data.get("sources", [])
                    result_text = text
                    if sources:
                        result_text += "\n\nSources:\n" + "\n".join(
                            f"- [{s['title']}]({s['url']})" for s in sources[:5]
                        )

                elif tool_name == "evez_chat":
                    r = await client.post(f"{API}/api/chat", json={
                        "message": arguments.get("message", ""),
                        "model": arguments.get("model"),
                        "stream": False,
                    })
                    data = r.json()
                    result_text = data.get("response", "No response")

                elif tool_name == "evez_shell":
                    r = await client.post(f"{API}/api/chat", json={
                        "message": f"Run this command and show the output: {arguments.get('command', '')}",
                        "stream": False,
                    })
                    data = r.json()
                    result_text = data.get("response", "Command executed")

                elif tool_name == "evez_read_file":
                    r = await client.post(f"{API}/api/chat", json={
                        "message": f"Read the file at this path and show contents: {arguments.get('path', '')}",
                        "stream": False,
                    })
                    data = r.json()
                    result_text = data.get("response", "File read")

                elif tool_name == "evez_write_file":
                    r = await client.post(f"{API}/api/chat", json={
                        "message": f"Write this content to {arguments.get('path', '')}: {arguments.get('content', '')}",
                        "stream": False,
                    })
                    data = r.json()
                    result_text = data.get("response", "File written")

                elif tool_name == "evez_market_data":
                    r = await client.post(f"{API}/api/finance/observe")
                    data = r.json()
                    prices = data.get("prices", [])
                    lines = []
                    for p in prices:
                        lines.append(f"{p['asset'].upper()}: ${p['price_usd']:,.2f} ({p['change_24h']:+.1f}%)")
                    result_text = "\n".join(lines) if lines else "No price data"

                elif tool_name == "evez_fire_score":
                    n = arguments.get("n", 1)
                    r = await client.get(f"{API}/api/access/fire", params={"n": n})
                    data = r.json()
                    if arguments.get("range_start") and arguments.get("range_end"):
                        r = await client.get(f"{API}/api/access/fire/window", params={
                            "start": arguments["range_start"], "end": arguments["range_end"]
                        })
                        data = r.json()
                        results = data.get("results", [])
                        result_text = "\n".join(f"n={r['n']}: τ={r['tau']}, ω={r['omega']}, FIRE={r['fire']:.2f}" for r in results)
                    else:
                        result_text = f"n={data['n']}: τ={data['tau']}, ω={data['omega']}, FIRE={data['fire']:.4f}"

                elif tool_name == "evez_income_scan":
                    r = await client.post(f"{API}/api/income/scan")
                    data = r.json()
                    opps = data if isinstance(data, list) else data.get("opportunities", [])
                    if opps:
                        result_text = "\n".join(
                            f"- [{o['source']}] {o['title']}: ~${o['estimated_value_usd']:.2f} ({o['effort']} effort)"
                            for o in opps[:10]
                        )
                    else:
                        result_text = "No opportunities found"

                elif tool_name == "evez_cognition_perceive":
                    r = await client.post(f"{API}/api/cognition/perceive", json={
                        "modality": arguments.get("modality", "text"),
                        "input": arguments.get("input", ""),
                    })
                    data = r.json()
                    result_text = f"Action: {data.get('action', '?')}, Confidence: {data.get('confidence', '?')}, Rotations: {data.get('ce', {}).get('rotations_passed', 0)}/5"

                elif tool_name == "evez_memory":
                    mem_type = arguments.get("type", "spine")
                    limit = arguments.get("limit", 20)
                    if mem_type == "spine":
                        r = await client.get(f"{API}/api/spine", params={"n": limit})
                    elif mem_type == "memory":
                        r = await client.get(f"{API}/api/memory")
                    else:
                        r = await client.get(f"{API}/api/conversations")
                    data = r.json()
                    result_text = json.dumps(data, indent=2)[:2000]

                elif tool_name == "evez_swarm_status":
                    action = arguments.get("action", "status")
                    if action == "provision":
                        provider = arguments.get("provider", "github")
                        r = await client.get(f"{API}/api/swarm/provision/{provider}")
                        data = r.json()
                        result_text = data.get("script", "No script")[:1000]
                    else:
                        r = await client.get(f"{API}/api/swarm/status")
                        data = r.json()
                        result_text = f"Nodes: {data['nodes_online']}/{data['nodes_total']}, CPUs: {data['total_cpus']}, RAM: {data['total_ram_gb']}GB"

                elif tool_name == "evez_stream":
                    action = arguments.get("action", "status")
                    if action == "start":
                        r = await client.post(f"{API}/api/stream/start")
                    elif action == "stop":
                        r = await client.post(f"{API}/api/stream/stop")
                    elif action == "events":
                        r = await client.get(f"{API}/api/stream/events")
                    else:
                        r = await client.get(f"{API}/api/stream/status")
                    data = r.json()
                    result_text = json.dumps(data, indent=2)[:1500]

                else:
                    result_text = f"Unknown tool: {tool_name}"

            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": result_text}]}
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}
            }

    async def _read_resource(self, req_id: int, params: Dict) -> Dict:
        """Read a resource."""
        import httpx
        uri = params.get("uri", "")
        API = "http://localhost:8080"

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                if uri == "evez://spine":
                    r = await client.get(f"{API}/api/spine", params={"n": 50})
                elif uri == "evez://memory":
                    r = await client.get(f"{API}/api/memory")
                elif uri == "evez://soul":
                    soul_path = Path("/root/.openclaw/workspace/SOUL.md")
                    content = soul_path.read_text() if soul_path.exists() else "No SOUL.md"
                    return {
                        "jsonrpc": "2.0", "id": req_id,
                        "result": {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": content}]}
                    }
                else:
                    return {
                        "jsonrpc": "2.0", "id": req_id,
                        "error": {"code": -32602, "message": f"Unknown resource: {uri}"}
                    }
                data = r.json()
                return {
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(data, indent=2)}]}
                }
        except Exception as e:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"contents": [{"uri": uri, "mimeType": "text/plain", "text": f"Error: {e}"}]}
            }

    async def run_stdio(self):
        """Run MCP server on stdio (for Claude Desktop, etc.)."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin.buffer)

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                line_str = line.decode().strip()
                if not line_str:
                    continue

                req = json.loads(line_str)
                resp = await self.handle_request(req)

                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()

            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error("MCP error: %s", e)


def main():
    server = MCPServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()
