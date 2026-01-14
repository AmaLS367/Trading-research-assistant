# Run linting and type checking

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

Set-Location $ProjectRoot

$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCmd) {
    Write-Host "Running ruff check..."
    uv run ruff check .
    Write-Host "Running mypy..."
    uv run mypy .
} else {
    Write-Host "Running ruff check..."
    ruff check .
    Write-Host "Running mypy..."
    mypy .
}

Write-Host "All checks passed!"
