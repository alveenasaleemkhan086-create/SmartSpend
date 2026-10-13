from django.contrib import admin
from .models import Category, Transaction, Budget, SavingsGoal, AllowancePlan

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "user", "is_default")
    list_filter = ("kind", "is_default")

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "kind", "category", "amount", "date")
    list_filter = ("kind", "date", "category")
    search_fields = ("title", "user__username", "note")

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "month", "limit_amount")

@admin.register(AllowancePlan)
class AllowancePlanAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "frequency", "next_date")

@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "target_amount", "saved_amount", "target_date")

from .models import MoneyPocket, SavingsChallenge

@admin.register(MoneyPocket)
class MoneyPocketAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "target_amount", "color")
    search_fields = ("name", "user__username")

@admin.register(SavingsChallenge)
class SavingsChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "target_amount", "saved_amount", "status", "end_date")
    list_filter = ("status",)
    search_fields = ("title", "user__username")
