import time
import uuid

# Empty registries — populated 100% by real live agent telemetry
ROOMS = {
    "cliporbit": {
        "id": "cliporbit",
        "name": "ClipOrbit Creative",
        "business": "ClipOrbit Media",
        "x": 9.5,
        "z": 7.5,
        "color": "#8b5cf6",
        "floor": "#2e1065",
        "lead": "Unassigned",
        "stats": {"today": 0, "running": 0, "turnaround": "—"},
        "tools": [],
        "skills": [],
    },
    "paystack": {
        "id": "paystack",
        "name": "Paystack & B2B Ops",
        "business": "B2B Automation",
        "x": -9.5,
        "z": 7.5,
        "color": "#ef4444",
        "floor": "#450a0a",
        "lead": "Unassigned",
        "stats": {"today": 0, "running": 0, "turnaround": "—"},
        "tools": [],
        "skills": [],
    },
    "research": {
        "id": "research",
        "name": "Research & Intel",
        "business": "Universal",
        "x": 0.0,
        "z": -11.5,
        "color": "#3b82f6",
        "floor": "#172554",
        "lead": "Unassigned",
        "stats": {"today": 0, "running": 0, "turnaround": "—"},
        "tools": [],
        "skills": [],
    },
    "social": {
        "id": "social",
        "name": "Social & Publishing",
        "business": "ClipOrbit & Brand",
        "x": 12.0,
        "z": -2.0,
        "color": "#ec4899",
        "floor": "#500724",
        "lead": "Unassigned",
        "stats": {"today": 0, "running": 0, "turnaround": "—"},
        "tools": [],
        "skills": [],
    },
    "dev": {
        "id": "dev",
        "name": "Dev & Engineering",
        "business": "Apps & SaaS",
        "x": 9.5,
        "z": -9.5,
        "color": "#22c55e",
        "floor": "#052e16",
        "lead": "Unassigned",
        "stats": {"today": 0, "running": 0, "turnaround": "—"},
        "tools": [],
        "skills": [],
    },
    "inbox": {
        "id": "inbox",
        "name": "Inbox & Outreach",
        "business": "Client Acquisition",
        "x": -9.5,
        "z": -9.5,
        "color": "#f59e0b",
        "floor": "#451a03",
        "lead": "Unassigned",
        "stats": {"today": 0, "running": 0, "turnaround": "—"},
        "tools": [],
        "skills": [],
    },
    "scripts": {
        "id": "scripts",
        "name": "Scripts & Strategy",
        "business": "Content & Copy",
        "x": -12.0,
        "z": -2.0,
        "color": "#a855f7",
        "floor": "#3b0764",
        "lead": "Unassigned",
        "stats": {"today": 0, "running": 0, "turnaround": "—"},
        "tools": [],
        "skills": [],
    },
    "analytics": {
        "id": "analytics",
        "name": "Analytics & QA",
        "business": "All Businesses",
        "x": 0.0,
        "z": 11.5,
        "color": "#14b8a6",
        "floor": "#042f2e",
        "lead": "Unassigned",
        "stats": {"today": 0, "running": 0, "turnaround": "—"},
        "tools": [],
        "skills": [],
    },
}

AGENTS = {}

BRAIN_STATE = {
    "notes_count": 0,
    "recent_memories": [],
}

TASKS = []

STATION_MAP = {
    "hunter": "research",
    "scout": "research",
    "editor": "cliporbit",
    "analyst": "analytics",
    "publisher": "social",
    "hub": "cliporbit",
}


