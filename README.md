# SmartSpend 360 — Student Edition

A student-friendly personal finance manager built with Django templates, Django views/forms, SQLite, HTML, CSS and vanilla JavaScript. **Django REST Framework is not used.** The interface uses a Sage Green + Cream palette and responsive layouts for desktop and mobile browsers.

## Features
- Registration, login/logout, profile and per-user data isolation
- Income and expenses with student-friendly categories, pocket money/allowance, scholarships, gifts, salary and freelance income
- Monthly budgets with spending progress and alerts
- Savings goals and savings challenges
- Money pockets/envelope budgets (name a pocket to match an expense category for automatic spend totals)
- Monthly expense calendar
- Recurring expense list
- Spending insights and month-over-month comparison
- Transaction search and filters
- CSV export and CSV import (required columns: `date,kind,title,category,amount`; optional `note`; date format `YYYY-MM-DD`)
- Django admin
- Responsive navigation, forms, cards and tables

## Windows setup (PowerShell)
Open the folder containing `manage.py` in VS Code. In the terminal:

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations finance
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. To use another port, run `python manage.py runserver 8001` and open `http://127.0.0.1:8001/`.

## Notes
- SQLite is configured by default; no MySQL setup is required for local development.
- CSV import creates matching categories when needed. Review the file before importing; importing the same file twice can create duplicates.
- This is a local learning/portfolio project, not a bank-connected financial product. Reminders currently provide a list of recurring expenses; they do not send push notifications or schedule background jobs.
- Before public deployment, configure a strong `SECRET_KEY`, `DEBUG=False`, allowed hosts, HTTPS, and production static/media storage.
