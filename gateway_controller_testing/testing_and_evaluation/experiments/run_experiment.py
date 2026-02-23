import subprocess
import threading
import time
import json
import re
import os, sys
import requests
from datetime import datetime, timezone, timedelta

if len(sys.argv) < 3:
    print("Usage: python run_experiment.py <concurrency_count> <data_size>")
    sys.exit(1)

CONCURRENCY_COUNT = int(sys.argv[1])
DATA_SIZE = sys.argv[2]

GATEWAY_HOST = "192.168.59.109"
PROM_URL = "http://localhost:9090/api/v1/query_range"
POD_REGEX = ".*(pst|sidecar|siena|producer|rabbit|small|medium|large).*"

payload_dict = {
    "delivery_mode": "lightweight_summary",
    "include_metadata": "false",
    "data_size": DATA_SIZE,
    "note": f"Triggers {DATA_SIZE} response"
}
json_payload = json.dumps(payload_dict)
detailed_results = []

def run_curl(request_id):
    write_out_format = f"ID:{request_id}|CODE:%{{http_code}}|CONN:%{{time_connect}}|TTFB:%{{time_starttransfer}}|TOTAL:%{{time_total}}"
    cmd = [
        "realcurl", "-ki", "-sS", "-o", "NUL",
        "-w", write_out_format,
        "--http3", "https://www.example.com/mq",
        "--resolve", f"www.example.com:443:{GATEWAY_HOST}",
        "-H", "Cache-Control: no-cache, no-store",
        "-H", "Pragma: no-cache",
        "-H", f"x-event-cbr-data: {json_payload}"
    ]
    process = subprocess.run(cmd, capture_output=True, text=True)
    match = re.search(r"ID:(\d+)\|CODE:(\d+)\|CONN:([\d\.]+)\|TTFB:([\d\.]+)\|TOTAL:([\d\.]+)", process.stdout)
    if match:
        detailed_results.append({
            "request_id": int(match.group(1)),
            "status_code": match.group(2),
            "conn_ms": float(match.group(3)) * 1000,
            "ttfb_ms": float(match.group(4)) * 1000,
            "total_ms": float(match.group(5)) * 1000
        })

# --- STEP 1: EXECUTE CONCURRENT REQUESTS ---
print(f"--- Launching {CONCURRENCY_COUNT} Concurrent Requests ---")
test_start_time = datetime.now(timezone.utc)
start_timer = time.perf_counter()

threads = [threading.Thread(target=run_curl, args=(i,)) for i in range(1, CONCURRENCY_COUNT + 1)]
for t in threads: t.start()
for t in threads: t.join()

test_end_time = datetime.now(timezone.utc)
total_runtime_ms = (time.perf_counter() - start_timer) * 1000

# --- STEP 2: WAIT FOR PROMETHEUS SCRAPE ---
print(f"Waiting 15s for Prometheus to collect metrics...")
time.sleep(15)

# --- STEP 3: QUERY PROMETHEUS ---
def fetch_metrics(query):
    params = {
        "query": query,
        # Change these lines in fetch_metrics:
        "start": (test_start_time - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": (test_end_time + timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "step": "5s"
    }
    try:
        r = requests.get(PROM_URL, params=params).json()
        return r.get('data', {}).get('result', [])
    except:
        return []

print("Fetching CPU and Memory metrics...")
mem_data = fetch_metrics(f'container_memory_working_set_bytes{{pod=~"{POD_REGEX}"}} / 1024 / 1024')
cpu_data = fetch_metrics(f'rate(container_cpu_usage_seconds_total{{pod=~"{POD_REGEX}"}}[1m])')

# --- STEP 4: ORGANIZE AND SAVE ---
timestamp_str = test_start_time.strftime("%Y%m%d_%H%M%S")
folder_path = os.path.join(DATA_SIZE, f"{CONCURRENCY_COUNT}__concurrent_requests", timestamp_str)
os.makedirs(folder_path, exist_ok=True)

successes = sum(1 for r in detailed_results if r.get("status_code") == "200")

final_output = {
    "test_metadata": {
        "timestamp": timestamp_str,
        "data_size": DATA_SIZE,
        "concurrency": CONCURRENCY_COUNT,
        "success_rate": f"{successes}/{CONCURRENCY_COUNT}",
        "total_execution_ms": round(total_runtime_ms, 2)
    },
    "network_performance": detailed_results,
    "prometheus_metrics": {
        "memory_mb": mem_data,
        "cpu_cores": cpu_data
    }
}

file_path = os.path.join(folder_path, "performance_data.json")
with open(file_path, "w") as f:
    json.dump(final_output, f, indent=4)

print(f"Complete! Integrated data saved to: {file_path}")