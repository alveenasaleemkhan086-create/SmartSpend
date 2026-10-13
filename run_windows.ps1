# Run this script from the extracted SmartSpend360 folder (the folder containing manage.py).
if (!(Test-Path .\manage.py)) { Write-Host "Open the inner SmartSpend360 folder containing manage.py first." -ForegroundColor Yellow; exit 1 }
if (!(Test-Path .\venv)) { python -m venv venv }
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
Write-Host "Setup complete. Run: python manage.py runserver 8001" -ForegroundColor Green
