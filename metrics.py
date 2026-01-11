from prometheus_client import Counter, start_http_server

# Cache metrics
CACHE_HITS = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_name"]
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_name"]
)

def start_metrics_server():
    # Portul pe care Prometheus îl va scrapa
    start_http_server(8000)
