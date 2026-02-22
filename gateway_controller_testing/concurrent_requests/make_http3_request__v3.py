import subprocess
import threading
import time
import json
import re

# --- CONFIGURATION --
CONCURRENCY_COUNT = 16
GATEWAY_HOST = "192.168.59.109"
DATA_SIZE = "1MB"

payload_dict = {
    "delivery_mode": "lightweight_summary",
    "include_metadata": "false",
    "data_size": DATA_SIZE,
    "note": "Triggers 1MB response"
}
json_payload = json.dumps(payload_dict)

results_list = []

# ... (payload_dict and json_payload stay the same) ...

def run_curl(request_id):
    output_file = f"response_{request_id}.json"
    
    write_out_format = (
        f"REQ_ID:{request_id}|CODE:%{{http_code}}|TTFB:%{{time_starttransfer}}s"
    )

    cmd = [
        "realcurl", "-ki", "-sS", "-o", output_file,
        "-w", write_out_format,
        "--http3", "https://www.example.com/mq",
        "--resolve", f"www.example.com:443:{GATEWAY_HOST}",
        "-H", "Cache-Control: no-cache, no-store",
        "-H", "Pragma: no-cache",
        "-H", f"x-event-cbr-data: {json_payload}"
    ]
    
    # Run the command
    process = subprocess.run(cmd, capture_output=True, text=True)
    output = process.stdout
    
    # Extract the code using regex (looks for CODE: then digits)
    match = re.search(r"CODE:(\d+)", output)
    status_code = match.group(1) if match else "000"
    
    # Store in our shared list
    results_list.append(status_code)
    
    #print(f"Request {request_id} finished with Status: {status_code}")

# --- EXECUTION ---
print(f"--- Launching {CONCURRENCY_COUNT} Concurrent Requests ---")
start_clock = time.strftime("%H:%M:%S")
start_timer = time.perf_counter()

threads = []
for i in range(1, CONCURRENCY_COUNT + 1):
    t = threading.Thread(target=run_curl, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# --- ANALYZE RESULTS ---
total_requests = len(results_list)
successes = results_list.count("200")
failures = total_requests - successes

print(f"\n--- Final Status Summary ---")
print(f"Total Requests: {total_requests}")
print(f"Total 200 OK:   {successes}")
print(f"Total Failed:   {failures}")

if failures > 0:
    print(f"Alert: {failures} requests did not return a 200!")

end_timer = time.perf_counter()
total_ms = (end_timer - start_timer) * 1000

print(f"--- Process Summary ---")
print(f"Started at: {start_clock}")
#print(f"Total Execution Time: {total_ms:.2f} ms")