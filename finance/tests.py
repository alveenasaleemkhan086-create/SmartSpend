from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Category, Transaction, SavingsGoal

class SmartSpendTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="SafePassword123")
        self.category = Category.objects.filter(user=self.user, kind="expense").first()

    def test_registration_creates_default_categories(self):
        self.assertTrue(Category.objects.filter(user=self.user, kind="expense").exists())
        self.assertTrue(Category.objects.filter(user=self.user, kind="income").exists())

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_user_only_sees_own_transactions(self):
        other = User.objects.create_user(username="other", password="SafePassword123")
        other_category = Category.objects.filter(user=other, kind="expense").first()
        Transaction.objects.create(user=other, category=other_category, kind="expense", title="Private", amount=Decimal("10.00"), date=date.today())
        self.client.login(username="tester", password="SafePassword123")
        response = self.client.get(reverse("transaction_list"))
        self.assertNotContains(response, "Private")

    def test_goal_progress_is_capped(self):
        goal = SavingsGoal.objects.create(user=self.user, title="Laptop", target_amount=Decimal("100.00"), saved_amount=Decimal("120.00"))
        self.assertEqual(goal.percent_complete(), 100)
