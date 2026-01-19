from prometheus_client import Counter, Histogram, start_http_server
import socket

CACHE_HITS = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["layer"],  # exact / semantic / llm
)

CACHE_MISSES = Counter("cache_misses_total", "Total number of cache misses", ["layer"])

REQUEST_LATENCY = Histogram(
    "rag_request_latency_seconds", "Latency of RAG requests", ["component"]
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
