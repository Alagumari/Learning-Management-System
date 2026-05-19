from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [('student','Student'),('instructor','Instructor'),('admin','Admin')]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_student(self): return self.role == 'student'
    def is_instructor(self): return self.role == 'instructor'
    def is_admin_user(self): return self.role == 'admin' or self.is_staff
    def get_avatar_url(self):
        if self.avatar: return self.avatar.url
        return '/static/images/default-avatar.png'
    def __str__(self): return f"{self.get_full_name() or self.username} ({self.role})"
