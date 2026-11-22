Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = "C:\kaleido_factory"
$DemoPy = Join-Path $Root "scripts\run_demo.py"
$OutDir = Join-Path $Root "output\demo_01"

python $DemoPy

if (Test-Path -LiteralPath $OutDir) {
    Get-ChildItem -Path $OutDir -Recurse -File | Select-Object FullName, Length | Format-Table -AutoSize
}