from prometheus_client import Counter, Histogram, start_http_server
import socket

# CACHE_HITS = Counter(
#     "cache_hits_total",
#     "Total number of cache hits",
#     ["layer"],  # exact / semantic / llm
# )

# CACHE_MISSES = Counter("cache_misses_total", "Total number of cache misses", ["layer"])

# REQUEST_LATENCY = Histogram(
#     "rag_request_latency_seconds", "Latency of RAG requests", ["component"]
# )


CACHE_OPS = Counter(
    "kartog_cache_ops_total",
    "Cache Operations (Hits/Misses)",
    ["method", "status"],  # method: 'exact' or 'semantic', status: 'hit' or 'miss'
)

TOOL_USAGE = Counter(
    "kartog_tool_usage_total", "Execution count of specific tools", ["tool_name"]
)

REQUEST_LATENCY = Histogram(
    "kartog_request_latency_seconds",
    "Time spent processing requests",
    ["stage"],  # e.g., 'total_flow', 'llm_extraction', 'neo4j_query'
)

ERROR_COUNT = Counter(
    "kartog_errors_total", "Exceptions raised in the application", ["type"]
)


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def start_metrics():
    # Only start if the port is NOT already in use
    if not is_port_in_use(8000):
        try:
            start_http_server(8000)
            print("Metrics server started on port 8000")
        except OSError:
            print("Metrics server already running (caught OSError).")
    else:
        print("Metrics server already running on port 8000.")
