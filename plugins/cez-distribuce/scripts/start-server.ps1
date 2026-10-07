$ErrorActionPreference = 'Stop'
$cezRoot = Split-Path -Parent $PSScriptRoot
$cezPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $cezPython)) {
    $cezPython = (Get-Command python.exe -ErrorAction Stop).Source
}
$env:PYTHONUTF8 = '1'
& $cezPython -B -u (Join-Path $cezRoot 'server.py')
exit $LASTEXITCODE
