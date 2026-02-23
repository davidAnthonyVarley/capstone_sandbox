# Define the experiment matrix
$DataSizes = @("10MB")
$ConcurrencyLevels = @(0, 1, 2, 3, 4, 5)

Write-Host "--- Starting Experiment Matrix ---" -ForegroundColor Cyan

foreach ($size in $DataSizes) {
    foreach ($level in $ConcurrencyLevels) {
        Write-Host "Running: Size=$size, Concurrency=$level" -ForegroundColor Yellow
        
        # Call the Python script with arguments
        python run_experiment.py $level $size
        
        Write-Host "Iteration Complete. Cooling down for 5s..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 5
    }
}

Write-Host "--- All Experiments Finished ---" -ForegroundColor Green