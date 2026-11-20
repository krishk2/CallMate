# Starts brain + pipeline + an ngrok tunnel, then points the Twilio number's webhook at the
# fresh tunnel URL automatically (free ngrok assigns a new random domain every restart, so
# this has to happen every time rather than once).

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $repoRoot ".env"

function Resolve-Ngrok {
    $cmd = Get-Command ngrok -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $found = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter "ngrok.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { return $found.FullName }
    throw "ngrok.exe not found. Install it with: winget install ngrok.ngrok"
}

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

Write-Host "Stopping any stale services on ports 8000/8001, and any running ngrok..."
Get-NetTCPConnection -LocalPort 8000, 8001 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Write-Host "Starting brain on port 8001..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$repoRoot'; uv run uvicorn callmate_brain.main:app --port 8001"
) -WindowStyle Normal

Write-Host "Starting pipeline on port 8000..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$repoRoot'; uv run uvicorn callmate_pipeline.main:app --port 8000"
) -WindowStyle Normal

Write-Host "Waiting for both services to come up..."
Start-Sleep -Seconds 4

Write-Host "Starting ngrok tunnel on port 8000..."
$ngrok = Resolve-Ngrok
Start-Process -FilePath $ngrok -ArgumentList "http", "8000" -WindowStyle Hidden

Write-Host "Waiting for the tunnel to come up..."
$publicUrl = $null
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $tunnels = (Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -ErrorAction Stop).tunnels
        $https = $tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
        if ($https) { $publicUrl = $https.public_url; break }
    } catch {}
}
if (-not $publicUrl) { throw "ngrok tunnel did not come up in time." }
Write-Host "Tunnel is live: $publicUrl"

(Get-Content $envPath) | ForEach-Object {
    if ($_ -match '^PUBLIC_BASE_URL=') { "PUBLIC_BASE_URL=$publicUrl" } else { $_ }
} | Set-Content $envPath
Write-Host "Updated .env PUBLIC_BASE_URL -> $publicUrl"

$sid = $envMap["TWILIO_ACCOUNT_SID"]
$token = $envMap["TWILIO_AUTH_TOKEN"]
$number = $envMap["TWILIO_NUMBER"]

if ($sid -and $token -and $number) {
    try {
        Write-Host "Looking up the Twilio phone number SID..."
        $cred = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${sid}:${token}"))
        $headers = @{ Authorization = "Basic $cred" }
        $encodedNumber = [Uri]::EscapeDataString($number)
        $lookup = Invoke-RestMethod -Uri "https://api.twilio.com/2010-04-01/Accounts/$sid/IncomingPhoneNumbers.json?PhoneNumber=$encodedNumber" -Headers $headers
        $pnSid = $lookup.incoming_phone_numbers[0].sid

        if ($pnSid) {
            $voiceUrl = "$publicUrl/twilio/voice"
            $statusUrl = "$publicUrl/twilio/status"
            $bodyPairs = @(
                "VoiceUrl=$([Uri]::EscapeDataString($voiceUrl))",
                "VoiceMethod=POST",
                "StatusCallback=$([Uri]::EscapeDataString($statusUrl))",
                "StatusCallbackMethod=POST"
            ) -join "&"
            Invoke-RestMethod -Uri "https://api.twilio.com/2010-04-01/Accounts/$sid/IncomingPhoneNumbers/$pnSid.json" `
                -Method Post -Headers $headers -Body $bodyPairs -ContentType "application/x-www-form-urlencoded" | Out-Null
            Write-Host "Twilio webhook updated -> $voiceUrl"
        } else {
            Write-Warning "No Twilio phone number matching $number was found; webhook not updated."
        }
    } catch {
        Write-Warning "Could not update the Twilio webhook automatically: $_"
    }
} else {
    Write-Warning "TWILIO_ACCOUNT_SID/AUTH_TOKEN/NUMBER missing from .env; skipping webhook update."
}

Write-Host ""
Write-Host "All set:"
Write-Host "  brain:    http://localhost:8001/healthz"
Write-Host "  pipeline: http://localhost:8000/healthz"
Write-Host "  public:   $publicUrl"
if ($number) { Write-Host "  Call $number to test." }
