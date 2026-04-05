from fastapi import FastAPI
from app.schemas import InputData
from app.cache import get_cache
from app.tasks import run_prediction
import hashlib
import json

app = FastAPI()

def hash_input(data):
    return hashlib.md5(json.dumps(data).encode()).hexdigest()

@app.post("/predict")
async def predict(data: InputData):
    data_dict = data.dict()
    key = hash_input(data_dict)

    # 1. tenta cache
    cached = get_cache(key)
    if cached:
        return {
            "status": "cached",
            "data": cached
        }

    # 2. dispara worker
    task = run_prediction.delay(data_dict)

    return {
        "status": "processing",
        "task_id": task.id
    }

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    from app.tasks import celery

    task = celery.AsyncResult(task_id)

    if task.state == "SUCCESS":
        return {
            "status": "done",
            "data": task.result
        }

    return {
        "status": task.state
    }
