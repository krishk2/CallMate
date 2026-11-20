<#
Starts both Fly machines right before a test call. Fly's free-trial tier force-stops each
machine 5 minutes after it starts (confirmed via `fly machine status` event logs: a clean
flyd exit with requested_stop=true at exactly +300s), overriding auto_stop_machines=false in
both fly.*.toml. There's no way around the 5-minute window without adding a card to the Fly
account (lifts the trial cap, same quoted ~$7-8/month either way) -- this script just makes
the most of the window: run it, then call within ~4 minutes.
#>

$fly = "$env:USERPROFILE\.fly\bin\fly.exe"
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Starting brain..."
& $fly machine start 286552e6bee548 --config "$repoRoot\fly.brain.toml"

Write-Host "Starting pipeline..."
& $fly machine start d895470c042378 --config "$repoRoot\fly.pipeline.toml"

Write-Host ""
Write-Host "Both machines starting now. Place your call within ~4 minutes --" -ForegroundColor Yellow
Write-Host "Fly's trial tier force-stops them 5 minutes after start, mid-call or not." -ForegroundColor Yellow
