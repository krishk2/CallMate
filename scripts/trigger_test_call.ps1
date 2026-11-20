param(
    [string]$To,
    [string]$BaseUrl  # e.g. https://callmate-pipeline.fly.dev to test the deployed app
                       # instead of your local/ngrok one. Defaults to .env's PUBLIC_BASE_URL.
)

# Calls pipeline's own POST /v1/calls/outbound (telephony/outbound.py) rather than hitting
# Twilio directly — that endpoint is the real, documented way to trigger an outbound call
# (see docs/demo.md), this script is just a thin convenience wrapper over it. Works around
# India's outbound-ISD restriction since receiving an international call needs no special
# permission, only dialing one out does.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $repoRoot ".env"

function Read-DotEnv($path) {
    $map = @{}
    Get-Content $path | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { return }
        $key = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()
        $hashIdx = $value.IndexOf("#")
        if ($hashIdx -ge 0) { $value = $value.Substring(0, $hashIdx).Trim() }
        $map[$key] = $value
    }
    return $map
}

$envMap = Read-DotEnv $envPath
$serviceToken = $envMap["SERVICE_TOKEN"]
if (-not $BaseUrl) { $BaseUrl = $envMap["PUBLIC_BASE_URL"] }

if (-not $To) { $To = $envMap["TEST_CALLER_NUMBER"] }
if (-not $To) {
    throw "No number to call. Pass -To +91..., or set TEST_CALLER_NUMBER in .env."
}
if (-not $serviceToken -or -not $BaseUrl) {
    throw "SERVICE_TOKEN missing from .env, or no -BaseUrl / PUBLIC_BASE_URL set."
}

$body = @{ to = $To; service_token = $serviceToken } | ConvertTo-Json

Write-Host "Calling $To via $BaseUrl/v1/calls/outbound ..."
$response = Invoke-RestMethod -Uri "$BaseUrl/v1/calls/outbound" `
    -Method Post -Body $body -ContentType "application/json"

Write-Host "Triggered. CallSid: $($response.call_sid)  status: $($response.status)"
Write-Host "Your phone should ring in a few seconds."
