from django.urls import path
from . import views

app_name = 'payments'
urlpatterns = [
    path('checkout/<slug:slug>/',  views.checkout,         name='checkout'),
    path('verify/',                views.payment_verify,   name='verify'),
    path('webhook/',               views.payment_webhook,  name='webhook'),
    path('success/',               views.payment_success,  name='success'),
    path('failed/',                views.payment_failed,   name='failed'),
    path('history/',               views.payment_history,  name='history'),
]
