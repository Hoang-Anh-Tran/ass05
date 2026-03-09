from django.db import models

class Order(models.Model):
    customer_id = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='PENDING')
    pay_method = models.CharField(max_length=50, default='credit_card')
    ship_method = models.CharField(max_length=50, default='standard')
    created_at = models.DateTimeField(auto_now_add=True)
