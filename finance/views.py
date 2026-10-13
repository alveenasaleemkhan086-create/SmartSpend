import csv
from datetime import date, timedelta
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import RegisterForm, TransactionForm, BudgetForm, SavingsGoalForm, AllowancePlanForm, ProfileForm
from .models import Transaction, Category, Budget, SavingsGoal, AllowancePlan

def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "finance/landing.html")

def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to SmartSpend 360! Your workspace is ready.")
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    transactions = Transaction.objects.filter(user=request.user)
    month_transactions = transactions.filter(date__year=today.year, date__month=today.month)
    income = month_transactions.filter(kind="income").aggregate(total=Sum("amount"))["total"] or Decimal("0")
    expenses = month_transactions.filter(kind="expense").aggregate(total=Sum("amount"))["total"] or Decimal("0")
    all_income = transactions.filter(kind="income").aggregate(total=Sum("amount"))["total"] or Decimal("0")
    all_expenses = transactions.filter(kind="expense").aggregate(total=Sum("amount"))["total"] or Decimal("0")
    budgets = Budget.objects.filter(user=request.user, month__year=today.year, month__month=today.month).select_related("category")
    for budget in budgets:
        budget.actual_spent = budget.spent()
        budget.usage_percent = budget.percent_used()
    category_totals = list(month_transactions.filter(kind="expense").values("category__name", "category__color").annotate(total=Sum("amount")).order_by("-total")[:6])
    context = {
        "month_name": today.strftime("%B %Y"),
        "income": income, "expenses": expenses, "net": income - expenses,
        "balance": all_income - all_expenses,
        "recent_transactions": transactions.select_related("category")[:6],
        "budgets": budgets[:4],
        "goals": SavingsGoal.objects.filter(user=request.user)[:3],
        "category_totals": category_totals,
        "transaction_count": month_transactions.count(),
        "budget_alerts": [b for b in budgets if b.percent_used() >= 80],
        "allowance_plan": AllowancePlan.objects.filter(user=request.user).first(),
        "pocket_money_received": month_transactions.filter(kind="income", income_source="pocket_money").aggregate(total=Sum("amount"))["total"] or Decimal("0"),
    }
    return render(request, "finance/dashboard.html", context)

@login_required
def transaction_list(request):
    qs = Transaction.objects.filter(user=request.user).select_related("category")
    kind = request.GET.get("kind", "")
    category_id = request.GET.get("category", "")
    search = request.GET.get("q", "").strip()
    start = request.GET.get("start", "")
    end = request.GET.get("end", "")
    if kind in ("income", "expense"):
        qs = qs.filter(kind=kind)
    if category_id.isdigit():
        qs = qs.filter(category_id=category_id)
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(note__icontains=search))
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)
    return render(request, "finance/transaction_list.html", {
        "transactions": qs, "categories": Category.objects.filter(user=request.user),
        "selected_kind": kind, "selected_category": category_id, "search": search,
        "start": start, "end": end,
        "total_filtered": qs.aggregate(total=Sum("amount"))["total"] or Decimal("0"),
    })

@login_required
def transaction_create(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, "Transaction saved successfully.")
            return redirect("transaction_list")
    else:
        initial = {"date": timezone.localdate(), "kind": request.GET.get("kind", "expense")}
        form = TransactionForm(user=request.user, initial=initial)
    return render(request, "finance/transaction_form.html", {"form": form, "page_title": "Add transaction"})

