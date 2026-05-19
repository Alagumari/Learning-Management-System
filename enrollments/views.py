from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
import json

from courses.models import Course, Lesson, Notification
from .models import Enrollment, LessonProgress


# ---------------------------
# HELPER FUNCTION
# ---------------------------
def get_first_lesson(course):
    return Lesson.objects.filter(
        module__course=course
    ).order_by('module__order', 'order').first()


def get_first_lesson_id(course):
    lesson = get_first_lesson(course)
    return lesson.id if lesson else None


# ---------------------------
# ENROLL VIEW
# ---------------------------
@login_required
def enroll(request, slug):
    course = get_object_or_404(Course, slug=slug, status='published')

    # already enrolled
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, 'Already enrolled!')

        first_lesson_id = get_first_lesson_id(course)
        if first_lesson_id:
            return redirect('enrollments:learn', slug=slug, lesson_id=first_lesson_id)

        return redirect('dashboard:index')

    # payment check
    if course.price_type == 'paid' and not request.GET.get('free_override'):
        return redirect('payments:checkout', slug=slug)

    # create enrollment
    enrollment = Enrollment.objects.create(user=request.user, course=course)
    course.update_stats()

    Notification.objects.create(
        user=course.instructor,
        title='New Enrollment',
        message=f'{request.user.get_full_name() or request.user.username} enrolled in "{course.title}"',
        notif_type='enrollment',
        link='/dashboard/'
    )

    messages.success(request, f'Successfully enrolled in "{course.title}"!')

    first_lesson = get_first_lesson(course)

    if first_lesson:
        return redirect('enrollments:learn', slug=slug, lesson_id=first_lesson.id)

    messages.warning(request, "No lessons found in this course yet.")
    return redirect('dashboard:index')


# ---------------------------
# LEARN VIEW (SAFE VERSION)
# ---------------------------
@login_required
def learn(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)

    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=course
    )

    # SAFE LESSON FETCH (IMPORTANT FIX)
    lesson = Lesson.objects.filter(
        id=lesson_id,
        module__course=course
    ).first()

    if not lesson:
        messages.error(request, "Lesson not found or not linked to this course.")
        first_lesson = get_first_lesson(course)

        if first_lesson:
            return redirect('enrollments:learn', slug=slug, lesson_id=first_lesson.id)

        return redirect('dashboard:index')

    modules = course.modules.prefetch_related('lessons').all()

    # update last accessed
    enrollment.last_lesson = lesson
    enrollment.last_accessed = timezone.now()
    enrollment.save(update_fields=['last_lesson', 'last_accessed'])

    progress_obj, _ = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )

    all_lessons = Lesson.objects.filter(
        module__course=course
    ).order_by('module__order', 'order')

    lesson_list = list(all_lessons)

    current_idx = next((i for i, l in enumerate(lesson_list) if l.id == lesson.id), 0)

    prev_lesson = lesson_list[current_idx - 1] if current_idx > 0 else None
    next_lesson = lesson_list[current_idx + 1] if current_idx < len(lesson_list) - 1 else None

    completed_ids = set(
        LessonProgress.objects.filter(
            enrollment=enrollment,
            is_completed=True
        ).values_list('lesson_id', flat=True)
    )

    return render(request, 'enrollments/learn.html', {
        'course': course,
        'lesson': lesson,
        'enrollment': enrollment,
        'modules': modules,
        'progress_obj': progress_obj,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'completed_ids': completed_ids,
    })


# ---------------------------
# MARK COMPLETE
# ---------------------------
@login_required
def mark_complete(request, lesson_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    lesson = get_object_or_404(Lesson, id=lesson_id)

    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=lesson.module.course
    )

    progress, _ = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )

    progress.is_completed = True
    progress.completed_at = timezone.now()
    progress.save()

    enrollment.update_progress()

    return JsonResponse({
        'success': True,
        'progress': enrollment.progress,
        'status': enrollment.status
    })


# ---------------------------
# SAVE PROGRESS
# ---------------------------
@login_required
def save_progress(request, lesson_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    lesson = get_object_or_404(Lesson, id=lesson_id)

    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=lesson.module.course
    )

    progress, _ = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )

    data = json.loads(request.body)

    progress.watch_time = data.get('watch_time', progress.watch_time)
    progress.save()

    return JsonResponse({'success': True})