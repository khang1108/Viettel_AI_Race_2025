from fastapi import APIRouter
from celery.result import AsyncResult
from app.celery_app import celery_app

router = APIRouter(prefix="/task", tags=["task"])

@router.get("/{task_id}")
def get_status(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    out = {
        "id": task_id,
        "state": res.state,
    }
    # Include result or error info when available (avoid huge payloads)
    if res.state == "SUCCESS":
        out["result"] = res.result if isinstance(res.result, dict) else str(res.result)
    elif res.state == "FAILURE":
        out["error"] = str(res.result)
    return out
