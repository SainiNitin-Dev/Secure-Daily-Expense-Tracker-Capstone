from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Expense(models.Model):
    class Category(models.TextChoices):
        FOOD = "Food"
        TRAVEL = "Travel"
        EDUCATION = "Education"
        SHOPPING = "Shopping"
        MEDICAL = "Medical"
        OTHER = "Other"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=9, choices=Category.choices)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    date = models.DateField()
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-date", "-id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="expense_amount_positive"),
        ]


class FailedLoginAttempt(models.Model):
    attempted_at = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=150, blank=True)
