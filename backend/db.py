import json
import os
import asyncpg

_POOL = None


async def init_db():
  global _POOL
  db_url = os.environ.get("DATABASE_URL")
  if not db_url:
    print("⚠️ DATABASE_URL not set — running in RAM-only mode.")
    return

  _POOL = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=5)
  async with _POOL.acquire() as conn:
    await conn.execute("""
            CREATE TABLE IF NOT EXISTS hq_kv_store (
                key TEXT PRIMARY KEY,
                value JSONB NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
  print("✅ Connected to Neon PostgreSQL persistence.")


async def save_state_snapshot(
    rooms: dict, agents: dict, tasks: list, brain: dict
):
  if not _POOL:
    return
  try:
    async with _POOL.acquire() as conn:
      for k, v in [
          ("rooms", rooms),
          ("agents", agents),
          ("tasks", tasks[:50]),
          ("brain", brain),
      ]:
        await conn.execute(
            """
                    INSERT INTO hq_kv_store (key, value, updated_at)
                    VALUES ($1, $2::jsonb, NOW())
                    ON CONFLICT (key)
                    DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
                    """,
            k,
            json.dumps(v),
        )
  except Exception as e:
    print(f"⚠️ Neon save error: {e}")


async def load_state_snapshot() -> dict:
  if not _POOL:
    return {}
  try:
    async with _POOL.acquire() as conn:
      rows = await conn.fetch("SELECT key, value FROM hq_kv_store;")
      result = {}
      for r in rows:
        val = r["value"]
        result[r["key"]] = json.loads(val) if isinstance(val, str) else val
      return result
  except Exception as e:
    print(f"⚠️ Neon load error: {e}")
    return {}