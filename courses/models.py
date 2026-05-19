from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='bi-folder')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self): return self.name

class Course(models.Model):
    LEVEL_CHOICES = [('beginner','Beginner'),('intermediate','Intermediate'),('advanced','Advanced'),('all','All Levels')]
    STATUS_CHOICES = [('draft','Draft'),('pending','Pending Review'),('published','Published'),('rejected','Rejected')]
    PRICE_TYPE = [('free','Free'),('paid','Paid')]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses_taught')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    preview_video = models.FileField(upload_to='course_previews/', blank=True, null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='all')
    language = models.CharField(max_length=50, default='English')
    price_type = models.CharField(max_length=10, choices=PRICE_TYPE, default='free')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    requirements = models.TextField(blank=True)
    what_you_learn = models.TextField(blank=True)
    tags = models.CharField(max_length=300, blank=True)
    total_duration = models.PositiveIntegerField(default=0, help_text='In minutes')
    total_lessons = models.PositiveIntegerField(default=0)
    total_enrolled = models.PositiveIntegerField(default=0)
    avg_rating = models.FloatField(default=0.0)
    total_ratings = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    certificate_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"; n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_thumbnail_url(self):
        if self.thumbnail: return self.thumbnail.url
        return '/static/images/default-course.png'

    def get_effective_price(self):
        if self.price_type == 'free': return 0
        if self.discount_price: return self.discount_price
        return self.price

    def update_stats(self):
        from enrollments.models import Enrollment
        self.total_enrolled = Enrollment.objects.filter(course=self, status='active').count()
        lessons = Lesson.objects.filter(module__course=self)
        self.total_lessons = lessons.count()
        self.total_duration = sum(l.duration or 0 for l in lessons)
        reviews = Review.objects.filter(course=self)
        if reviews.exists():
            self.avg_rating = round(sum(r.rating for r in reviews) / reviews.count(), 1)
            self.total_ratings = reviews.count()
        self.save()

    def __str__(self): return self.title

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self): return f"{self.course.title} - {self.title}"

class Lesson(models.Model):
    CONTENT_TYPE = [('video','Video'),('pdf','PDF'),('text','Text/Article'),('quiz','Quiz')]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE, default='video')
    video = models.FileField(upload_to='lesson_videos/', blank=True, null=True)
    video_url = models.URLField(blank=True, help_text='External video URL (YouTube/Vimeo)')
    pdf = models.FileField(upload_to='lesson_pdfs/', blank=True, null=True)
    text_content = models.TextField(blank=True)
    duration = models.PositiveIntegerField(default=0, help_text='In minutes')
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False, help_text='Free preview lesson')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self): return f"{self.module.title} - {self.title}"

class Resource(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='resources/')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['course','user']
        ordering = ['-created_at']

    def __str__(self): return f"{self.user.username} - {self.course.title} ({self.rating}★)"

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user','course']

class Notification(models.Model):
    TYPE_CHOICES = [('enrollment','Enrollment'),('review','Review'),('certificate','Certificate'),('announcement','Announcement'),('system','System')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self): return f"{self.user.username}: {self.title}"
