from django.db import models
from accounts.models import CustomUser

class LoyaltyRule(models.Model):
    points_threshold = models.IntegerField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.discount_percentage}% off at {self.points_threshold} points"