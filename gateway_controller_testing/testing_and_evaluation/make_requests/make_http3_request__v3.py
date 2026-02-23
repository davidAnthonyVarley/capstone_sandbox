import subprocess
import threading
import time
import json
import re
import os

# --- CONFIGURATION ---
CONCURRENCY_COUNT = 10
GATEWAY_HOST = "192.168.59.109"
DATA_SIZE = "1MB"

payload_dict = {
    "delivery_mode": "lightweight_summary",
    "include_metadata": "false",
    "data_size": DATA_SIZE,
    "note": "Triggers 1MB response"
}
json_payload = json.dumps(payload_dict)

# Shared list to store detailed dictionaries for each request
detailed_results = []

def run_curl(request_id):
    # Updated format to get Connect Time, TTFB, and Total Time
    # We use pipe separators to make parsing extremely reliable
    write_out_format = (
        f"ID:{request_id}|CODE:%{{http_code}}|CONN:%{{time_connect}}|TTFB:%{{time_starttransfer}}|TOTAL:%{{time_total}}"
    )

    cmd = [
        "realcurl", "-ki", "-sS", "-o", "NUL", # 'NUL' discards body to save disk I/O
        "-w", write_out_format,
        "--http3", "https://www.example.com/mq",
        "--resolve", f"www.example.com:443:{GATEWAY_HOST}",
        "-H", "Cache-Control: no-cache, no-store",
        "-H", "Pragma: no-cache",
        "-H", f"x-event-cbr-data: {json_payload}"
    ]
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    output = process.stdout
    
    # Parse the output using regex
    # Pattern: ID:1|CODE:200|CONN:0.045|TTFB:0.120|TOTAL:0.550
    pattern = r"ID:(\d+)\|CODE:(\d+)\|CONN:([\d\.]+)\|TTFB:([\d\.]+)\|TOTAL:([\d\.]+)"
    match = re.search(pattern, output)
    
    if match:
        result = {
            "request_id": int(match.group(1)),
            "status_code": match.group(2),
            "connection_setup_ms": float(match.group(3)) * 1000,
            "time_to_first_byte_ms": float(match.group(4)) * 1000,
            "total_request_time_ms": float(match.group(5)) * 1000
        }
    else:
        result = {"request_id": request_id, "status_code": "000", "error": "Parse Error"}

    detailed_results.append(result)

# --- EXECUTION ---
print(f"--- Launching {CONCURRENCY_COUNT} Concurrent Requests ---")
timestamp = time.strftime("%Y%m%d_%H%M%S")
start_timer = time.perf_counter()

threads = []
for i in range(1, CONCURRENCY_COUNT + 1):
    t = threading.Thread(target=run_curl, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

end_timer = time.perf_counter()

# --- FOLDER CALCULATIONS ---
# Folder structure: {data_size}\{concurrency}\{timestamp}
folder_path = os.path.join(DATA_SIZE, str(CONCURRENCY_COUNT), timestamp)
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# --- METADATA & SUCCESS COUNTS ---
successes = sum(1 for r in detailed_results if r.get("status_code") == "200")
total_runtime_ms = (end_timer - start_timer) * 1000

final_output = {
    "metadata": {
        "timestamp": timestamp,
        "concurrency_target": CONCURRENCY_COUNT,
        "actual_requests": len(detailed_results),
        "success_count": successes,
        "failure_count": len(detailed_results) - successes,
        "total_test_duration_ms": round(total_runtime_ms, 2),
        "data_size": DATA_SIZE
    },
    "individual_requests": detailed_results
}

# --- SAVE TO FILE ---
file_name = os.path.join(folder_path, "performance_data.json")
with open(file_name, "w") as f:
    json.dump(final_output, f, indent=4)

print(f"Done! Results saved to: {file_name}")
print(f"Success Rate: {successes}/{CONCURRENCY_COUNT}")