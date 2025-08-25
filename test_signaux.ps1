# PowerShell script to send two fake trading signals via curl
# Usage: run this script from PowerShell: ./send_signals.ps1

# Fichier NDJSON cible (ajustable si nécessaire)
$targetFile = "signals.ndjson"

# Génère deux timestamps UTC actuels (à 1s d’intervalle)
$timestamp1 = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ")
Start-Sleep -Milliseconds 500
$timestamp2 = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ")

# Données JSON formatées en NDJSON
$signal1 = @{ timestamp = $timestamp1; instrument = "UB1!"; position = -1; content_type = "text/plain" } | ConvertTo-Json -Compress
$signal2 = @{ timestamp = $timestamp2; instrument = "UB1!"; position = 0; content_type = "text/plain" } | ConvertTo-Json -Compress

# Ajoute les deux lignes au fichier NDJSON
$signal1 | Out-File -FilePath $targetFile -Encoding utf8 -Append
$signal2 | Out-File -FilePath $targetFile -Encoding utf8 -Append

Write-Host "`n✅ Deux signaux ont été envoyés à $targetFile :"
Write-Host $signal1
Write-Host $signal2
