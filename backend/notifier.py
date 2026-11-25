import os
import aiohttp


async def send_iphone_alert(title: str, body: str):
  """Sends instant push notification via Telegram Bot and/or ntfy.sh."""
  hq_url = os.environ.get(
      "AGENT_HQ_URL", "https://cliporbit-mission-control.onrender.com"
  )
  tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
  tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
  ntfy_topic = os.environ.get("NTFY_TOPIC")

  async with aiohttp.ClientSession() as session:
    if tg_token and tg_chat:
      url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
      payload = {
          "chat_id": tg_chat,
          "text": f"🏢 *Agent HQ Approval Needed*\n*{title}*\n{body}\n\n👉 {hq_url}",
          "parse_mode": "Markdown",
      }
      try:
        await session.post(url, json=payload, timeout=5)
      except Exception:
        pass

    if ntfy_topic:
      try:
        await session.post(
            f"https://ntfy.sh/{ntfy_topic}",
            data=f"{title}: {body}".encode("utf-8"),
            headers={
                "Title": "Agent HQ Approval",
                "Priority": "high",
                "Click": hq_url,
            },
            timeout=5,
        )
      except Exception:
        pass