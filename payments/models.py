from django.db import models
from django.conf import settings
from courses.models import Course
import uuid

class Order(models.Model):
    STATUS = [
        ('pending',  'Pending'),
        ('paid',     'Paid'),
        ('failed',   'Failed'),
        ('refunded', 'Refunded'),
    ]
    order_id           = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user               = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    course             = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='orders')
    amount             = models.DecimalField(max_digits=10, decimal_places=2)
    status             = models.CharField(max_length=20, choices=STATUS, default='pending')
    payment_method     = models.CharField(max_length=50, default='razorpay')
    razorpay_order_id  = models.CharField(max_length=200, blank=True)
    razorpay_payment_id= models.CharField(max_length=200, blank=True)
    razorpay_signature = models.CharField(max_length=400, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    paid_at            = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} – {self.course.title} ({self.status})"
