from django.db import models
from django.contrib.auth.hashers import make_password, check_password as django_check_password


class AuthUser(models.Model):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Stored as hashed
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.name} ({self.role})"


class RefreshToken(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.CharField(max_length=500, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_revoked = models.BooleanField(default=False)

    def __str__(self):
        return f"RefreshToken for {self.user.email}"
