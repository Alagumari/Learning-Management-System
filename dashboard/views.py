from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Sum

@login_required
def index(request):
    user = request.user
    if user.is_admin_user():
        return admin_dashboard(request)
    elif user.is_instructor():
        return instructor_dashboard(request)
    else:
        return student_dashboard(request)

@login_required
def student_dashboard(request):
    from enrollments.models import Enrollment, LessonProgress
    from certificates.models import Certificate
    from courses.models import Wishlist

    enrollments = Enrollment.objects.filter(user=request.user).select_related('course','last_lesson').order_by('-last_accessed')
    active = enrollments.filter(status='active')
    completed = enrollments.filter(status='completed')
    certificates = Certificate.objects.filter(user=request.user, is_valid=True)
    wishlist_count = Wishlist.objects.filter(user=request.user).count()

    # Recently accessed
    recent = active.order_by('-last_accessed')[:4]

    # Progress summary
    in_progress = [e for e in active if 0 < e.progress < 100]

    return render(request, 'dashboard/student.html', {
        'enrollments': enrollments, 'active_enrollments': active,
        'completed_enrollments': completed, 'certificates': certificates,
        'wishlist_count': wishlist_count, 'recent_courses': recent,
        'in_progress': in_progress,
    })

@login_required
def instructor_dashboard(request):
    from enrollments.models import Enrollment
    from courses.models import Course, Review

    courses = Course.objects.filter(instructor=request.user).annotate(
        enrollment_count=Count('enrollments')
    ).order_by('-created_at')

    total_students = Enrollment.objects.filter(course__instructor=request.user, status='active').count()
    total_courses = courses.count()
    published_courses = courses.filter(status='published').count()
    pending_courses = courses.filter(status='pending').count()
    avg_rating = Review.objects.filter(course__instructor=request.user).aggregate(avg=Avg('rating'))['avg'] or 0

    recent_enrollments = Enrollment.objects.filter(
        course__instructor=request.user
    ).select_related('user','course').order_by('-enrolled_at')[:10]

    recent_reviews = Review.objects.filter(
        course__instructor=request.user
    ).select_related('user','course').order_by('-created_at')[:5]

    return render(request, 'dashboard/instructor.html', {
        'courses': courses, 'total_students': total_students,
        'total_courses': total_courses, 'published_courses': published_courses,
        'pending_courses': pending_courses, 'avg_rating': round(avg_rating, 1),
        'recent_enrollments': recent_enrollments, 'recent_reviews': recent_reviews,
    })

@login_required
def admin_dashboard(request):
    if not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('home')
    from accounts.models import CustomUser
    from courses.models import Course
    from enrollments.models import Enrollment
    from payments.models import Order

    total_users = CustomUser.objects.count()
    total_students = CustomUser.objects.filter(role='student').count()
    total_instructors = CustomUser.objects.filter(role='instructor').count()
    total_courses = Course.objects.count()
    published = Course.objects.filter(status='published').count()
    pending = Course.objects.filter(status='pending').count()
    total_enrollments = Enrollment.objects.count()
    total_revenue = Order.objects.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0

    pending_courses = Course.objects.filter(status='pending').select_related('instructor')[:10]
    recent_users = CustomUser.objects.order_by('-date_joined')[:10]
    recent_courses = Course.objects.order_by('-created_at')[:10]

    return render(request, 'dashboard/admin.html', {
        'total_users': total_users, 'total_students': total_students,
        'total_instructors': total_instructors, 'total_courses': total_courses,
        'published': published, 'pending': pending,
        'total_enrollments': total_enrollments, 'total_revenue': total_revenue,
        'pending_courses': pending_courses, 'recent_users': recent_users,
        'recent_courses': recent_courses,
    })

@login_required
def approve_course(request, course_id):
    if not request.user.is_admin_user():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    from courses.models import Course, Notification
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        action = request.POST.get('action','approve')
        if action == 'approve':
            course.status = 'published'
            course.published_at = timezone.now()
            course.save()
            Notification.objects.create(
                user=course.instructor, title='Course Approved! 🎉',
                message=f'Your course "{course.title}" has been approved and is now live!',
                notif_type='announcement', link=f'/courses/{course.slug}/'
            )
            messages.success(request, f'"{course.title}" approved and published.')
        else:
            course.status = 'rejected'
            course.save()
            Notification.objects.create(
                user=course.instructor, title='Course Review Update',
                message=f'Your course "{course.title}" needs revision before publishing.',
                notif_type='announcement'
            )
            messages.warning(request, f'"{course.title}" rejected.')
    return redirect('dashboard:admin')

@login_required
def manage_users(request):
    if not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('home')
    from accounts.models import CustomUser
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'dashboard/manage_users.html', {'users': users})

@login_required
def toggle_user_status(request, user_id):
    if not request.user.is_admin_user():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    from accounts.models import CustomUser
    user = get_object_or_404(CustomUser, id=user_id)
    if user == request.user:
        return JsonResponse({'error': 'Cannot deactivate yourself'}, status=400)
    user.is_active = not user.is_active
    user.save()
    return JsonResponse({'success': True, 'is_active': user.is_active})
