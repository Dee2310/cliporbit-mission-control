import time
import uuid

ROOMS = {
    "cliporbit": {
        "id": "cliporbit",
        "name": "ClipOrbit Creative",
        "business": "ClipOrbit Media",
        "x": 9.5,
        "z": 7.5,
        "color": "#8b5cf6",
        "floor": "#2e1065",
        "lead": "Video Editor",
        "stats": {"today": 0, "running": 0, "turnaround": "11m"},
        "tools": [
            {"name": "YouTube Data API", "status": "Connected"},
            {"name": "FFmpeg / yt-dlp", "status": "Connected"},
            {"name": "CapCut / Subtitles", "status": "Connected"},
            {"name": "GitHub Actions", "status": "Connected"},
        ],
        "skills": [
            {"name": "rough-cut", "pct": 85},
            {"name": "captions-burn-in", "pct": 72},
            {"name": "resize-for-shorts", "pct": 91},
            {"name": "hook-extractor", "pct": 66},
        ],
    },
    "paystack": {
        "id": "paystack",
        "name": "Paystack & B2B Ops",
        "business": "B2B Automation",
        "x": -9.5,
        "z": 7.5,
        "color": "#ef4444",
        "floor": "#450a0a",
        "lead": "Webhook Architect",
        "stats": {"today": 0, "running": 0, "turnaround": "4m"},
        "tools": [
            {"name": "Paystack Webhooks", "status": "Connected"},
            {"name": "Neon PostgreSQL", "status": "Connected"},
            {"name": "WhatsApp Receipts", "status": "Connected"},
            {"name": "Render Cloud", "status": "Connected"},
        ],
        "skills": [
            {"name": "verify-signature", "pct": 96},
            {"name": "receipt-dispatch", "pct": 88},
            {"name": "ledger-reconcile", "pct": 74},
        ],
    },
    "research": {
        "id": "research",
        "name": "Research & Intel",
        "business": "Universal",
        "x": 0.0,
        "z": -11.5,
        "color": "#3b82f6",
        "floor": "#172554",
        "lead": "Hunter & Scout",
        "stats": {"today": 0, "running": 0, "turnaround": "6m"},
        "tools": [
            {"name": "YouTube Scraper", "status": "Connected"},
            {"name": "GitHub Trending", "status": "Connected"},
            {"name": "Gemini Deep Search", "status": "Connected"},
        ],
        "skills": [
            {"name": "viral-hook-scan", "pct": 82},
            {"name": "competitor-audit", "pct": 64},
            {"name": "niche-scoring", "pct": 79},
        ],
    },
    "social": {
        "id": "social",
        "name": "Social & Publishing",
        "business": "ClipOrbit & Brand",
        "x": 12.0,
        "z": -2.0,
        "color": "#ec4899",
        "floor": "#500724",
        "lead": "Publisher Bot",
        "stats": {"today": 0, "running": 0, "turnaround": "3m"},
        "tools": [
            {"name": "YouTube Shorts", "status": "Connected"},
            {"name": "TikTok / Reels", "status": "Connected"},
            {"name": "X / Threads", "status": "Connected"},
        ],
        "skills": [
            {"name": "auto-schedule", "pct": 94},
            {"name": "seo-metadata", "pct": 81},
            {"name": "cross-post", "pct": 70},
        ],
    },
    "dev": {
        "id": "dev",
        "name": "Dev & Engineering",
        "business": "Apps & SaaS",
        "x": 9.5,
        "z": -9.5,
        "color": "#22c55e",
        "floor": "#052e16",
        "lead": "Full-Stack Agent",
        "stats": {"today": 0, "running": 0, "turnaround": "16m"},
        "tools": [
            {"name": "GitHub Repos", "status": "Connected"},
            {"name": "Python / Node.js", "status": "Connected"},
            {"name": "Flutter / Vue 3", "status": "Connected"},
        ],
        "skills": [
            {"name": "api-builder", "pct": 89},
            {"name": "ci-deploy", "pct": 92},
            {"name": "bug-triage", "pct": 67},
        ],
    },
    "inbox": {
        "id": "inbox",
        "name": "Inbox & Outreach",
        "business": "Client Acquisition",
        "x": -9.5,
        "z": -9.5,
        "color": "#f59e0b",
        "floor": "#451a03",
        "lead": "Outreach Closer",
        "stats": {"today": 0, "running": 0, "turnaround": "5m"},
        "tools": [
            {"name": "WhatsApp Business", "status": "Connected"},
            {"name": "Gmail API", "status": "Connected"},
            {"name": "Lead CRM", "status": "Connected"},
        ],
        "skills": [
            {"name": "pitch-personalizer", "pct": 84},
            {"name": "follow-up-seq", "pct": 76},
        ],
    },
    "scripts": {
        "id": "scripts",
        "name": "Scripts & Strategy",
        "business": "Content & Copy",
        "x": -12.0,
        "z": -2.0,
        "color": "#a855f7",
        "floor": "#3b0764",
        "lead": "Hook Writer",
        "stats": {"today": 0, "running": 0, "turnaround": "8m"},
        "tools": [
            {"name": "Gemini 2.5 Pro", "status": "Connected"},
            {"name": "Google Drive Docs", "status": "Connected"},
        ],
        "skills": [
            {"name": "3sec-hook-gen", "pct": 90},
            {"name": "b2b-case-study", "pct": 73},
        ],
    },
    "analytics": {
        "id": "analytics",
        "name": "Analytics & QA",
        "business": "All Businesses",
        "x": 0.0,
        "z": 11.5,
        "color": "#14b8a6",
        "floor": "#042f2e",
        "lead": "Retention Analyst",
        "stats": {"today": 0, "running": 0, "turnaround": "2m"},
        "tools": [
            {"name": "YT Studio Metrics", "status": "Connected"},
            {"name": "Paystack Revenue", "status": "Connected"},
            {"name": "SQLite Telemetry", "status": "Connected"},
        ],
        "skills": [
            {"name": "audio-sync-qa", "pct": 95},
            {"name": "revenue-forecast", "pct": 80},
        ],
    },
}

