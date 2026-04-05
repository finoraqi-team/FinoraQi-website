from celery import Celery
from app.config import REDIS_URL
from app.model import model
from app.cache import set_cache
import hashlib
import json

celery = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)

def hash_input(data):
    return hashlib.md5(json.dumps(data).encode()).hexdigest()

@celery.task
def run_prediction(data):
    key = hash_input(data)
    result = model.predict(data["value"])
    set_cache(key, result)
    return result
