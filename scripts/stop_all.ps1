# Stops pipeline, brain, and any ngrok tunnel started by start_all.ps1.

Get-NetTCPConnection -LocalPort 8000, 8001 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "Stopped pipeline, brain, and ngrok."
