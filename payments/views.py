import json
import hmac
import hashlib
import razorpay

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from courses.models import Course, Notification
from enrollments.models import Enrollment
from .models import Order


def _razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


@login_required
def checkout(request, slug):
    course = get_object_or_404(Course, slug=slug, status='published')

    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, 'You are already enrolled!')
        return redirect('dashboard:index')

    if course.price_type == 'free':
        return redirect('enrollments:enroll', slug=slug)

    # Amount in paise (Razorpay needs integer paise)
    amount_inr   = float(course.get_effective_price())
    amount_paise = int(amount_inr * 100)

    # Create / reuse a pending Order row
    order = Order.objects.filter(
        user=request.user, course=course, status='pending'
    ).first()

    if not order:
        order = Order.objects.create(
            user=request.user,
            course=course,
            amount=amount_inr,
        )

    # Create Razorpay order
    try:
        client = _razorpay_client()
        rz_order = client.order.create({
            'amount':   amount_paise,
            'currency': settings.RAZORPAY_CURRENCY,
            'receipt':  str(order.order_id),
            'notes': {
                'course':   course.title,
                'username': request.user.username,
            },
        })
        order.razorpay_order_id = rz_order['id']
        order.save(update_fields=['razorpay_order_id'])
    except Exception as e:
        # If Razorpay keys are test / invalid, store a dummy id and let
        # the template still render (user sees the Razorpay checkout modal)
        order.razorpay_order_id = f'order_DEMO_{order.order_id.hex[:12]}'
        order.save(update_fields=['razorpay_order_id'])

    context = {
        'course':             course,
        'order':              order,
        'razorpay_key_id':    settings.RAZORPAY_KEY_ID,
        'razorpay_order_id':  order.razorpay_order_id,
        'amount_paise':       amount_paise,
        'amount_inr':         amount_inr,
        'user_name':          request.user.get_full_name() or request.user.username,
        'user_email':         request.user.email,
        'user_phone':         request.user.phone if hasattr(request.user, 'phone') else '',
    }
    return render(request, 'payments/checkout.html', context)


@csrf_exempt
@login_required
def payment_verify(request):
    """
    Called via AJAX after Razorpay modal success.
    Verifies HMAC signature, marks order paid, auto-enrolls student.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    rz_order_id   = data.get('razorpay_order_id', '')
    rz_payment_id = data.get('razorpay_payment_id', '')
    rz_signature  = data.get('razorpay_signature', '')

    # Find the order
    order = Order.objects.filter(
        user=request.user,
        razorpay_order_id=rz_order_id,
        status='pending',
    ).first()

    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)

    # ── Verify HMAC-SHA256 signature ──
    generated = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f"{rz_order_id}|{rz_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if generated != rz_signature:
        order.status = 'failed'
        order.save(update_fields=['status'])
        return JsonResponse({'error': 'Signature verification failed', 'success': False}, status=400)

    # ── Mark order paid ──
    order.status              = 'paid'
    order.razorpay_payment_id = rz_payment_id
    order.razorpay_signature  = rz_signature
    order.paid_at             = timezone.now()
    order.save()

    # ── Enroll student ──
    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user, course=order.course
    )
    if created:
        order.course.update_stats()
        Notification.objects.create(
            user=order.course.instructor,
            title='New Paid Enrollment 💰',
            message=f'{request.user.get_full_name() or request.user.username} purchased "{order.course.title}".',
            notif_type='enrollment',
        )

    return JsonResponse({
        'success':  True,
        'redirect': '/dashboard/',
        'message':  f'Payment successful! You are now enrolled in "{order.course.title}".',
    })


@csrf_exempt
def payment_webhook(request):
    """
    Razorpay webhook endpoint.
    Register this URL in your Razorpay Dashboard → Webhooks.
    Events handled: payment.captured
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # Verify webhook signature
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
    if webhook_secret:
        received_sig = request.headers.get('X-Razorpay-Signature', '')
        generated = hmac.new(
            webhook_secret.encode(),
            request.body,
            hashlib.sha256,
        ).hexdigest()
        if generated != received_sig:
            return JsonResponse({'error': 'Invalid signature'}, status=400)

    try:
        payload = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    event = payload.get('event')
    if event == 'payment.captured':
        entity     = payload['payload']['payment']['entity']
        rz_order_id = entity.get('order_id', '')
        rz_pay_id   = entity.get('id', '')

        order = Order.objects.filter(razorpay_order_id=rz_order_id).first()
        if order and order.status == 'pending':
            order.status               = 'paid'
            order.razorpay_payment_id  = rz_pay_id
            order.paid_at              = timezone.now()
            order.save()
            Enrollment.objects.get_or_create(user=order.user, course=order.course)
            order.course.update_stats()

    return JsonResponse({'status': 'ok'})


@login_required
def payment_success(request):
    messages.success(request, '🎉 Payment successful! You are now enrolled.')
    return redirect('dashboard:index')


@login_required
def payment_failed(request):
    messages.error(request, '❌ Payment failed or cancelled. Please try again.')
    return redirect('courses:list')


@login_required
def payment_history(request):
    orders = Order.objects.filter(user=request.user).select_related('course')
    return render(request, 'payments/history.html', {'orders': orders})
