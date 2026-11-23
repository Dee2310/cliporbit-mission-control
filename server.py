import asyncio
import json
import os
import socket
import time
import aiohttp
from aiohttp import web
from backend.office_state import (
    AGENTS,
    BRAIN_STATE,
    ROOMS,
    TASKS,
    apply_agent_event,
    spawn_subagents,
)

CONNECTED_CLIENTS = set()


def get_local_ip():
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip
  except Exception:
    return "127.0.0.1"


async def broadcast(payload: dict):
  if CONNECTED_CLIENTS:
    msg = json.dumps(payload)
    await asyncio.gather(
        *[ws.send_str(msg) for ws in CONNECTED_CLIENTS],
        return_exceptions=True,
    )


async def index_handler(request):
  return web.FileResponse("static/index.html")


async def webhook_handler(request):
  try:
    data = await request.json()
  except Exception:
    return web.json_response({"error": "Invalid JSON"}, status=400)

  event_payload = apply_agent_event(data)
  await broadcast(event_payload)
  return web.json_response({"status": "ok"})


async def command_handler(request):
  try:
    data = await request.json()
  except Exception:
    return web.json_response({"error": "Invalid JSON"}, status=400)

  prompt = data.get("prompt", "").strip()
  room_id = data.get("room", "cliporbit")
  spawn_payload = spawn_subagents(room_id, prompt)
  await broadcast(spawn_payload)
  return web.json_response(
      {"status": "spawned", "count": len(spawn_payload["subagents"])}
  )


async def trigger_github_publish(task_payload: dict) -> tuple[bool, str]:
  """Fires a repository_dispatch event to your ClipOrbit GitHub repo."""
  github_token = os.environ.get("GITHUB_TOKEN")
  repo = os.environ.get("CLIPORBIT_REPO", "Dee2310/cliporbit")

  if not github_token:
    return False, "GITHUB_TOKEN not configured on Render"

  url = f"https://api.github.com/repos/{repo}/dispatches"
  headers = {
      "Authorization": f"Bearer {github_token}",
      "Accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
  }
  body = {"event_type": "approve_youtube_upload", "client_payload": task_payload}

  async with aiohttp.ClientSession() as session:
    async with session.post(url, headers=headers, json=body) as resp:
      if resp.status == 204:
        return True, "GitHub Actions upload workflow triggered!"
      err_text = await resp.text()
      return False, f"GitHub API error ({resp.status}): {err_text}"


async def approve_task_handler(request):
  data = await request.json()
  task_id = data.get("task_id")

  target_task = None
  for t in TASKS:
    if t["id"] == task_id:
      target_task = t
      break

  if not target_task:
    return web.json_response({"error": "Task not found"}, status=404)

  triggered, status_msg = await trigger_github_publish({
      "task_id": target_task["id"],
      "title": target_task["title"],
      "video_id": target_task.get("video_id", ""),
      "clip_path": target_task.get("clip_path", ""),
  })

  target_task["status"] = "running" if triggered else "waiting"
  target_task["progress"] = 10 if triggered else 0
  target_task["time"] = "Dispatched to GitHub"

  BRAIN_STATE["notes_count"] += 1
  BRAIN_STATE["recent_memories"].insert(
      0,
      {
          "id": f"mem_{int(time.time()*1000)}",
          "source": "Social & Publishing",
          "text": f"Approval dispatch: {status_msg} ({target_task['title']})",
      },
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
        })
    )
    async for msg in ws:
      pass
  finally:
    CONNECTED_CLIENTS.discard(ws)
  return ws


app = web.Application()
app.router.add_get("/", index_handler)
app.router.add_get("/ws", ws_handler)
app.router.add_post("/api/event", webhook_handler)
app.router.add_post("/api/command", command_handler)
app.router.add_post("/api/tasks/approve", approve_task_handler)
app.router.add_static("/static/", path="static", name="static")

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8000))
  local_ip = get_local_ip()
  print("🏢 Agent HQ — Universal Multi-Business Command Center LIVE!")
  print(f"💻 Laptop URL: http://localhost:{port}")
  print(f"📱 iPhone URL: http://{local_ip}:{port}")
  web.run_app(app, host="0.0.0.0", port=port, print=None)