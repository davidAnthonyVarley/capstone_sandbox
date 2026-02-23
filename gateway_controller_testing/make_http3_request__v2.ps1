# Setup variables
$GATEWAY_HOST = (minikube ip);


$JSON_PAYLOAD = '{ \"delivery_mode\": \"lightweight_summary\", \"include_metadata\": \"false\", \"data_size\": \"100MB\", \"note\": \"Triggers 1MB response\" }';

Write-Host "--- Starting High-Precision Request ---" -ForegroundColor Cyan

# 1. Capture the exact Start Time (Clock) and Start the Timer (Duration)
$startTime = Get-Date -Format "HH:mm:ss.fff"
$sw = [System.Diagnostics.Stopwatch]::StartNew()

# 2. Run curl
realcurl -vki -sS -o response_data.json `
  -w "`n--- Network Latency Stats ---`nHTTP Code: %{http_code}`nConnect Time: %{time_connect}s`nTime to First Byte: %{time_starttransfer}s`nTotal Request Time: %{time_total}s`n" `
  --http3 "https://www.example.com/mq" `
  --resolve "www.example.com:443:$GATEWAY_HOST" `
  -H "Cache-Control: no-cache, no-store" `
  -H "Pragma: no-cache" `
  -H "x-event-cbr-data: $JSON_PAYLOAD"

# 3. Stop Timer and Capture the exact End Time
$sw.Stop()
$endTime = Get-Date -Format "HH:mm:ss.fff"

Write-Host "--- DATA SIZE ---" -ForegroundColor Cyan
Write-Host "--- 1MB ---" -ForegroundColor Yellow
Write-Host ""
Write-Host "--- PowerShell Summary ---" -ForegroundColor Cyan
Write-Host "Request Started: $startTime"
Write-Host "Request Ended:   $endTime"
Write-Host "Total Process Execution: $($sw.Elapsed.TotalMilliseconds) ms"