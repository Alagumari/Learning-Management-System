from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='list'),
    path('create/', views.course_create, name='create'),

    # static routes first
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:course_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),

    # slug routes after
    path('<slug:slug>/', views.course_detail, name='detail'),
    path('<slug:slug>/edit/', views.course_edit, name='edit'),
    path('<slug:slug>/delete/', views.course_delete, name='delete'),
    path('<slug:slug>/publish/', views.course_publish, name='publish'),
    path('<slug:slug>/modules/', views.module_list, name='modules'),
    path('<slug:slug>/modules/add/', views.module_add, name='module_add'),
    path('<slug:slug>/review/', views.add_review, name='add_review'),

    path('module/<int:module_id>/edit/', views.module_edit, name='module_edit'),
    path('module/<int:module_id>/delete/', views.module_delete, name='module_delete'),
    path('module/<int:module_id>/lesson/add/', views.lesson_add, name='lesson_add'),
    path('lesson/<int:lesson_id>/edit/', views.lesson_edit, name='lesson_edit'),
    path('lesson/<int:lesson_id>/delete/', views.lesson_delete, name='lesson_delete'),
]