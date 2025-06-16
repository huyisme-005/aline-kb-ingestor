
"""
backend/api/tasks.py

Defines Celery background tasks for payload ingestion.
"""

import os
from celery import Celery
import json

# Configure Celery broker & backend
REDIS = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
cel = Celery("tasks", broker=REDIS, backend=REDIS)

@cel.task
def ingest_payload(payload: dict):
    """
    Persist a KBPayload to disk (could be extended to S3/DB).

    Args:
        payload: Dict matching the KBPayload schema.

    Returns:
        Dict containing the output file path.
    """
    os.makedirs("data", exist_ok=True)
    team = payload["team_id"]
    out_path = f"data/{team}_{cel.request.id}.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    return {"path": out_path}
