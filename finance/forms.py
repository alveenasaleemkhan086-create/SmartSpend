from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Transaction, Category, Budget, SavingsGoal, AllowancePlan, MoneyPocket, SavingsChallenge

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=40, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "email", "password1", "password2")

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["kind", "title", "amount", "category", "date", "income_source", "is_recurring", "note", "receipt"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 3, "placeholder": "Optional note..."}),
            "income_source": forms.Select(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["income_source"].required = False
        self.fields["income_source"].help_text = "For income transactions, choose where the money came from."
        self.fields["is_recurring"].required = False
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)

    def clean(self):
        cleaned = super().clean()
        category = cleaned.get("category")
        kind = cleaned.get("kind")
        if kind == "expense":
            cleaned["income_source"] = ""
        if kind == "income":
            cleaned["is_recurring"] = False
        if category and kind and category.kind != kind:
            self.add_error("category", "Choose a category matching the transaction type.")
        if category and self.user and category.user_id != self.user.id:
            self.add_error("category", "Choose one of your own categories.")
        return cleaned

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ["category", "month", "limit_amount"]
        widgets = {"month": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user, kind="expense")

class SavingsGoalForm(forms.ModelForm):
    class Meta:
        model = SavingsGoal
        fields = ["title", "target_amount", "saved_amount", "target_date", "color"]
        widgets = {"target_date": forms.DateInput(attrs={"type": "date"})}


class AllowancePlanForm(forms.ModelForm):
    class Meta:
        model = AllowancePlan
        fields = ["amount", "frequency", "next_date", "note"]
        widgets = {
            "next_date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.TextInput(
                attrs={
                    "placeholder": "e.g. college travel and canteen money"
                }
            ),
        }
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {"first_name": forms.TextInput(attrs={"placeholder": "First name"}), "last_name": forms.TextInput(attrs={"placeholder": "Last name"}), "email": forms.EmailInput(attrs={"placeholder": "you@example.com"})}


class MoneyPocketForm(forms.ModelForm):
    class Meta:
        model = MoneyPocket
        fields = ["name", "target_amount", "color"]
        widgets = {"name": forms.TextInput(attrs={"placeholder": "e.g. Food, Travel, Books"})}

class SavingsChallengeForm(forms.ModelForm):
    class Meta:
        model = SavingsChallenge
        fields = ["title", "target_amount", "saved_amount", "start_date", "end_date", "status"]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}), "end_date": forms.DateInput(attrs={"type": "date"})}
