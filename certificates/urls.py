from django.urls import path
from . import views

app_name = 'certificates'
urlpatterns = [
    path('', views.certificate_list, name='list'),
    path('<uuid:cert_id>/', views.certificate_view, name='view'),
    path('<uuid:cert_id>/download/', views.certificate_download, name='download'),
    path('verify/<uuid:cert_id>/', views.verify_certificate, name='verify'),
]
