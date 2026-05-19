from django.urls import path
from . import views

app_name = 'dashboard'
urlpatterns = [
    path('', views.index, name='index'),
    path('student/', views.student_dashboard, name='student'),
    path('instructor/', views.instructor_dashboard, name='instructor'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('approve-course/<int:course_id>/', views.approve_course, name='approve_course'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('toggle-user/<int:user_id>/', views.toggle_user_status, name='toggle_user'),
]