def apply_agent_event(data: dict) -> dict:
  agent_id = data.get("agent_id")
  if not agent_id:
    return {
        "type": "NOOP",
        "tasks": TASKS,
        "brain": BRAIN_STATE,
    }

  raw_room = data.get("room") or data.get("station", "cliporbit")
  room_id = STATION_MAP.get(raw_room, raw_room)
  if room_id not in ROOMS:
    room_id = "cliporbit"

  state = data.get("state", "working")
  progress = int(data.get("progress", 0))
  task = data.get("task", "")
  message = data.get("message", task)
  agent_name = data.get("agent_name", agent_id.replace("_", " ").title())

  # Dynamically register the agent on first live ping
  if agent_id not in AGENTS:
    AGENTS[agent_id] = {
        "id": agent_id,
        "name": agent_name,
        "room": room_id,
        "business": data.get("business", ROOMS[room_id]["business"]),
        "role": data.get("role", "Live Agent"),
        "color": data.get("color", ROOMS[room_id]["color"]),
        "state": state,
        "progress": progress,
        "task": task,
        "mission": data.get("mission", ""),
        "tools": data.get("tools", []),
        "rule": data.get("rule", ""),
        "is_subagent": bool(data.get("is_subagent", False)),
    }
    if ROOMS[room_id]["lead"] == "Unassigned":
      ROOMS[room_id]["lead"] = agent_name
  else:
    AGENTS[agent_id].update({
        "room": room_id,
        "state": state,
        "progress": progress,
        "task": task,
    })
    if "mission" in data:
      AGENTS[agent_id]["mission"] = data["mission"]
    if "tools" in data:
      AGENTS[agent_id]["tools"] = data["tools"]
    if "rule" in data:
      AGENTS[agent_id]["rule"] = data["rule"]

  # Register any connected tools reported live by the agent
  for tool_name in data.get("tools", []):
    if not any(t["name"] == tool_name for t in ROOMS[room_id]["tools"]):
      ROOMS[room_id]["tools"].append({"name": tool_name, "status": "Live"})

  # Handle approval queue vs running tasks
  if data.get("needs_approval"):
    TASKS.insert(
        0,
        {
            "id": f"tsk_{uuid.uuid4().hex[:6]}",
            "title": task,
            "room": room_id,
            "agent": AGENTS[agent_id]["name"],
            "status": "waiting",
            "action": "Approve",
            "video_id": data.get("video_id", ""),
            "clip_path": data.get("clip_path", ""),
        },
    )
  elif state == "working" and task:
    existing = next(
        (
            t
            for t in TASKS
            if t["agent"] == AGENTS[agent_id]["name"]
            and t["status"] == "running"
        ),
        None,
    )
    if existing:
      existing["title"] = task
      existing["progress"] = progress
    else:
      TASKS.insert(
          0,
          {
              "id": f"tsk_{uuid.uuid4().hex[:6]}",
              "title": task,
              "room": room_id,
              "agent": AGENTS[agent_id]["name"],
              "status": "running",
              "progress": progress,
          },
      )

  if progress >= 100 and state == "idle":
    ROOMS[room_id]["stats"]["today"] += 1
    for t in TASKS:
      if t["agent"] == AGENTS[agent_id]["name"] and t["status"] == "running":
        t["status"] = "done"
        t["time"] = "Just now"

    if message:
      BRAIN_STATE["notes_count"] += 1
      BRAIN_STATE["recent_memories"].insert(
          0,
          {
              "id": f"mem_{int(time.time() * 1000)}",
              "source": ROOMS[room_id]["name"],
              "text": f"{AGENTS[agent_id]['name']}: {message}",
          },
      )
      BRAIN_STATE["recent_memories"] = BRAIN_STATE["recent_memories"][:20]

  return {
      "type": "AGENT_UPDATE",
      "event_id": f"evt_{int(time.time() * 1000)}",
      "agent": AGENTS[agent_id],
      "room": ROOMS[room_id],
      "tasks": TASKS[:25],
      "brain": BRAIN_STATE,
      "message": message,
  }


def spawn_subagents(room_id: str, prompt: str) -> dict:
  if room_id not in ROOMS:
    room_id = "cliporbit"

  created_subs = []
  for idx in range(1, 4):
    sub_id = f"sub_{room_id}_{idx}_{uuid.uuid4().hex[:4]}"
    sub_agent = {
        "id": sub_id,
        "name": f"Sub-{idx} • {room_id[:4].upper()}",
        "room": room_id,
        "business": ROOMS[room_id]["business"],
        "role": "Parallel Sub-Agent",
        "color": ROOMS[room_id]["color"],
        "state": "working",
        "progress": 0,
        "task": prompt,
        "mission": prompt,
        "tools": [],
        "rule": "Requires Dee's approval for external actions.",
        "is_subagent": True,
        "slot": idx - 1,
    }
    AGENTS[sub_id] = sub_agent
    created_subs.append(sub_agent)
    TASKS.insert(
        0,
        {
            "id": f"tsk_{uuid.uuid4().hex[:6]}",
            "title": f"{sub_agent['name']}: {prompt}",
            "room": room_id,
            "agent": sub_agent["name"],
            "status": "running",
            "progress": 0,
        },
    )

  return {
      "type": "PARALLEL_SPAWN",
      "room_id": room_id,
      "subagents": created_subs,
      "tasks": TASKS[:25],
      "brain": BRAIN_STATE,
      "message": f"Dispatched 3 sub-agents in {ROOMS[room_id]['name']}",
  }