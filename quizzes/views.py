from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
import json
from .models import Quiz, Question, Choice, QuizAttempt, AttemptAnswer
from courses.models import Module
from enrollments.models import Enrollment

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=quiz.module.course)
    attempts = QuizAttempt.objects.filter(user=request.user, quiz=quiz)
    can_attempt = attempts.count() < quiz.max_attempts
    best_attempt = attempts.order_by('-score').first()
    return render(request, 'quizzes/detail.html', {
        'quiz': quiz, 'attempts': attempts, 'can_attempt': can_attempt, 'best_attempt': best_attempt
    })

@login_required
def quiz_take(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=quiz.module.course)
    attempts_count = QuizAttempt.objects.filter(user=request.user, quiz=quiz).count()
    if attempts_count >= quiz.max_attempts:
        messages.error(request, f'Maximum attempts ({quiz.max_attempts}) reached.')
        return redirect('quizzes:detail', quiz_id=quiz_id)
    questions = quiz.questions.prefetch_related('choices').all()
    return render(request, 'quizzes/take.html', {'quiz': quiz, 'questions': questions})

@login_required
def quiz_submit(request, quiz_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    quiz = get_object_or_404(Quiz, id=quiz_id)
    data = json.loads(request.body)
    answers = data.get('answers', {})
    time_taken = data.get('time_taken', 0)

    attempt = QuizAttempt.objects.create(
        user=request.user, quiz=quiz,
        total_questions=quiz.questions.count(),
        completed_at=timezone.now(), time_taken=time_taken
    )

    correct = 0
    for q in quiz.questions.all():
        choice_id = answers.get(str(q.id))
        selected = None
        is_correct = False
        if choice_id:
            try:
                selected = Choice.objects.get(id=choice_id, question=q)
                is_correct = selected.is_correct
                if is_correct: correct += 1
            except Choice.DoesNotExist:
                pass
        AttemptAnswer.objects.create(attempt=attempt, question=q, selected_choice=selected, is_correct=is_correct)

    total = quiz.questions.count()
    score = round((correct / total) * 100, 1) if total else 0
    attempt.correct_answers = correct
    attempt.score = score
    attempt.is_passed = score >= quiz.pass_score
    attempt.save()

    return JsonResponse({'success': True, 'score': score, 'correct': correct, 'total': total,
                         'passed': attempt.is_passed, 'attempt_id': attempt.id})

@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    answers = attempt.answers.select_related('question','selected_choice').prefetch_related('question__choices').all()
    return render(request, 'quizzes/result.html', {'attempt': attempt, 'answers': answers})

@login_required
def quiz_create(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if module.course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, 'Permission denied.')
        return redirect('home')
    if hasattr(module, 'quiz'):
        messages.info(request, 'Quiz already exists for this module.')
        return redirect('quizzes:manage', quiz_id=module.quiz.id)
    if request.method == 'POST':
        quiz = Quiz.objects.create(
            module=module, title=request.POST.get('title','Module Quiz'),
            description=request.POST.get('description',''),
            time_limit=int(request.POST.get('time_limit',0)),
            pass_score=int(request.POST.get('pass_score',70)),
            max_attempts=int(request.POST.get('max_attempts',3)),
        )
        messages.success(request, 'Quiz created! Now add questions.')
        return redirect('quizzes:manage', quiz_id=quiz.id)
    return render(request, 'quizzes/create.html', {'module': module})

@login_required
def quiz_manage(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.module.course.instructor != request.user and not request.user.is_admin_user():
        messages.error(request, 'Permission denied.')
        return redirect('home')
    questions = quiz.questions.prefetch_related('choices').all()
    return render(request, 'quizzes/manage.html', {'quiz': quiz, 'questions': questions})

@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.module.course.instructor != request.user and not request.user.is_admin_user():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    if request.method == 'POST':
        data = json.loads(request.body)
        question = Question.objects.create(quiz=quiz, text=data['text'], explanation=data.get('explanation',''), order=quiz.questions.count())
        for i, choice in enumerate(data.get('choices', [])):
            Choice.objects.create(question=question, text=choice['text'], is_correct=choice.get('is_correct', False))
        return JsonResponse({'success': True, 'question_id': question.id})
    return JsonResponse({'error': 'Method not allowed'}, status=405)
