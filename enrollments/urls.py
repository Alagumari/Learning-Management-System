from django.urls import path
from . import views

app_name = 'enrollments'
urlpatterns = [
    path('enroll/<slug:slug>/', views.enroll, name='enroll'),
    path('learn/<slug:slug>/<int:lesson_id>/', views.learn, name='learn'),
    path('mark-complete/<int:lesson_id>/', views.mark_complete, name='mark_complete'),
    path('save-progress/<int:lesson_id>/', views.save_progress, name='save_progress'),
]
