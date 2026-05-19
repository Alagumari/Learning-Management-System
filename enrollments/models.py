from django.db import models
from django.conf import settings
from courses.models import Course, Lesson

class Enrollment(models.Model):
    STATUS = [('active','Active'),('completed','Completed'),('dropped','Dropped')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    progress = models.FloatField(default=0.0)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    last_lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        unique_together = ['user','course']
        ordering = ['-enrolled_at']

    def calculate_progress(self):
        total = Lesson.objects.filter(module__course=self.course).count()
        if not total: return 0.0
        completed = LessonProgress.objects.filter(enrollment=self, is_completed=True).count()
        return round((completed / total) * 100, 1)

    def update_progress(self):
        self.progress = self.calculate_progress()
        if self.progress >= 100:
            from django.utils import timezone
            self.status = 'completed'
            self.completed_at = timezone.now()
            # Auto-generate certificate
            from certificates.models import Certificate
            cert, created = Certificate.objects.get_or_create(
                user=self.user, course=self.course,
                defaults={'enrollment': self}
            )
            if created:
                from courses.models import Notification
                Notification.objects.create(
                    user=self.user, title='🎉 Course Completed!',
                    message=f'Congratulations! You completed "{self.course.title}". Your certificate is ready.',
                    notif_type='certificate',
                    link=f'/certificates/{cert.certificate_id}/'
                )
        self.save()

    def __str__(self): return f"{self.user.username} - {self.course.title}"

class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
    is_completed = models.BooleanField(default=False)
    watch_time = models.PositiveIntegerField(default=0, help_text='Seconds watched')
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['enrollment','lesson']

    def __str__(self): return f"{self.enrollment.user.username} - {self.lesson.title}"
