$certPath = "$(Get-Location)\www.example.com.crt"
$certBytes = [System.IO.File]::ReadAllBytes($certPath)
$hasher = [System.Security.Cryptography.SHA256]::Create()
$hashBytes = $hasher.ComputeHash($certBytes)
$base64Hash = [Convert]::ToBase64String($hashBytes)

Write-Host "`nYour WebTransport Hash is:" -ForegroundColor Green
Write-Host $base64Hash