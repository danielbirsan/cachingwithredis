from prometheus_client import Counter, Histogram, start_http_server

CACHE_HITS = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["layer"]  # exact / semantic / llm
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["layer"]
)

REQUEST_LATENCY = Histogram(
    "rag_request_latency_seconds",
    "Latency of RAG requests",
    ["component"]
)

def start_metrics():
    start_http_server(8000)
