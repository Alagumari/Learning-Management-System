from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Course, Category, Module, Lesson, Review, Wishlist, Notification
from .forms import CourseForm, ModuleForm, LessonForm, ReviewForm

def home(request):
    featured = Course.objects.filter(status='published', is_featured=True)[:6]
    latest = Course.objects.filter(status='published').order_by('-published_at')[:8]
    categories = Category.objects.all()[:8]
    popular = Course.objects.filter(status='published').order_by('-total_enrolled')[:6]
    stats = {
        'courses': Course.objects.filter(status='published').count(),
        'students': __import__('accounts').models.CustomUser.objects.filter(role='student').count(),
        'instructors': __import__('accounts').models.CustomUser.objects.filter(role='instructor').count(),
    }
    return render(request, 'home.html', {
        'featured_courses': featured, 'latest_courses': latest,
        'categories': categories, 'popular_courses': popular, 'stats': stats
    })

def course_list(request):
    courses = Course.objects.filter(status='published')
    q = request.GET.get('q','')
    category = request.GET.get('category','')
    level = request.GET.get('level','')
    price_type = request.GET.get('price','')
    sort = request.GET.get('sort','-created_at')

    if q: courses = courses.filter(Q(title__icontains=q)|Q(description__icontains=q)|Q(tags__icontains=q))
    if category: courses = courses.filter(category__slug=category)
    if level: courses = courses.filter(level=level)
    if price_type: courses = courses.filter(price_type=price_type)

    sort_map = {'newest':'-created_at','oldest':'created_at','popular':'-total_enrolled','rating':'-avg_rating','price_low':'price','price_high':'-price'}
    courses = courses.order_by(sort_map.get(sort, '-created_at'))

    paginator = Paginator(courses, 12)
    page = paginator.get_page(request.GET.get('page',1))
    categories = Category.objects.all()
    return render(request, 'courses/list.html', {'courses': page, 'categories': categories, 'q': q, 'selected_category': category, 'selected_level': level, 'selected_price': price_type, 'sort': sort})

def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    modules = course.modules.prefetch_related('lessons').all()
    reviews = course.reviews.select_related('user').all()[:10]
    is_enrolled = False
    is_wishlisted = False
    enrollment = None
    review_form = ReviewForm()
    user_review = None

    if request.user.is_authenticated:
        from enrollments.models import Enrollment
        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
        is_enrolled = enrollment is not None
        is_wishlisted = Wishlist.objects.filter(user=request.user, course=course).exists()
        user_review = Review.objects.filter(user=request.user, course=course).first()

    related = Course.objects.filter(category=course.category, status='published').exclude(pk=course.pk)[:4]
    return render(request, 'courses/detail.html', {
        'course': course, 'modules': modules, 'reviews': reviews,
        'is_enrolled': is_enrolled, 'is_wishlisted': is_wishlisted,
        'enrollment': enrollment, 'review_form': review_form, 'user_review': user_review,
        'related_courses': related
    })

@login_required
def course_create(request):
    if not (request.user.is_instructor() or request.user.is_admin_user()):
        messages.error(request, 'Only instructors can create courses.')
        return redirect('home')
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, 'Course created! Now add modules and lessons.')
            return redirect('courses:modules', slug=course.slug)
    else:
        form = CourseForm()
    return render(request, 'courses/create.html', {'form': form})

@login_required
def course_edit(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, 'Permission denied.')
        return redirect('courses:detail', slug=slug)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('courses:detail', slug=slug)
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/edit.html', {'form': form, 'course': course})

@login_required
def course_delete(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, 'Permission denied.')
        return redirect('home')
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted.')
        return redirect('dashboard:index')
    return render(request, 'courses/confirm_delete.html', {'course': course})

@login_required
def course_publish(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    if request.method == 'POST':
        course.status = 'pending'
        course.save()
        messages.info(request, 'Course submitted for review.')
    return redirect('courses:detail', slug=slug)

@login_required
def module_list(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, 'Permission denied.')
        return redirect('home')
    modules = course.modules.prefetch_related('lessons').all()
    return render(request, 'courses/modules.html', {'course': course, 'modules': modules, 'module_form': ModuleForm(), 'lesson_form': LessonForm()})

@login_required
def module_add(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user and not request.user.is_admin_user():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'module_id': module.id, 'title': module.title})
            messages.success(request, 'Module added!')
    return redirect('courses:modules', slug=slug)

@login_required
def module_edit(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if module.course.instructor != request.user and not request.user.is_admin_user():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, 'Module updated!')
    return redirect('courses:modules', slug=module.course.slug)

@login_required
def module_delete(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    slug = module.course.slug
    if module.course.instructor != request.user and not request.user.is_admin_user():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    if request.method == 'POST':
        module.delete()
        messages.success(request, 'Module deleted.')
    return redirect('courses:modules', slug=slug)

@login_required
def lesson_add(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if module.course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, 'Permission denied.')
        return redirect('home')
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.save()
            module.course.update_stats()
            messages.success(request, 'Lesson added!')
    return redirect('courses:modules', slug=module.course.slug)

@login_required
def lesson_edit(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if lesson.module.course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, 'Permission denied.')
        return redirect('home')
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            lesson.module.course.update_stats()
            messages.success(request, 'Lesson updated!')
    return redirect('courses:modules', slug=lesson.module.course.slug)

@login_required
def lesson_delete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    slug = lesson.module.course.slug
    if lesson.module.course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, 'Permission denied.')
        return redirect('home')
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Lesson deleted.')
    return redirect('courses:modules', slug=slug)

@login_required
def add_review(request, slug):
    course = get_object_or_404(Course, slug=slug)
    from enrollments.models import Enrollment
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, 'Enroll in this course to leave a review.')
        return redirect('courses:detail', slug=slug)
    if request.method == 'POST':
        existing = Review.objects.filter(user=request.user, course=course).first()
        form = ReviewForm(request.POST, instance=existing)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.course = course
            review.save()
            course.update_stats()
            messages.success(request, 'Review submitted!')
    return redirect('courses:detail', slug=slug)

@login_required
def toggle_wishlist(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, course=course)
    if not created:
        obj.delete()
        added = False
    else:
        added = True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'added': added})
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('course')
    return render(request, 'courses/wishlist.html', {'wishlist': items})

@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)
