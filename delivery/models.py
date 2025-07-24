from django.db import models
from orders.models import Order

class Delivery(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    delivery_status = models.CharField(max_length=50, default='pending')
    delivery_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Delivery for Order {self.order.id}"