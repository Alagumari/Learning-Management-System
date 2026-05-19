def notifications(request):
    context = {'notifications': [], 'unread_count': 0}
    if request.user.is_authenticated:
        try:
            from courses.models import Notification
            notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
            context['notifications'] = notifs
            context['unread_count'] = notifs.filter(is_read=False).count()
        except Exception:
            pass
    return context
