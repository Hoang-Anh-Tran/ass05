from django.apps import AppConfig


class AppConfig(AppConfig):
    name = "app"

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(seed_admin, sender=self)


def seed_admin(sender, **kwargs):
    from .models import Customer
    import requests

    if not Customer.objects.filter(email="admin@bookstore.com").exists():
        admin = Customer.objects.create(
            name="Admin",
            email="admin@bookstore.com",
            password="admin123",
            role="admin"
        )
        # Also create a cart for the admin
        try:
            requests.post(
                "http://cart-service:4000/",
                json={"customer_id": admin.id},
                timeout=5
            )
        except Exception:
            pass
