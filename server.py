import asyncio
import json
import os
import random
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
    "hunter_agent": {"id": "hunter_agent", "name": "Hunter Agent", "role": "Channel Discovery", "color": "#22d3ee", "state": "idle", "progress": 0, "task": "Standby", "station": "hub", "completed_count": 12},
    "scout_agent": {"id": "scout_agent", "name": "Scout Agent", "role": "Hook Extraction", "color": "#38bdf8", "state": "idle", "progress": 0, "task": "Standby", "station": "hub", "completed_count": 9},
    "editor_agent": {"id": "editor_agent", "name": "Editor Agent", "role": "9:16 Vertical Render", "color": "#f472b6", "state": "idle", "progress": 0, "task": "Standby", "station": "hub", "completed_count": 7},
    "analyst_agent": {"id": "analyst_agent", "name": "Analyst Agent", "role": "Retention & QA", "color": "#a78bfa", "state": "idle", "progress": 0, "task": "Standby", "station": "hub", "completed_count": 7},
    "publisher_agent": {"id": "publisher_agent", "name": "Publisher Agent", "role": "YouTube Upload", "color": "#fbbf24", "state": "idle", "progress": 0, "task": "Standby", "station": "hub", "completed_count": 6}
}

PIPELINE_TASKS = [
    ("hunter_agent", "hunter", "Scanning tech & business podcasts for viral hooks"),
    ("scout_agent", "hunter", "Scoring transcript timestamps for 45s Short"),
    ("editor_agent", "editor", "Rendering 1080x1920 vertical clip + captions"),
    ("analyst_agent", "analyst", "Verifying audio sync & 3-sec hook retention"),
    ("publisher_agent", "publisher", "Uploading Short & updating SQLite schedule")
]

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

async def cliporbit_simulator():
    """Simulates step-by-step progress until real ClipOrbit webhook events arrive."""
    await asyncio.sleep(2)
    while True:
        agent_id, station_key, task_desc = random.choice(PIPELINE_TASKS)
        agent = AGENTS[agent_id]
        target_coords = STATIONS[station_key]

        # 1. Moving to station
        agent.update({"state": "moving", "station": station_key, "task": f"Moving to {target_coords['name']}", "progress": 0})
        await broadcast({
            "event_id": f"evt_{int(time.time()*1000)}",
            "agent": agent,
            "target": target_coords,
            "message": f"Heading to {target_coords['name']}..."
        })
        await asyncio.sleep(2.2)

        # 2. Executing task with incremental progress updates (25% -> 60% -> 90%)
        for pct in [25, 60, 90]:
            agent.update({"state": "working", "task": task_desc, "progress": pct})
            await broadcast({
                "event_id": f"evt_{int(time.time()*1000)}",
                "agent": agent,
                "target": target_coords,
                "message": f"[{pct}%] {task_desc}"
            })
            await asyncio.sleep(1.3)

        # 3. Completed
        agent["completed_count"] += 1
        agent.update({"state": "idle", "task": "Completed & Verified", "progress": 100})
        await broadcast({
            "event_id": f"evt_{int(time.time()*1000)}",
            "agent": agent,
            "target": target_coords,
            "message": f"Finished: {task_desc}"
        })
        await asyncio.sleep(1.5)

# HTTP Route: Serve index.html
async def index_handler(request):
    return web.FileResponse("index.html")

# HTTP Webhook: Real ClipOrbit agents (GitHub Actions / local scripts) can POST updates here!
async def webhook_handler(request):
    data = await request.json()
    agent_id = data.get("agent_id", "hunter_agent")
    station_key = data.get("station", "hub")
    if agent_id in AGENTS:
        AGENTS[agent_id].update({
            "state": data.get("state", "working"),
            "task": data.get("task", "Running pipeline step"),
            "progress": data.get("progress", 50),
            "station": station_key
        })
        await broadcast({
            "event_id": f"evt_{int(time.time()*1000)}",
            "agent": AGENTS[agent_id],
            "target": STATIONS.get(station_key, STATIONS["hub"]),
            "message": data.get("message", AGENTS[agent_id]["task"])
        })
    return web.json_response({"status": "ok"})

# WebSocket Route
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

async def start_background_tasks(app):
    app["sim_task"] = asyncio.create_task(cliporbit_simulator())

async def cleanup_background_tasks(app):
    app["sim_task"].cancel()

app = web.Application()
app.router.add_get("/", index_handler)
app.router.add_get("/ws", ws_handler)
app.router.add_post("/api/event", webhook_handler)
app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    local_ip = get_local_ip()
    print(f"🎬 ClipOrbit Mission Control LIVE!")
    print(f"💻 Laptop URL: http://localhost:{port}")
    print(f"📱 iPhone URL: http://{local_ip}:{port}")
    web.run_app(app, host="0.0.0.0", port=port, print=None)