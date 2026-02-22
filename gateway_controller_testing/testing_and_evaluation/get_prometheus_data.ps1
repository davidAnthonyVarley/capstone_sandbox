realcurl -G "http://localhost:9090/api/v1/query_range" `
    --data-urlencode "query=container_memory_working_set_bytes" `
    --data-urlencode "start=2026-02-22T20:30:00Z" `
    --data-urlencode "end=2026-02-22T22:00:00Z" `
    --data-urlencode "step=1m" | `
jq -r '.data.result[] | .metric.pod as $pod | .values[] | [($pod), (.[0] | strftime("%Y-%m-%dT%H:%M:%SZ")), .[1]] | @csv' > my_data.csv;
