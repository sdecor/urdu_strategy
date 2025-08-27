Param(
  [string]$Root = "."
)

# Remplace les lignes qui loggent des headers [TRADE] ou [AUTH] par la version sanitizée
$files = Get-ChildItem -Path $Root -Recurse -Include *.py | Where-Object { -not $_.PSIsContainer }

foreach ($f in $files) {
    $content = Get-Content -Path $f.FullName -Raw

    # Inject import sanitize_headers si on détecte un log headers
    if ($content -match "\[(TRADE|AUTH|POSITION|ORDER|FLATTEN|API)\]\s*Headers:\s*\{") {
        if ($content -notmatch "from utils\.log_sanitizer import sanitize_headers") {
            $content = "from utils.log_sanitizer import sanitize_headers`r`n" + $content
        }
    }

    # Remplacement des logs headers directs -> sanitize_headers(headers)
    $content = $content -replace "(\[.*?\]\s*Headers:\s*)\{?headers\}?", '$1{sanitize_headers(headers)}'

    Set-Content -Path $f.FullName -Value $content -Encoding UTF8
}

Write-Host "✅ Remplacement terminé. Vérifie les imports ajoutés."