AGENTS = {
    "hunter_agent": {
        "id": "hunter_agent",
        "name": "Hunter Agent",
        "room": "research",
        "role": "Channel Discovery",
        "color": "#3b82f6",
        "state": "idle",
        "progress": 0,
        "task": "Standby",
        "is_subagent": False,
    },
    "scout_agent": {
        "id": "scout_agent",
        "name": "Scout Agent",
        "room": "research",
        "role": "Hook Extraction",
        "color": "#60a5fa",
        "state": "idle",
        "progress": 0,
        "task": "Standby",
        "is_subagent": False,
    },
    "editor_agent": {
        "id": "editor_agent",
        "name": "Video Editor",
        "room": "cliporbit",
        "role": "Lead Vertical Cutter",
        "color": "#8b5cf6",
        "state": "idle",
        "progress": 0,
        "task": "Standby",
        "is_subagent": False,
    },
    "design_agent": {
        "id": "design_agent",
        "name": "Graphic Design",
        "room": "cliporbit",
        "role": "Thumbnails & Overlays",
        "color": "#a78bfa",
        "state": "idle",
        "progress": 0,
        "task": "Standby",
        "is_subagent": False,
    },
    "publisher_agent": {
        "id": "publisher_agent",
        "name": "Publisher Bot",
        "room": "social",
        "role": "Multi-Platform Upload",
        "color": "#ec4899",
        "state": "idle",
        "progress": 0,
        "task": "Standby",
        "is_subagent": False,
    },
    "analyst_agent": {
        "id": "analyst_agent",
        "name": "QA & Analyst",
        "room": "analytics",
        "role": "Retention & Audio Check",
        "color": "#14b8a6",
        "state": "idle",
        "progress": 0,
        "task": "Standby",
        "is_subagent": False,
    },
    "paystack_agent": {
        "id": "paystack_agent",
        "name": "Paystack Ops",
        "room": "paystack",
        "role": "Webhook & Receipt Engine",
        "color": "#ef4444",
        "state": "idle",
        "progress": 0,
        "task": "Standby",
        "is_subagent": False,
    },
    "dev_agent": {
        "id": "dev_agent",
        "name": "Full-Stack Dev",
        "room": "dev",
        "role": "Python / Vue / Flutter",
        "color": "#22c55e",
        "state": "idle",
        "progress": 0,
        "task": "Standby",
        "is_subagent": False,
    },
    "outreach_agent": {
        "id": "outreach_agent",
        "name": "Outreach Agent",
        "room": "inbox",
        "role": "B2B WhatsApp & Email",
        "color": "#f59e0b",
        "state": "idle",
        "progress": 0,
        "task": "Standby",
        "is_subagent": False,
    },
    "script_agent": {
        "id": "script_agent",
        "name": "Hook Writer",
        "room": "scripts",
        "role": "Script & Copywriting",
        "color": "#a855f7",
        "state": "idle",
        "progress": 0,
        "task": "Standby",
        "is_subagent": False,
    },
}

