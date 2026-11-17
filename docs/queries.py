"""Пять запросов из раздела 9 отчёта №5.

Запуск: python manage.py shell < docs/queries.py
Для просмотра SQL используйте print(qs.query). Для prefetch SQL снимайте
оба запроса через CaptureQueriesContext.
"""
from django.db import connection
from django.db.models import Avg, Count
from django.test.utils import CaptureQueriesContext

from core.models import Book, Copy, Exchange


# 9.1. Фильтрация: доступные экземпляры жанра «Роман» в Казани.
qs_1 = Copy.objects.filter(
    city='Казань',
    is_available=True,
    book__bookgenre__genre='Роман',
).distinct()
print('\n9.1 SQL:')
print(qs_1.query)
print('Результат:', list(qs_1.values_list('id', flat=True)))

# 9.2. Сортировка: десять последних новых заявок.
qs_2 = Exchange.objects.filter(status='new').order_by('-created_at')[:10]
print('\n9.2 SQL:')
print(qs_2.query)
print('Результат:', list(qs_2.values_list('id', flat=True)))

# 9.3. Агрегация: количество заявок и средняя оценка по статусу.
stats = (
    Exchange.objects
    .values('status')
    .annotate(total=Count('id'), avg_rating=Avg('review__rating'))
    .order_by('status')
)
with CaptureQueriesContext(connection) as stats_queries:
    stats_result = list(stats)
print('\n9.3 SQL:')
print(stats_queries.captured_queries[-1]['sql'])
print('Результат:', stats_result)

# 9.4. select_related: книга, получатель и владелец загружаются одним запросом.
qs_4 = Exchange.objects.select_related(
    'copy__book',
    'requester__reader',
    'copy__owner__reader',
).filter(status='new')[:5]
print('\n9.4 SQL:')
print(qs_4.query)
print('Результат:', [
    (item.pk, item.copy.book.title, item.requester.reader.email, item.copy.owner.reader.email)
    for item in qs_4
])

# 9.5. prefetch_related: отдельная загрузка связующих строк BookGenre.
qs_5 = Book.objects.prefetch_related('bookgenre_set').filter(
    bookgenre__genre='Антиутопия'
).distinct()
with CaptureQueriesContext(connection) as captured:
    books = list(qs_5)
print('\n9.5 SQL (основной + prefetch):')
print(*[query['sql'] for query in captured.captured_queries], sep='\n\n')
print('Результат:', [book.title for book in books])
