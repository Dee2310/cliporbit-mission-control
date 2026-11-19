import asyncio
import json
import os
import socket
import time
from aiohttp import web

CONNECTED_CLIENTS = set()

STATIONS = {
    "hub": {"x": 0, "z": 0, "name": "Director Hub", "color": "#8b5cf6"},
    "hunter": {"x": -7, "z": -5, "name": "Hunter & Scout Bay", "color": "#06b6d4"},
    "editor": {"x": 7, "z": -5, "name": "Editor Render Studio", "color": "#ec4899"},
    "analyst": {"x": -6, "z": 6, "name": "Analyst & QA Lab", "color": "#f59e0b"},
    "publisher": {"x": 6, "z": 6, "name": "Shorts Broadcast Tower", "color": "#ef4444"}
}

AGENTS = {
    "hunter_agent": {"id": "hunter_agent", "name": "Hunter Agent", "role": "Channel Discovery", "color": "#22d3ee", "state": "idle", "progress": 0, "task": "Standby", "station": "hub", "completed_count": 0},
    "scout_agent": {"id": "scout_agent", "name": "Scout Agent", "role": "Hook Extraction", "color": "#38bdf8", "state": "idle", "progress": 0, "task": "Standby", "station": "hub", "completed_count": 0},
    "editor_agent": {"id": "editor_agent", "name": "Editor Agent", "role": "9:16 Vertical Render", "color": "#f472b6", "state": "idle", "progress": 0, "task": "Standby", "station": "hub", "completed_count": 0},
    "analyst_agent": {"id": "analyst_agent", "name": "Analyst Agent", "role": "Retention & QA", "color": "#a78bfa", "state": "idle", "progress": 0, "task": "Standby", "station": "hub", "completed_count": 0},
    "publisher_agent": {"id": "publisher_agent", "name": "Publisher Agent", "role": "YouTube Upload", "color": "#fbbf24", "state": "idle", "progress": 0, "task": "Standby", "station": "hub", "completed_count": 0}
}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

async def broadcast(event_data):
    if CONNECTED_CLIENTS:
        message = json.dumps(event_data)
        await asyncio.gather(*[ws.send_str(message) for ws in CONNECTED_CLIENTS], return_exceptions=True)

# HTTP Route: Serve index.html
async def index_handler(request):
    return web.FileResponse("index.html")

# HTTP Webhook: Real ClipOrbit agents POST live updates here
async def webhook_handler(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    agent_id = data.get("agent_id", "hunter_agent")
    station_key = data.get("station", "hub")
    state = data.get("state", "working")
    progress = int(data.get("progress", 50))
    task = data.get("task", "Running pipeline step")
    message = data.get("message", task)

    if agent_id in AGENTS:
        if progress >= 100 and state == "idle" and AGENTS[agent_id]["progress"] < 100:
            AGENTS[agent_id]["completed_count"] += 1

        AGENTS[agent_id].update({
            "state": state,
            "task": task,
            "progress": progress,
            "station": station_key
        })

        await broadcast({
            "event_id": f"evt_{int(time.time()*1000)}",
            "agent": AGENTS[agent_id],
            "target": STATIONS.get(station_key, STATIONS["hub"]),
            "message": message
        })

    return web.json_response({"status": "ok"})

# WebSocket Route: Streams updates to your iPhone & laptop
async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    CONNECTED_CLIENTS.add(ws)
    try:
        await ws.send_str(json.dumps({
            "type": "INITIAL_STATE",
            "stations": STATIONS,
            "agents": AGENTS
        }))
        async for msg in ws:
            pass
    finally:
        CONNECTED_CLIENTS.discard(ws)
    return ws

app = web.Application()
app.router.add_get("/", index_handler)
app.router.add_get("/ws", ws_handler)
app.router.add_post("/api/event", webhook_handler)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    local_ip = get_local_ip()
    print(f"🎬 ClipOrbit Mission Control LIVE (Production Mode)")
    print(f"💻 Laptop URL: http://localhost:{port}")
    print(f"📱 iPhone URL: http://{local_ip}:{port}")
    web.run_app(app, host="0.0.0.0", port=port, print=None)