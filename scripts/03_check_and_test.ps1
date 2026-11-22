Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = "C:\kaleido_factory"
$MaxLines = 250
$Violations = @()

Get-ChildItem -Path (Join-Path $Root "src") -Filter "*.py" -Recurse | ForEach-Object {
    $lines = @((Get-Content -LiteralPath $_.FullName)).Count
    if ($lines -gt $MaxLines) {
        $Violations += "$($_.FullName): $lines righe (max $MaxLines)"
    }
}

if ($Violations.Count -gt 0) {
    $Violations | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    exit 1
}

Write-Host "Tutti i moduli in src/ sono <= $MaxLines righe." -ForegroundColor Green
python -m pytest -q