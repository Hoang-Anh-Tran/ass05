from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAYMENT_RESERVED', 'Payment Reserved'),
        ('SHIPPING_RESERVED', 'Shipping Reserved'),
        ('CONFIRMED', 'Confirmed'),
        ('FAILED', 'Failed'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('SHIPPING_FAILED', 'Shipping Failed'),
        ('COMPENSATING', 'Compensating'),
    ]
    customer_id = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    pay_method = models.CharField(max_length=50, default='credit_card')
    ship_method = models.CharField(max_length=50, default='standard')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"


class SagaLog(models.Model):
    """Tracks each step of the saga orchestration for an order."""
    STEP_CHOICES = [
        ('ORDER_CREATED', 'Order Created'),
        ('PAYMENT_RESERVE', 'Payment Reserve'),
        ('PAYMENT_RESERVE_FAILED', 'Payment Reserve Failed'),
        ('SHIPPING_RESERVE', 'Shipping Reserve'),
        ('SHIPPING_RESERVE_FAILED', 'Shipping Reserve Failed'),
        ('ORDER_CONFIRMED', 'Order Confirmed'),
        ('COMPENSATION_PAYMENT_CANCEL', 'Compensation: Payment Cancel'),
        ('COMPENSATION_SHIPPING_CANCEL', 'Compensation: Shipping Cancel'),
        ('SAGA_COMPLETED', 'Saga Completed'),
        ('SAGA_FAILED', 'Saga Failed'),
    ]
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='saga_logs')
    step = models.CharField(max_length=50, choices=STEP_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    details = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"SagaLog Order#{self.order_id} - {self.step} ({self.status})"
