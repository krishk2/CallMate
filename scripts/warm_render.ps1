<#
Keeps both Render free-tier services awake during a testing session. Render's free plan
spins a service down after 15 min with zero traffic and cold-starts it on the next request --
confirmed live to take long enough that a brain WS handshake made right after a caller's
greeting can get a flat HTTP 502 if brain happened to be asleep (pipeline/brain_client/
client.py now retries that, but staying warm avoids hitting it at all).

Run this once before a testing session and leave it running in its own window; it pings both
services' /healthz every 10 minutes, well under the 15-minute sleep window.
#>

$pipelineUrl = "https://callmate-pipeline-3464.onrender.com/healthz"
$brainUrl = "https://callmate-brain-3464.onrender.com/healthz"

Write-Host "Pinging both services every 10 minutes. Ctrl+C to stop." -ForegroundColor Yellow

while ($true) {
    $time = Get-Date -Format "HH:mm:ss"
    try {
        $p = Invoke-WebRequest -Uri $pipelineUrl -TimeoutSec 30 -UseBasicParsing
        Write-Host "[$time] pipeline: $($p.StatusCode)"
    } catch {
        Write-Host "[$time] pipeline: FAILED - $_" -ForegroundColor Red
    }
    try {
        $b = Invoke-WebRequest -Uri $brainUrl -TimeoutSec 30 -UseBasicParsing
        Write-Host "[$time] brain:    $($b.StatusCode)"
    } catch {
        Write-Host "[$time] brain:    FAILED - $_" -ForegroundColor Red
    }
    Start-Sleep -Seconds 600
}
