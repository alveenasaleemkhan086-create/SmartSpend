from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from finance import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.landing, name="landing"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/add/", views.transaction_create, name="transaction_create"),
    path("transactions/<int:pk>/edit/", views.transaction_update, name="transaction_update"),
    path("transactions/<int:pk>/delete/", views.transaction_delete, name="transaction_delete"),
    path("transactions/export/csv/", views.export_transactions_csv, name="export_transactions_csv"),
    path("budgets/", views.budget_list, name="budget_list"),
    path("budgets/add/", views.budget_create, name="budget_create"),
    path("goals/", views.goal_list, name="goal_list"),
    path("goals/add/", views.goal_create, name="goal_create"),
    path("allowance/", views.allowance_settings, name="allowance_settings"),
    path("profile/", views.profile, name="profile"),
    path("insights/", views.insights, name="insights"),
    path("pockets/", views.pockets, name="pockets"),
    path("pockets/add/", views.pocket_create, name="pocket_create"),
    path("challenges/", views.challenges, name="challenges"),
    path("challenges/add/", views.challenge_create, name="challenge_create"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("reminders/", views.reminders, name="reminders"),
    path("transactions/import/", views.import_transactions_csv, name="import_transactions_csv"),
]
