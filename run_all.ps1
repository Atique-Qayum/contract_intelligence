# Run the whole demo pipeline on Windows PowerShell:  .\run_all.ps1
# Prereq: python -m venv .venv ; .venv\Scripts\Activate.ps1 ; pip install -r requirements.txt
$ErrorActionPreference = "Stop"
python generate_data.py
python generate_hard.py
python extract.py
python load_db.py
python report.py
python tests/test_pipeline.py
Write-Host "Done. See outputs/report.md"
