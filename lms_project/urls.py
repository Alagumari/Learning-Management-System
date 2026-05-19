from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from courses import views as course_views

urlpatterns = [
    path('admin/',        admin.site.urls),
    path('',              course_views.home,       name='home'),
    path('accounts/',     include('accounts.urls')),
    path('courses/',      include('courses.urls')),
    path('enrollments/',  include('enrollments.urls')),
    path('quizzes/',      include('quizzes.urls')),
    path('certificates/', include('certificates.urls')),
    path('dashboard/',    include('dashboard.urls')),
    path('payments/',     include('payments.urls')),
] + static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
