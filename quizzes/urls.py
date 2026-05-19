from django.urls import path
from . import views

app_name = 'quizzes'
urlpatterns = [
    path('<int:quiz_id>/', views.quiz_detail, name='detail'),
    path('<int:quiz_id>/take/', views.quiz_take, name='take'),
    path('<int:quiz_id>/submit/', views.quiz_submit, name='submit'),
    path('result/<int:attempt_id>/', views.quiz_result, name='result'),
    path('create/<int:module_id>/', views.quiz_create, name='create'),
    path('manage/<int:quiz_id>/', views.quiz_manage, name='manage'),
    path('manage/<int:quiz_id>/add-question/', views.add_question, name='add_question'),
]
