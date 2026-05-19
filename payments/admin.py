from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ['order_id','user','course','amount','status','razorpay_payment_id','created_at','paid_at']
    list_filter   = ['status','created_at']
    search_fields = ['user__username','course__title','razorpay_order_id','razorpay_payment_id']
    readonly_fields = ['order_id','razorpay_order_id','razorpay_payment_id','razorpay_signature','created_at','paid_at']
    ordering      = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user','course')
