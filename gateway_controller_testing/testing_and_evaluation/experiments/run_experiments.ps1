# Define the experiment matrix
$DataSizes = @("1MB")

Write-Host "--- Starting Experiment Matrix ---" -ForegroundColor Cyan

foreach ($size in $DataSizes) {
    $level = 0;
    while ($level -lt 31) {
        Write-Host "Running: Size=$size, Concurrency=$level" -ForegroundColor Yellow
        
        # Call the Python script with arguments
        python run_experiment.py $level $size
        
        Write-Host "Iteration Complete. Cooling down for 5s..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 5

        $level++;
    }
}

Write-Host "--- All Experiments Finished ---" -ForegroundColor Green