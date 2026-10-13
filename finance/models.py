from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

class Category(models.Model):
    KIND_CHOICES = [("income", "Income"), ("expense", "Expense")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="finance_categories")
    name = models.CharField(max_length=60)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default="expense")
    color = models.CharField(max_length=7, default="#6478f5")
    icon = models.CharField(max_length=24, default="circle-dollar-sign")
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name", "kind"], name="unique_user_category_kind")
        ]

    def __str__(self):
        return f"{self.name} ({self.kind})"

class Transaction(models.Model):
    KIND_CHOICES = [("income", "Income"), ("expense", "Expense")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    title = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    date = models.DateField(default=timezone.localdate)
    note = models.TextField(blank=True)
    receipt = models.FileField(upload_to="receipts/%Y/%m/", blank=True, null=True)
    INCOME_SOURCE_CHOICES = [
        ("pocket_money", "Pocket money / Allowance"),
        ("salary", "Salary"),
        ("freelance", "Freelancing"),
        ("scholarship", "Scholarship"),
        ("gift", "Gift"),
        ("part_time", "Part-time work"),
        ("other", "Other"),
    ]
    income_source = models.CharField(max_length=20, choices=INCOME_SOURCE_CHOICES, blank=True)
    is_recurring = models.BooleanField(default=False, help_text="Mark regular expenses such as recharge or subscriptions.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [models.Index(fields=["user", "date"]), models.Index(fields=["user", "kind"])]

    def __str__(self):
        return f"{self.title} — {self.amount}"

class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, limit_choices_to={"kind": "expense"})
    month = models.DateField(help_text="Choose any date in the target month.")
    limit_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-month", "category__name"]
        constraints = [models.UniqueConstraint(fields=["user", "category", "month"], name="unique_budget_user_category_month")]

    def spent(self):
        return Transaction.objects.filter(
            user=self.user, category=self.category, kind="expense",
            date__year=self.month.year, date__month=self.month.month
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    def percent_used(self):
        if not self.limit_amount:
            return 0
        return min(100, int((self.spent() / self.limit_amount) * 100))

    def __str__(self):
        return f"{self.category.name} budget — {self.month:%b %Y}"

class SavingsGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="savings_goals")
    title = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    saved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    target_date = models.DateField(blank=True, null=True)
    color = models.CharField(max_length=7, default="#22b8a7")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["target_date", "title"]

    def percent_complete(self):
        if not self.target_amount:
            return 0
        return min(100, int((self.saved_amount / self.target_amount) * 100))

    def remaining(self):
        return max(Decimal("0.00"), self.target_amount - self.saved_amount)

    def __str__(self):
        return self.title


class AllowancePlan(models.Model):
    FREQUENCY_CHOICES = [("weekly", "Weekly"), ("monthly", "Monthly"), ("custom", "Custom / irregular")]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="allowance_plan")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default="monthly")
    next_date = models.DateField(blank=True, null=True)
    note = models.CharField(max_length=180, blank=True, help_text="Optional note, e.g. hostel and travel allowance")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s {self.get_frequency_display()} allowance"

class MoneyPocket(models.Model):
    """A simple envelope budget for a user's money."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="money_pockets")
    name = models.CharField(max_length=60)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    color = models.CharField(max_length=7, default="#789477")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["user", "name"], name="unique_money_pocket_user_name")]

    def spent(self):
        return Transaction.objects.filter(user=self.user, kind="expense", category__name__iexact=self.name).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    def remaining(self):
        return max(Decimal("0.00"), self.target_amount - self.spent())

    def percent_used(self):
        if not self.target_amount:
            return 0
        return min(100, int(self.spent() / self.target_amount * 100))


class SavingsChallenge(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("completed", "Completed"), ("paused", "Paused")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="savings_challenges")
    title = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    saved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="active")

    class Meta:
        ordering = ["status", "end_date", "title"]

    def percent_complete(self):
        return min(100, int(self.saved_amount / self.target_amount * 100)) if self.target_amount else 0
