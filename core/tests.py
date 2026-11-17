from django.core.management import call_command
from django.db.models import Avg, Count
from django.test import TestCase

from .models import Book, BookGenre, Complaint, Copy, Exchange, ExchangeStatusLog, Genre, Reader, ReaderProfile, Review


class CoreDemoDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_core_demo', verbosity=0)

    def test_seed_counts_match_report(self):
        self.assertEqual(Reader.objects.count(), 20)
        self.assertEqual(ReaderProfile.objects.count(), 20)
        self.assertEqual(Book.objects.count(), 40)
        self.assertEqual(BookGenre.objects.count(), 64)
        self.assertGreaterEqual(Genre.objects.count(), 10)
        self.assertEqual(Copy.objects.count(), 60)
        self.assertEqual(Exchange.objects.count(), 35)
        self.assertEqual(ExchangeStatusLog.objects.count(), 70)
        self.assertEqual(Complaint.objects.count(), 4)
        self.assertEqual(Review.objects.count(), 15)

    def test_kazan_roman_query_returns_copy_43(self):
        result = Copy.objects.filter(
            city='Казань',
            is_available=True,
            book__bookgenre__genre='Роман',
        ).distinct()
        self.assertEqual(list(result.values_list('id', flat=True)), [43])

    def test_exchange_status_distribution(self):
        counts = dict(
            Exchange.objects.values('status')
            .annotate(total=Count('id'))
            .values_list('status', 'total')
        )
        self.assertEqual(counts, {
            'new': 5,
            'accepted': 5,
            'sent': 4,
            'done': 15,
            'cancelled': 3,
            'dispute': 3,
        })

    def test_done_reviews_average_is_56_over_15(self):
        result = Exchange.objects.filter(status='done').aggregate(avg=Avg('review__rating'))
        self.assertAlmostEqual(result['avg'], 56 / 15, places=2)

    def test_antiutopia_books_are_four(self):
        books = Book.objects.filter(bookgenre__genre='Антиутопия').distinct()
        self.assertEqual(books.count(), 4)