@login_required
def transaction_update(request, pk):
    item = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == "POST":
        form = TransactionForm(request.POST, request.FILES, instance=item, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction updated.")
            return redirect("transaction_list")
    else:
        form = TransactionForm(instance=item, user=request.user)
    return render(request, "finance/transaction_form.html", {"form": form, "page_title": "Edit transaction"})

@login_required
def transaction_delete(request, pk):
    item = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Transaction deleted.")
        return redirect("transaction_list")
    return render(request, "finance/transaction_confirm_delete.html", {"item": item})

@login_required
def export_transactions_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="smartspend-transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(["Date", "Type", "Title", "Category", "Income source", "Recurring", "Amount", "Note"])
    for item in Transaction.objects.filter(user=request.user).select_related("category"):
        writer.writerow([item.date, item.kind, item.title, item.category.name, item.get_income_source_display() if item.income_source else "", "Yes" if item.is_recurring else "No", item.amount, item.note])
    return response

@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user).select_related("category")
    for budget in budgets:
        budget.actual_spent = budget.spent()
        budget.usage_percent = budget.percent_used()
    return render(request, "finance/budget_list.html", {"budgets": budgets})

@login_required
def budget_create(request):
    if request.method == "POST":
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.month = item.month.replace(day=1)
            item.save()
            messages.success(request, "Budget created.")
            return redirect("budget_list")
    else:
        form = BudgetForm(initial={"month": timezone.localdate().replace(day=1)}, user=request.user)
    return render(request, "finance/generic_form.html", {"form": form, "page_title": "Create a budget", "back_url": "budget_list"})

@login_required
def goal_list(request):
    return render(request, "finance/goal_list.html", {"goals": SavingsGoal.objects.filter(user=request.user)})

@login_required
def goal_create(request):
    if request.method == "POST":
        form = SavingsGoalForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, "Savings goal added.")
            return redirect("goal_list")
    else:
        form = SavingsGoalForm()
    return render(request, "finance/generic_form.html", {"form": form, "page_title": "Create a savings goal", "back_url": "goal_list"})

@login_required
def allowance_settings(request):
    plan = AllowancePlan.objects.filter(user=request.user).first()
    if request.method == "POST":
        form = AllowancePlanForm(request.POST, instance=plan)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, "Pocket money plan saved.")
            return redirect("dashboard")
    else:
        form = AllowancePlanForm(instance=plan)
    return render(request, "finance/generic_form.html", {"form": form, "page_title": "Pocket money plan", "back_url": "dashboard", "form_hint": "Set your expected allowance. Record each amount you actually receive as an income transaction so your balance stays accurate."})

@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "finance/generic_form.html", {"form": form, "page_title": "Your profile", "back_url": "dashboard"})

@login_required
def insights(request):
    today = timezone.localdate()
    this_month = Transaction.objects.filter(user=request.user, date__year=today.year, date__month=today.month)
    previous_month_date = (today.replace(day=1) - timedelta(days=1))
    previous_month = Transaction.objects.filter(user=request.user, date__year=previous_month_date.year, date__month=previous_month_date.month)
    def total(qs, kind):
        return qs.filter(kind=kind).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    current_expenses, previous_expenses = total(this_month, "expense"), total(previous_month, "expense")
    current_income = total(this_month, "income")
    difference = current_expenses - previous_expenses
    if previous_expenses:
        change_percent = int((difference / previous_expenses) * 100)
    else:
        change_percent = None
    category_totals = list(this_month.filter(kind="expense").values("category__name", "category__color").annotate(total=Sum("amount")).order_by("-total"))
    recurring = Transaction.objects.filter(user=request.user, kind="expense", is_recurring=True).select_related("category")[:10]
    return render(request, "finance/insights.html", {"month_name": today.strftime("%B %Y"), "current_income": current_income, "current_expenses": current_expenses, "previous_expenses": previous_expenses, "difference": difference, "change_percent": change_percent, "category_totals": category_totals, "recurring": recurring, "transaction_count": this_month.count()})


from .forms import MoneyPocketForm, SavingsChallengeForm
from .models import MoneyPocket, SavingsChallenge
import calendar as pycalendar

@login_required
def pockets(request):
    items = list(MoneyPocket.objects.filter(user=request.user))
    for item in items:
        item.actual_spent = item.spent()
        item.left = item.remaining()
        item.usage = item.percent_used()
    return render(request, "finance/pockets.html", {"pockets": items})

