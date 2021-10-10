from datetime import date

day = date.today()


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': day.year
    }
