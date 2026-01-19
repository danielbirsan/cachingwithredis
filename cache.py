import os
import json
import hashlib
import redis
from prometheus_client import Counter, start_http_server
import numpy as np
from redis.commands.search.field import VectorField, TextField, TagField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import time
from metrics import CACHE_OPS, ERROR_COUNT

# start_http_server(8000)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

CACHE_INDEX_NAME = "semantic_cache_idx"
VECTOR_DIMENSION = 384  # for 'all-MiniLM-L6-v2'

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
    method_type = "exact"

    if val is not None:
        CACHE_OPS.labels(method=method_type, status="hit").inc()
        return json.loads(val)

    CACHE_OPS.labels(method=method_type, status="miss").inc()
    return None


def cache_set(key: str, value, ttl: int):
    redis_client.setex(key, ttl, json.dumps(value))


def init_semantic_cache():
    """
    Creates a Vector Search Index in Redis if it doesn't exist.
    """
    try:
        redis_client.ft(CACHE_INDEX_NAME).info()
        print("Semantic Cache Index already exists.")
    except Exception as e:
        print("Creating Semantic Cache Index...")
        schema = (
            TextField("$.query_text", as_name="query_text"),
            TagField("$.category", as_name="category"),
            VectorField(
                "$.embedding",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": VECTOR_DIMENSION,
                    "DISTANCE_METRIC": "COSINE",
                },
                as_name="embedding",
            ),
        )
        redis_client.ft(CACHE_INDEX_NAME).create_index(
            schema,
            definition=IndexDefinition(
                prefix=["sem_cache:"], index_type=IndexType.JSON
            ),
        )


def semantic_cache_get(
    query_vector: list[float], category: str, threshold: float = 0.1
):
    """
    Performs a K-Nearest Neighbor (KNN) search.
    Threshold 0.1 means 'very similar'. Lower is stricter.
    """
    query = (
        Query(f"(@category:{{{category}}})=>[KNN 1 @embedding $vec AS score]")
        .sort_by("score")
        .return_field("$response", "response")
        .return_field("score")
        .dialect(2)
    )

    params = {"vec": np.array(query_vector, dtype=np.float32).tobytes()}

    try:
        results = redis_client.ft(CACHE_INDEX_NAME).search(query, query_params=params)

        if results.docs:
            doc = results.docs[0]
            score = float(doc.score)

            if score < threshold:
                CACHE_OPS.labels(method="semantic", status="hit").inc()
                print(f"[SEMANTIC HIT] Category: {category}, Score: {score}")
                return json.loads(doc.response)

            CACHE_OPS.labels(method="semantic", status="miss").inc()
            print(
                f"[SEMANTIC MISS] Best match in {category} was score {score} (threshold {threshold})"
            )

    except Exception as e:
        ERROR_COUNT.labels(type="redis_search").inc()
        print(f"Vector search failed: {e}")

    return None


def semantic_cache_set(
    query_text: str, query_vector: list[float], response, category: str
):
    """
    Stores the result along with its vector embedding.
    """

    key = f"sem_cache:{hash(query_text + category)}"

    data = {
        "query_text": query_text,
        "category": category,
        "embedding": query_vector,
        "response": json.dumps(response),
        "created_at": time.time(),
    }

    redis_client.json().set(key, "$", data)
    redis_client.expire(key, 86400)  # 24 hours


def invalidate_cache_for_term(term: str):
    """
    Searches the Semantic Cache Index for any queries containing the specific term
    (e.g., 'Software Engineer') and deletes those specific keys.
    """
    if not term:
        return

    search_query = Query(f'@query_text:"{term}"').no_content()

    try:
        result = redis_client.ft(CACHE_INDEX_NAME).search(search_query)

        if not result.docs:
            print(f"[CACHE CLEANUP] No entries found for term: '{term}'")
            return

        keys_to_delete = [doc.id for doc in result.docs]

        if keys_to_delete:
            redis_client.delete(*keys_to_delete)
            print(
                f"[CACHE CLEANUP] Invalidated {len(keys_to_delete)} keys for: '{term}'"
            )

    except Exception as e:
        print(f"[CACHE CLEANUP ERROR] Could not invalidate: {e}")
