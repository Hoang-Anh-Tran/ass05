"""
Load Testing Script for Bookstore Microservices
Requires: pip install locust

Usage:
    locust -f load_test.py --host=http://localhost:4000
    
Then open http://localhost:8089 in your browser to start the test.
"""
import json
import random
from locust import HttpUser, task, between, events


class BookstoreUser(HttpUser):
    """Simulates a typical bookstore user workflow."""
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """Register and login to get JWT token."""
        email = f"loadtest_{random.randint(10000, 99999)}@test.com"
        password = "loadtest123"

        # Register
        self.client.post("/auth/register/", json={
            "name": f"Load Test User {random.randint(1, 1000)}",
            "email": email,
            "password": password,
            "role": "customer",
        })

        # Login
        resp = self.client.post("/auth/login/", json={
            "email": email,
            "password": password,
        })
        if resp.status_code == 200:
            self.token = resp.json().get("access")

    @property
    def auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(5)
    def browse_books(self):
        """Browse book catalog - most common action."""
        self.client.get("/books/", headers=self.auth_headers)

    @task(3)
    def view_health(self):
        """Check system health."""
        self.client.get("/health/")

    @task(2)
    def view_metrics(self):
        """Check metrics."""
        self.client.get("/metrics/")

    @task(2)
    def browse_catalog(self):
        """Browse vouchers."""
        self.client.get("/catalog/vouchers/", headers=self.auth_headers)

    @task(1)
    def create_order(self):
        """Create an order - triggers saga pattern."""
        self.client.post("/orders/", json={
            "customer_id": random.randint(1, 100),
            "total_amount": str(round(random.uniform(10, 200), 2)),
            "pay_method": random.choice(["credit_card", "paypal", "cod"]),
            "ship_method": random.choice(["standard", "express", "overnight"]),
        }, headers=self.auth_headers)

    @task(1)
    def view_orders(self):
        """View order list."""
        self.client.get("/orders/list/", headers=self.auth_headers)

    @task(1)
    def browse_comments(self):
        """Browse comments."""
        self.client.get("/comments/", headers=self.auth_headers)


class AdminUser(HttpUser):
    """Simulates an admin user checking observability endpoints."""
    wait_time = between(5, 10)
    weight = 1  # Lower weight = fewer admin users

    @task(3)
    def check_health(self):
        self.client.get("/health/")

    @task(2)
    def check_metrics(self):
        self.client.get("/metrics/")

    @task(1)
    def check_gateway_home(self):
        self.client.get("/")
