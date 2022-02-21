from django.utils import timezone


# USE_TZ = True
def year(request):
    """Добавляет переменную с текущим годом."""
    now = timezone.now()
    return {'year': now.year}
