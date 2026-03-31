# NEXUS on Cloudflare Workers — edge-deployed AI API

Deploy nexus as a Cloudflare Worker for global edge distribution.

## Setup

```bash
# Install wrangler
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Deploy
wrangler deploy
```

## wrangler.toml

```toml
name = "nexus-api"
main = "worker.js"
compatibility_date = "2024-01-01"

[vars]
NEXUS_VERSION = "0.1.0"

[[kv_namespaces]]
binding = "NEXUS_MEMORY"
id = "your-kv-namespace-id"

[[d1_databases]]
binding = "NEXUS_DB"
database_name = "nexus"
database_id = "your-d1-database-id"
```

## worker.js (Minimal Edge API)

```javascript
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'ok',
        version: env.NEXUS_VERSION,
        edge: true,
        region: request.cf?.colo || 'unknown',
      }), {
        headers: { 'Content-Type': 'application/json' },
      });
    }
    
    // Chat endpoint
    if (url.pathname === '/chat' && request.method === 'POST') {
      const body = await request.json();
      
      // Store in KV
      const taskId = crypto.randomUUID();
      await env.NEXUS_MEMORY.put(`task:${taskId}`, JSON.stringify({
        message: body.message,
        provider: body.provider || 'auto',
        created: new Date().toISOString(),
        status: 'queued',
      }));
      
      return new Response(JSON.stringify({
        id: taskId,
        status: 'queued',
        message: 'Task submitted to edge queue',
      }), {
        headers: { 'Content-Type': 'application/json' },
        status: 201,
      });
    }
    
    // Dashboard
    if (url.pathname === '/' || url.pathname === '/dashboard') {
      return new Response(DASHBOARD_HTML, {
        headers: { 'Content-Type': 'text/html' },
      });
    }
    
    return new Response('Not Found', { status: 404 });
  },
};

const DASHBOARD_HTML = `<!DOCTYPE html>
<html><head><title>NEXUS Edge</title></head>
<body style="background:#0a0a0f;color:#e0e0e0;font-family:monospace;padding:2rem">
<h1 style="color:#ffd700">⚡ NEXUS Edge</h1>
<p>Deployed on Cloudflare Workers. Global edge distribution.</p>
</body></html>`;
```

## Benefits of Edge Deployment

- **Global latency**: <50ms from any continent
- **Zero cold starts**: Workers start instantly
- **Free tier**: 100K requests/day free
- **KV storage**: Persistent memory across edge locations
- **D1 database**: SQLite at the edge for structured data
- **Auto-scaling**: No server management

## Architecture

```
User → Cloudflare Edge (200+ locations)
      ├── Worker (API logic)
      ├── KV (memory/conversations)
      ├── D1 (task queue/revenue)
      └── R2 (file storage if needed)
```

This complements the VPS deployment:
- **VPS**: Full daemon, local cognition, 24/7 background tasks
- **Edge**: Fast API responses, global distribution, zero maintenance
