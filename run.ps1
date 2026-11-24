Set-Location "$PSScriptRoot\VisualSQL"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting VisualSQL Server..." -ForegroundColor Green
Write-Host "URL: http://127.0.0.1:5000" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
& "C:\Users\bhuvaneswari\AppData\Local\Programs\Python\Python313\python.exe" app.py
