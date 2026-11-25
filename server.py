import asyncio
import json
import os
import socket
import time
import aiohttp
from aiohttp import web
from backend.db import init_db, load_state_snapshot, save_state_snapshot
from backend.notifier import send_iphone_alert
from backend.office_state import (
    AGENTS,
    BRAIN_STATE,
    ROOMS,
    TASKS,
    apply_agent_event,
    spawn_subagents,
)

CONNECTED_CLIENTS = set()

# Maps each department to its GitHub repo and workflow dispatch event
DEPARTMENT_DISPATCH = {
    "cliporbit": {
        "repo_env": "CLIPORBIT_REPO",
        "default_repo": "Dee2310/cliporbit-agents",
        "event": "run_cliporbit_batch",
    },
    "social": {
        "repo_env": "CLIPORBIT_REPO",
        "default_repo": "Dee2310/cliporbit-agents",
        "event": "approve_youtube_upload",
    },
    "paystack": {
        "repo_env": "PAYSTACK_REPO",
        "default_repo": "Dee2310/paystack-order-demo",
        "event": "run_paystack_audit",
    },
    "inbox": {
        "repo_env": "OUTREACH_REPO",
        "default_repo": "Dee2310/cliporbit-agents",
        "event": "run_outreach_batch",
    },
    "dev": {
        "repo_env": "HQ_REPO",
        "default_repo": "Dee2310/dee-agent-hq",
        "event": "run_dev_check",
    },
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


def verify_api_key(request) -> bool:
  secret = os.environ.get("AGENT_HQ_SECRET")
  if not secret:
    return True
  return request.headers.get("X-API-Key") == secret


def verify_pin(request) -> bool:
  required_pin = os.environ.get("HQ_PIN")
  if not required_pin:
    return True
  return request.headers.get("X-HQ-PIN") == required_pin


async def broadcast(payload: dict):
  if CONNECTED_CLIENTS:
    msg = json.dumps(payload)
    await asyncio.gather(
        *[ws.send_str(msg) for ws in CONNECTED_CLIENTS],
        return_exceptions=True,
    )


async def trigger_github_dispatch(
    repo: str, event_type: str, client_payload: dict
) -> tuple[bool, str]:
  github_token = os.environ.get("GITHUB_TOKEN")
  if not github_token:
    return False, "GITHUB_TOKEN not set on Render"

  url = f"https://api.github.com/repos/{repo}/dispatches"
  headers = {
      "Authorization": f"Bearer {github_token}",
      "Accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
  }
  body = {"event_type": event_type, "client_payload": client_payload}

  async with aiohttp.ClientSession() as session:
    async with session.post(url, headers=headers, json=body) as resp:
      if resp.status == 204:
        return True, f"Dispatched `{event_type}` to {repo}"
      err = await resp.text()
      return False, f"GitHub API ({resp.status}): {err}"


async def index_handler(request):
  return web.FileResponse("static/index.html")


async def webhook_handler(request):
  if not verify_api_key(request):
    return web.json_response({"error": "Unauthorized API key"}, status=401)

  try:
    data = await request.json()
  except Exception:
    return web.json_response({"error": "Invalid JSON"}, status=400)

  event_payload = apply_agent_event(data)
  asyncio.create_task(
      save_state_snapshot(ROOMS, AGENTS, TASKS, BRAIN_STATE)
  )

  if data.get("needs_approval"):
    asyncio.create_task(
        send_iphone_alert(
            data.get("task", "New Task Ready"),
            data.get("message", "Tap to review & approve in Agent HQ."),
        )
    )

  await broadcast(event_payload)
  return web.json_response({"status": "ok"})


async def command_handler(request):
  if not verify_pin(request):
    return web.json_response(
        {"error": "Invalid HQ PIN — tap the lock icon to enter your PIN."},
        status=403,
    )

  try:
    data = await request.json()
  except Exception:
    return web.json_response({"error": "Invalid JSON"}, status=400)

  prompt = data.get("prompt", "").strip()
  target = data.get("room", "cliporbit")  # Can be a room_id or "agent:<id>"
  if not prompt:
    return web.json_response({"error": "Enter a command first."}, status=400)

  # Check if user targeted a specific live agent (e.g. "agent:hunter_agent")
  target_agent = None
  if target.startswith("agent:"):
    ag_id = target.split(":", 1)[1]
    target_agent = AGENTS.get(ag_id)
    room_id = target_agent["room"] if target_agent else "cliporbit"
  else:
    room_id = target if target in ROOMS else "cliporbit"

  if target_agent:
    target_agent["state"] = "working"
    target_agent["progress"] = 5
    target_agent["task"] = prompt
    TASKS.insert(
        0,
        {
            "id": f"tsk_{int(time.time() * 1000) % 100000}",
            "title": prompt,
            "room": room_id,
            "agent": target_agent["name"],
            "status": "running",
            "progress": 5,
        },
    )
    spawn_payload = {
        "type": "AGENT_UPDATE",
        "agent": target_agent,
        "room": ROOMS[room_id],
        "tasks": TASKS[:25],
        "brain": BRAIN_STATE,
    }
    actor_label = target_agent["name"]
  else:
    spawn_payload = spawn_subagents(room_id, prompt)
    actor_label = ROOMS[room_id]["name"]

  # Trigger real GitHub Actions repository_dispatch
  route = DEPARTMENT_DISPATCH.get(room_id)
  dispatch_note = "Queued locally"
  triggered = False
  if route:
    repo = os.environ.get(route["repo_env"], route["default_repo"])
    triggered, detail = await trigger_github_dispatch(
        repo,
        route["event"],
        {
            "prompt": prompt,
            "room": room_id,
            "agent_id": target_agent["id"] if target_agent else "",
        },
    )
    dispatch_note = detail

  BRAIN_STATE["notes_count"] += 1
  BRAIN_STATE["recent_memories"].insert(
      0,
      {
          "id": f"mem_{int(time.time() * 1000)}",
          "source": actor_label,
          "text": f"Dee Dispatched: '{prompt}' ({dispatch_note})",
      },
  )

  asyncio.create_task(
      save_state_snapshot(ROOMS, AGENTS, TASKS, BRAIN_STATE)
  )
  await broadcast(spawn_payload)

  return web.json_response({
      "status": "ok",
      "triggered": triggered,
      "message": f"Sent to {actor_label}: {dispatch_note}",
  })


async def approve_task_handler(request):
  if not verify_pin(request):
    return web.json_response({"error": "Invalid HQ PIN"}, status=403)

  data = await request.json()
  task_id = data.get("task_id")

  target_task = next((t for t in TASKS if t["id"] == task_id), None)
  if not target_task:
    return web.json_response({"error": "Task not found"}, status=404)

  room_id = target_task.get("room", "social")
  route = DEPARTMENT_DISPATCH.get(
      room_id,
      {
          "repo_env": "CLIPORBIT_REPO",
          "default_repo": "Dee2310/cliporbit-agents",
          "event": "approve_youtube_upload",
      },
  )
  repo = os.environ.get(route["repo_env"], route["default_repo"])

  triggered, status_msg = await trigger_github_dispatch(
      repo,
      "approve_youtube_upload" if room_id in ("social", "cliporbit") else route["event"],
      {
          "task_id": target_task["id"],
          "title": target_task["title"],
          "video_id": target_task.get("video_id", ""),
          "clip_path": target_task.get("clip_path", ""),
      },
  )

  target_task["status"] = "running" if triggered else "waiting"
  target_task["progress"] = 10 if triggered else 0
  target_task["time"] = "Dispatched"

  BRAIN_STATE["notes_count"] += 1
  BRAIN_STATE["recent_memories"].insert(
      0,
      {
          "id": f"mem_{int(time.time() * 1000)}",
          "source": ROOMS.get(room_id, {}).get("name", "Agent HQ"),
          "text": f"Approved: {target_task['title']} -> {status_msg}",
      },
  )

  asyncio.create_task(
      save_state_snapshot(ROOMS, AGENTS, TASKS, BRAIN_STATE)
  )
  await broadcast({
      "type": "TASKS_SYNC",
      "tasks": TASKS,
      "brain": BRAIN_STATE,
      "message": status_msg,
  })
  return web.json_response(
      {"status": "ok", "triggered": triggered, "detail": status_msg}
  )


async def ws_handler(request):
  ws = web.WebSocketResponse()
  await ws.prepare(request)
  CONNECTED_CLIENTS.add(ws)
  try:
    await ws.send_str(
        json.dumps({
            "type": "INITIAL_STATE",
            "rooms": ROOMS,
            "agents": AGENTS,
            "brain": BRAIN_STATE,
            "tasks": TASKS,
            "pin_required": bool(os.environ.get("HQ_PIN")),
        })
    )
    async for msg in ws:
      pass
  finally:
    CONNECTED_CLIENTS.discard(ws)
  return ws


async def on_startup(app):
  await init_db()
  saved = await load_state_snapshot()
  if saved.get("rooms"):
    for k, v in saved["rooms"].items():
      if k in ROOMS:
        ROOMS[k].update(v)
  if saved.get("agents"):
    AGENTS.update(saved["agents"])
  if saved.get("tasks"):
    TASKS.extend(saved["tasks"])
  if saved.get("brain"):
    BRAIN_STATE.update(saved["brain"])
  print(
      f"📦 Restored {len(AGENTS)} live agents and {len(TASKS)} tasks from Neon."
  )


app = web.Application()
app.on_startup.append(on_startup)
app.router.add_get("/", index_handler)
app.router.add_get("/ws", ws_handler)
app.router.add_post("/api/event", webhook_handler)
app.router.add_post("/api/command", command_handler)
app.router.add_post("/api/tasks/approve", approve_task_handler)
app.router.add_static("/static/", path="static", name="static")

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8000))
  local_ip = get_local_ip()
  print("🏢 Agent HQ — Persistent Multi-Business Command Center LIVE!")
  print(f"💻 Laptop URL: http://localhost:{port}")
  print(f"📱 iPhone URL: http://{local_ip}:{port}")
  web.run_app(app, host="0.0.0.0", port=port, print=None)