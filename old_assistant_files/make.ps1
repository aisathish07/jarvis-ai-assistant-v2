param($cmd)
switch ($cmd) {
    "run"   { python main_minimal.py }
    "test"  { python -m pytest -v }
    "lint"  { ruff check .; ruff format --check . }
    "watch" { python -m watchdog.cli auto --pattern="*.py" --command="python -m pytest -xvs" . }
    default { Write-Host "Usage: .\make.ps1 <run|test|lint|watch>" }
}