from django.contrib import admin
from .models import Category, Course, Module, Lesson, Resource, Review, Wishlist, Notification

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name','slug']
    prepopulated_fields = {'slug': ('name',)}

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title','instructor','category','status','level','price_type','total_enrolled','avg_rating','created_at']
    list_filter = ['status','level','price_type','category']
    search_fields = ['title','instructor__username']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]
    actions = ['approve_courses','reject_courses']

    def approve_courses(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{queryset.count()} courses approved.')
    approve_courses.short_description = 'Approve selected courses'

    def reject_courses(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f'{queryset.count()} courses rejected.')
    reject_courses.short_description = 'Reject selected courses'

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title','course','order']
    list_filter = ['course']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title','module','content_type','duration','order','is_preview']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user','course','rating','created_at']
    list_filter = ['rating']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user','title','notif_type','is_read','created_at']
    list_filter = ['notif_type','is_read']
