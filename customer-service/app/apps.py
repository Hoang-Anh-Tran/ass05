from django.apps import AppConfig


class AppConfig(AppConfig):
    name = "app"

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(seed_accounts, sender=self)


def seed_accounts(sender, **kwargs):
    from .models import Customer
    import requests

    # Seed admin
    if not Customer.objects.filter(email="admin@bookstore.com").exists():
        Customer.objects.create(
            name="Admin",
            email="admin@bookstore.com",
            password="admin123",
            role="admin"
        )

    # Seed staff
    if not Customer.objects.filter(email="staff@bookstore.com").exists():
        Customer.objects.create(
            name="Staff",
            email="staff@bookstore.com",
            password="staff123",
            role="staff"
        )
