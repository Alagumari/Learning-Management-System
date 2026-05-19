from django.contrib import admin
from .models import Enrollment, LessonProgress

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user','course','status','progress','enrolled_at']
    list_filter = ['status']
    search_fields = ['user__username','course__title']

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['enrollment','lesson','is_completed','watch_time']
    list_filter = ['is_completed']
