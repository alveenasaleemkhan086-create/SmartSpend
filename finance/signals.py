from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Category

User = get_user_model()

DEFAULT_CATEGORIES = [
    ("Pocket Money", "income", "#22b8a7", "wallet"),
    ("Salary", "income", "#22b8a7", "wallet"),
    ("Scholarship", "income", "#6478f5", "graduation-cap"),
    ("Gift", "income", "#ec6c93", "gift"),
    ("Freelance", "income", "#6478f5", "briefcase-business"),
    ("Food", "expense", "#f59e0b", "utensils"),
    ("Transport", "expense", "#6478f5", "car-front"),
    ("Shopping", "expense", "#ec6c93", "shopping-bag"),
    ("Bills", "expense", "#8b75e8", "receipt"),
    ("Health", "expense", "#22b8a7", "heart-pulse"),
    ("Education", "expense", "#6478f5", "graduation-cap"),
    ("College fees", "expense", "#8b75e8", "school"),
    ("Stationery", "expense", "#22b8a7", "notebook-pen"),
    ("Mobile recharge", "expense", "#f59e0b", "smartphone"),
    ("Hostel / Rent", "expense", "#8b75e8", "building-2"),
    ("Entertainment", "expense", "#f97316", "clapperboard"),
    ("Other", "expense", "#8a96a8", "circle-ellipsis"),
]

@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if created:
        Category.objects.bulk_create([
            Category(user=instance, name=name, kind=kind, color=color, icon=icon, is_default=True)
            for name, kind, color, icon in DEFAULT_CATEGORIES
        ])