@login_required
def pocket_create(request):
    form = MoneyPocketForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False); item.user = request.user; item.save()
        messages.success(request, "Money pocket created.")
        return redirect("pockets")
    return render(request, "finance/generic_form.html", {"form": form, "page_title": "Create a money pocket", "back_url": "pockets", "form_hint": "Create an envelope for a spending category. Match its name to an expense category for automatic tracking."})

@login_required
def challenges(request):
    return render(request, "finance/challenges.html", {"challenges": SavingsChallenge.objects.filter(user=request.user)})

@login_required
def challenge_create(request):
    form = SavingsChallengeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False); item.user = request.user; item.save()
        messages.success(request, "Savings challenge added.")
        return redirect("challenges")
    return render(request, "finance/generic_form.html", {"form": form, "page_title": "Create a savings challenge", "back_url": "challenges"})

@login_required
def calendar_view(request):
    today = timezone.localdate()
    try:
        year, month = int(request.GET.get("year", today.year)), int(request.GET.get("month", today.month))
        if month < 1 or month > 12: raise ValueError
        first = date(year, month, 1)
    except (ValueError, TypeError):
        first = today.replace(day=1); year, month = first.year, first.month
    last_day = pycalendar.monthrange(year, month)[1]
    rows = Transaction.objects.filter(user=request.user, date__year=year, date__month=month).values("date", "kind").annotate(total=Sum("amount"))
    daily = {}
    for row in rows: daily.setdefault(row["date"].day, {"income": Decimal("0"), "expense": Decimal("0")})[row["kind"]] += row["total"]
    weeks = pycalendar.Calendar(firstweekday=0).monthdayscalendar(year, month)
    return render(request, "finance/calendar.html", {"month_name": first.strftime("%B %Y"), "weeks": weeks, "daily": daily, "prev_year": (first - timedelta(days=1)).year, "prev_month": (first - timedelta(days=1)).month, "next_year": (first.replace(day=last_day) + timedelta(days=1)).year, "next_month": (first.replace(day=last_day) + timedelta(days=1)).month, "year": year, "month": month})

@login_required
def reminders(request):
    items = Transaction.objects.filter(user=request.user, kind="expense", is_recurring=True).select_related("category")
    return render(request, "finance/reminders.html", {"transactions": items})

@login_required
def import_transactions_csv(request):
    result = None
    if request.method == "POST":
        upload = request.FILES.get("csv_file")
        if not upload or not upload.name.lower().endswith(".csv"):
            messages.error(request, "Choose a CSV file to import.")
        else:
            try:
                decoded = upload.read().decode("utf-8-sig").splitlines()
                reader = csv.DictReader(decoded)
                required = {"date", "kind", "title", "category", "amount"}
                if not reader.fieldnames or not required.issubset({h.strip().lower() for h in reader.fieldnames}):
                    raise ValueError("CSV needs columns: date, kind, title, category, amount.")
                headers = {h.strip().lower(): h for h in reader.fieldnames}
                created = 0
                for row in reader:
                    kind = (row.get(headers["kind"]) or "").strip().lower()
                    if kind not in ("income", "expense"): continue
                    category_name = (row.get(headers["category"]) or "Other").strip()[:60]
                    category = Category.objects.filter(user=request.user, name__iexact=category_name, kind=kind).first()
                    if not category: category = Category.objects.create(user=request.user, name=category_name or "Other", kind=kind, is_default=False)
                    Transaction.objects.create(user=request.user, category=category, kind=kind, title=(row.get(headers["title"]) or "Imported transaction")[:120], amount=Decimal((row.get(headers["amount"]) or "0").replace(",", "")), date=date.fromisoformat((row.get(headers["date"]) or "").strip()), note=(row.get(headers.get("note", "")) or "Imported from CSV")[:2000], income_source=(row.get(headers.get("income source", "")) or "other") if kind == "income" else "")
                    created += 1
                messages.success(request, f"Imported {created} transaction(s).")
                return redirect("transaction_list")
            except Exception as exc:
                messages.error(request, f"Could not import this CSV: {exc}")
    return render(request, "finance/import_csv.html")
