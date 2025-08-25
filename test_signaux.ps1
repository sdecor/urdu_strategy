# PowerShell script to send two fake trading signals via curl
# Usage: run this script from PowerShell: ./send_signals.ps1

# Webhook local
$webhookUrl = "https://f06e013c12d4.ngrok-free.app/tv_urdu"

# Génère deux timestamps UTC actuels (à 1s d’intervalle)
$timestamp1 = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ")
Start-Sleep -Milliseconds 500
$timestamp2 = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ")

# Crée deux signaux JSON
$signal1 = @{ timestamp = $timestamp1; instrument = "UB1!"; position = -1; content_type = "text/plain" } | ConvertTo-Json -Compress
$signal2 = @{ timestamp = $timestamp2; instrument = "UB1!"; position = 0; content_type = "text/plain" } | ConvertTo-Json -Compress

# Envoie chaque signal via curl
Write-Host "`n🚀 Envoi du signal 1..."
curl -Uri $webhookUrl -Method POST -Body $signal1 -ContentType "application/json"

Write-Host "`n🚀 Envoi du signal 2..."
curl -Uri $webhookUrl -Method POST -Body $signal2 -ContentType "application/json"

Write-Host "`n✅ Deux signaux envoyés à $webhookUrl :"
Write-Host $signal1
Write-Host $signal2
