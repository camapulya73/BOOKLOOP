from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Book as CoreBook, BookGenre, Copy, Exchange, Genre, ReaderProfile
from .models import Favorite

User = get_user_model()


class BookLoopTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@example.com', password='StrongPass123!')
        self.reader = User.objects.create_user(email='reader@example.com', password='StrongPass123!')
        self.owner_profile = ReaderProfile.objects.create(
            reader=self.owner, display_name='Владелец', city='Казань'
        )
        self.reader_profile = ReaderProfile.objects.create(
            reader=self.reader, display_name='Читатель', city='Казань'
        )
        self.genre = Genre.objects.create(name='Роман')
        self.book = CoreBook.objects.create(title='Тестовая книга', author='Автор')
        BookGenre.objects.create(book=self.book, genre=self.genre)
        self.copy = Copy.objects.create(
            book=self.book,
            owner=self.owner_profile,
            city='Казань',
            condition=Copy.Condition.GOOD,
            is_available=True,
            moderation_status=Copy.ModerationStatus.APPROVED,
        )

    def test_catalog_contains_available_book(self):
        self.assertContains(self.client.get(reverse('catalog')), 'Тестовая книга')

    def test_guest_can_open_book(self):
        self.assertEqual(self.client.get(reverse('book_detail', args=[self.copy.pk])).status_code, 200)

    def test_user_can_propose_exchange(self):
        self.client.login(email='reader@example.com', password='StrongPass123!')
        response = self.client.post(reverse('propose_exchange', args=[self.copy.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Exchange.objects.count(), 1)

    def test_owner_cannot_exchange_with_self(self):
        self.client.login(email='owner@example.com', password='StrongPass123!')
        self.client.post(reverse('propose_exchange', args=[self.copy.pk]))
        self.assertEqual(Exchange.objects.count(), 0)

    def test_favorite_unique_constraint(self):
        Favorite.objects.create(user=self.reader, copy=self.copy)
        self.assertEqual(Favorite.objects.filter(user=self.reader, copy=self.copy).count(), 1)