BRAIN_STATE = {
    "notes_count": 1842,
    "recent_memories": [
        {
            "id": "mem_1",
            "source": "ClipOrbit",
            "text": (
                "Clips under 42s with bold yellow/white captions retain +24%"
                " past 3s."
            ),
        },
        {
            "id": "mem_2",
            "source": "Paystack Ops",
            "text": (
                "Auto-WhatsApp PDF receipts cut merchant support follow-ups by"
                " 80%."
            ),
        },
    ],
}

# Clean production task list (populates from real webhook events)
TASKS = []

STATION_MAP = {
    "hunter": "research",
    "editor": "cliporbit",
    "analyst": "analytics",
    "publisher": "social",
    "hub": "cliporbit",
}


def apply_agent_event(data: dict) -> dict:
  agent_id = data.get("agent_id", "editor_agent")
  raw_room = data.get("room") or data.get("station", "cliporbit")
  room_id = STATION_MAP.get(raw_room, raw_room)
  if room_id not in ROOMS:
    room_id = "cliporbit"

  state = data.get("state", "working")
  progress = int(data.get("progress", 50))
  task = data.get("task", "Executing workflow step")
  message = data.get("message", task)

  if agent_id not in AGENTS:
    AGENTS[agent_id] = {
        "id": agent_id,
        "name": data.get("agent_name", agent_id.replace("_", " ").title()),
        "room": room_id,
        "role": "Sub-Agent Worker",
        "color": ROOMS[room_id]["color"],
        "state": state,
        "progress": progress,
        "task": task,
        "is_subagent": True,
    }
  else:
    AGENTS[agent_id].update({
        "room": room_id,
        "state": state,
        "progress": progress,
        "task": task,
    })

  # If ClipOrbit requests human approval before publishing to YouTube:
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
  elif state == "working":
    # Track running task on the board
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

    BRAIN_STATE["notes_count"] += 1
    BRAIN_STATE["recent_memories"].insert(
        0,
        {
            "id": f"mem_{int(time.time()*1000)}",
            "source": ROOMS[room_id]["name"],
            "text": f"{AGENTS[agent_id]['name']} completed: {message}",
        },
    )
    BRAIN_STATE["recent_memories"] = BRAIN_STATE["recent_memories"][:15]

  return {
      "type": "AGENT_UPDATE",
      "event_id": f"evt_{int(time.time()*1000)}",
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
        "role": "Parallel Sub-Agent",
        "color": ROOMS[room_id]["color"],
        "state": "working",
        "progress": 15 * idx,
        "task": prompt or f"Parallel batch task #{idx}",
        "is_subagent": True,
        "slot": idx - 1,
    }
    AGENTS[sub_id] = sub_agent
    created_subs.append(sub_agent)
    TASKS.insert(
        0,
        {
            "id": f"tsk_{uuid.uuid4().hex[:6]}",
            "title": f"{sub_agent['name']}: {prompt or 'Parallel execution'}",
            "room": room_id,
            "agent": sub_agent["name"],
            "status": "running",
            "progress": sub_agent["progress"],
        },
    )

  BRAIN_STATE["notes_count"] += 1
  return {
      "type": "PARALLEL_SPAWN",
      "room_id": room_id,
      "subagents": created_subs,
      "tasks": TASKS[:25],
      "brain": BRAIN_STATE,
      "message": (
          f"Spawned 3 parallel sub-agents in {ROOMS[room_id]['name']}"
      ),
  }