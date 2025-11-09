# TCP connections
$port = 34433
write-host "Searching for processes on port $port"
$tcpProcs = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | 
    ForEach-Object { Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue }

# UDP endpoints
$udpProcs = Get-NetUDPEndpoint -LocalPort $port -ErrorAction SilentlyContinue | 
    ForEach-Object { Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue }

# Combine and remove duplicates
$allProcs = $tcpProcs + $udpProcs | Sort-Object Id -Unique

# Display
$allProcs | Select-Object Id, ProcessName
