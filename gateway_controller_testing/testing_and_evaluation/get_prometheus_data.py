import requests
import pandas as pd

# 1. Define your query and time range
url = "http://localhost:9090/api/v1/query_range"
params = {
    "query": 'container_memory_working_set_bytes{pod=~".*small.*"}',
    # We use a 3-minute window to see the "spike" in the middle
    "start": "2026-02-22T23:00:00Z", 
    "end":   "2026-02-23T01:00:00Z",
    "step":  "5s" # Assuming you set your scrape interval to 5s
}

# 2. Get the data from Prometheus
response = requests.get(url, params=params).json()

# 3. Flatten the JSON into a list for the spreadsheet
rows = []
if response.get('status') == 'success':
    for result in response['data']['result']:
        pod = result['metric'].get('pod', 'unknown')
        for timestamp, value in result['values']:
            rows.append({
                "Time": pd.to_datetime(timestamp, unit='s'), 
                "Pod": pod, 
                "Value_MB": round(float(value)/1024/1024, 2)
            })

# 4. Create the Excel file
df = pd.DataFrame(rows)
file = "new_prometheus_metrics.xlsx"
df.to_excel(f"{file}", index=False) # <--- The key change is here

print(f"Successfully saved to {file}")