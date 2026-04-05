import redis
import json
from app.config import REDIS_URL

r = redis.Redis.from_url(REDIS_URL)

def get_cache(key):
    data = r.get(key)
    return json.loads(data) if data else None

def set_cache(key, value, ttl=300):
    r.setex(key, ttl, json.dumps(value))
