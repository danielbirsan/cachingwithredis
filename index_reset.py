import redis

r = redis.Redis(host="localhost", port=6379)  # Adjust host/port if needed
try:
    r.ft("semantic_cache_idx").dropindex(delete_documents=True)
    print("Old index deleted.")
except:
    print("No index to delete.")
