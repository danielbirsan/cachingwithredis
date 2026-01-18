import os
import json
import hashlib
import redis
from prometheus_client import Counter, start_http_server
<<<<<<< Updated upstream

start_http_server(8000)
=======
import numpy as np
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import time
from metrics import CACHE_HITS, CACHE_MISSES
>>>>>>> Stashed changes

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)


def make_key(prefix: str, payload: dict) -> str:
    """
    Generates a deterministic cache key based on a prefix and a JSON-serializable payload.
    """
    raw = json.dumps(payload, sort_keys=True)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"{prefix}:{digest}"


def cache_get(key: str):
    """
    Retrieves a value from Redis cache.
    Updates Prometheus HIT / MISS counters.
    """
    val = redis_client.get(key)
    prefix = key.split(":", 1)[0]

    if val is not None:
        CACHE_HITS.labels(prefix=prefix).inc()
        return json.loads(val)

    CACHE_MISSES.labels(prefix=prefix).inc()
    return None


def cache_set(key: str, value, ttl: int):
    redis_client.setex(key, ttl, json.dumps(value))
