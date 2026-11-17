from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    Book, BookGenre, Complaint, Copy, Exchange, ExchangeStatusLog, Genre,
    Reader, ReaderProfile, Review,
)


BOOKS = [
    ('Мастер и Маргарита', 'Михаил Булгаков', 'Роман'),
    ('1984', 'Джордж Оруэлл', 'Антиутопия'),
    ('Скотный двор', 'Джордж Оруэлл', 'Антиутопия'),
    ('451 градус по Фаренгейту', 'Рэй Брэдбери', 'Антиутопия'),
    ('О дивный новый мир', 'Олдос Хаксли', 'Антиутопия'),
    ('Маленький принц', 'Антуан де Сент-Экзюпери', 'Сказка'),
    ('Отцы и дети', 'Иван Тургенев', 'Роман'),
    ('Анна Каренина', 'Лев Толстой', 'Роман'),
    ('Собака Баскервилей', 'Артур Конан Дойл', 'Детектив'),
    ('Властелин колец', 'Джон Р. Р. Толкин', 'Фэнтези'),
    ('Преступление и наказание', 'Фёдор Достоевский', 'Роман'),
    ('Дюна', 'Фрэнк Герберт', 'Фантастика'),
    ('Пикник на обочине', 'Аркадий и Борис Стругацкие', 'Фантастика'),
    ('Норвежский лес', 'Харуки Мураками', 'Роман'),
    ('Евгений Онегин', 'Александр Пушкин', 'Поэзия'),
    ('Граф Монте-Кристо', 'Александр Дюма', 'Приключения'),
    ('Шерлок Холмс: Этюд в багровых тонах', 'Артур Конан Дойл', 'Детектив'),
    ('Три товарища', 'Эрих Мария Ремарк', 'Роман'),
    ('Идиот', 'Фёдор Достоевский', 'Роман'),
    ('Гарри Поттер и философский камень', 'Дж. К. Роулинг', 'Фэнтези'),
    ('Солярис', 'Станислав Лем', 'Фантастика'),
    ('Человек-невидимка', 'Герберт Уэллс', 'Фантастика'),
    ('Вино из одуванчиков', 'Рэй Брэдбери', 'Роман'),
    ('Тихий Дон', 'Михаил Шолохов', 'Роман'),
    ('Алхимик', 'Пауло Коэльо', 'Роман'),
    ('Имя розы', 'Умберто Эко', 'Детектив'),
    ('Цветы для Элджернона', 'Дэниел Киз', 'Фантастика'),
    ('Чайка по имени Джонатан Ливингстон', 'Ричард Бах', 'Притча'),
    ('Повелитель мух', 'Уильям Голдинг', 'Роман'),
    ('Доктор Живаго', 'Борис Пастернак', 'Роман'),
    ('Три мушкетёра', 'Александр Дюма', 'Приключения'),
    ('Капитанская дочка', 'Александр Пушкин', 'Роман'),
    ('Понедельник начинается в субботу', 'Аркадий и Борис Стругацкие', 'Фантастика'),
    ('Остров сокровищ', 'Роберт Льюис Стивенсон', 'Приключения'),
    ('Моби Дик', 'Герман Мелвилл', 'Приключения'),
    ('Гордость и предубеждение', 'Джейн Остин', 'Роман'),
    ('Маленькие женщины', 'Луиза Мэй Олкотт', 'Роман'),
    ('Человек в высоком замке', 'Филип Дик', 'Фантастика'),
    ('Зов предков', 'Джек Лондон', 'Приключения'),
    ('Старик и море', 'Эрнест Хемингуэй', 'Повесть'),
]

CITIES = ['Москва', 'Санкт-Петербург', 'Казань', 'Екатеринбург', 'Новосибирск']


class Command(BaseCommand):
    help = 'Создаёт демонстрационные данные для 11 моделей приложения core.'

    @transaction.atomic
    def handle(self, *args, **options):
        if Book.objects.exists() or Reader.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Данные core уже существуют. Для повторного заполнения удалите db.sqlite3, '
                'выполните migrate и запустите seed_demo заново.'
            ))
            self.print_counts()
            return

        readers = []
        profiles = []
        for number in range(1, 21):
            reader = Reader.objects.create_user(
                email=f'reader{number:02d}@example.com',
                password='BookloopDemo2026!',
                role=Reader.Role.ADMIN if number == 1 else Reader.Role.READER,
            )
            profile = ReaderProfile.objects.create(
                reader=reader,
                city=CITIES[(number - 1) % len(CITIES)],
                balance=5 + number % 8,
                display_name=f'Читатель {number:02d}',
                about='Демонстрационный профиль участника BOOKLOOP.',
            )
            readers.append(reader)
            profiles.append(profile)

        books = []
        for title, author, genre in BOOKS:
            book = Book.objects.create(
                title=title,
                author=author,
                description=f'Демонстрационное описание произведения «{title}».',
            )
            books.append(book)
            genre_obj, _ = Genre.objects.get_or_create(name=genre)
            BookGenre.objects.create(book=book, genre=genre_obj)

        # Ещё по одному жанру для первых 24 произведений: всего 64 строки BookGenre.
        secondary_genres = [
            'Классика', 'Приключения', 'Роман', 'История', 'Фантастика', 'Психология',
            'Детектив', 'Фэнтези', 'Нон-фикшн', 'Поэзия', 'Роман', 'Классика',
        ]
        for index in range(24):
            genre = secondary_genres[index % len(secondary_genres)]
            if genre == books[index].bookgenre_set.first().genre_id:
                genre = 'Классика' if genre != 'Классика' else 'Приключения'
            genre_obj, _ = Genre.objects.get_or_create(name=genre)
            BookGenre.objects.create(book=books[index], genre=genre_obj)

        copies = []
        for index in range(60):
            if index < 40:
                book = books[index]
            elif index == 41:
                # Copy №42 — Маленький принц для контрольной заявки №33.
                book = books[5]
            elif index == 42:
                # Copy №43 — единственный экземпляр для запроса 9.1.
                book = books[0]
            else:
                book = books[(index - 40) % 20]

            owner_index = index % 20
            if index == 42:
                owner_index = 19  # reader20@example.com
            city = CITIES[index % len(CITIES)]
            if index == 42:
                city = 'Казань'
            elif book.bookgenre_set.filter(genre='Роман').exists() and city == 'Казань':
                city = 'Москва'
            copy = Copy.objects.create(
                book=book,
                owner=profiles[owner_index],
                condition=[Copy.Condition.NEW, Copy.Condition.GOOD, Copy.Condition.FAIR, Copy.Condition.POOR][index % 4],
                city=city,
                is_available=(index % 7 != 0),
                moderation_status=Copy.ModerationStatus.APPROVED,
            )
            copies.append(copy)
        # Copy №43 должен быть доступен и находиться в Казани.
        Copy.objects.filter(pk=43).update(city='Казань', is_available=True)

        new_ids = [33, 6, 7, 27, 22]
        statuses = {}
        statuses.update({pk: Exchange.Status.NEW for pk in new_ids})
        statuses.update({pk: Exchange.Status.ACCEPTED for pk in range(1, 6)})
        statuses.update({pk: Exchange.Status.SENT for pk in range(8, 12)})
        statuses.update({pk: Exchange.Status.DONE for pk in list(range(12, 22)) + list(range(23, 27)) + [35]})
        statuses.update({pk: Exchange.Status.CANCELLED for pk in range(28, 31)})
        statuses.update({pk: Exchange.Status.DISPUTE for pk in [31, 32, 34]})

        # Для пяти новых заявок фиксируем участников и книги из контрольного примера отчёта.
        expected_new = {
            33: (41, 15, 20),  # Маленький принц, reader15 -> reader20
            6: (6, 12, 18),   # Отцы и дети, reader12 -> reader18
            7: (7, 19, 20),   # Анна Каренина, reader19 -> reader20
            27: (8, 5, 14),   # Собака Баскервилей, reader05 -> reader14
            22: (9, 5, 8),    # Властелин колец, reader05 -> reader08
        }
        for pk in range(1, 36):
            if pk in expected_new:
                copy_index, requester_number, owner_number = expected_new[pk]
                copy = copies[copy_index]
                copy.owner = profiles[owner_number - 1]
                copy.save(update_fields=['owner'])
                requester = profiles[requester_number - 1]
            else:
                copy = copies[(pk - 1) % len(copies)]
                requester = profiles[(pk + 4) % len(profiles)]
                if requester.pk == copy.owner_id:
                    requester = profiles[(pk + 5) % len(profiles)]

            status = statuses[pk]
            method = '' if status == Exchange.Status.NEW else Exchange.Method.MEET
            meet_place = '' if not method else 'Казань, центральная библиотека'
            meet_at = None if not method else timezone.now() + timedelta(days=3)
            track_no = ''
            if status in {Exchange.Status.SENT, Exchange.Status.DONE}:
                method = Exchange.Method.POST
                meet_place = ''
                meet_at = None
                track_no = f'RU{pk:010d}'

            exchange = Exchange.objects.create(
                copy=copy,
                requester=requester,
                status=status,
                method=method,
                meet_place=meet_place,
                meet_at=meet_at,
                track_no=track_no,
            )
            # Время задаётся отдельно, чтобы порядок новых заявок совпал с контрольным примером.
            if pk in new_ids:
                priority = new_ids.index(pk)
                created = timezone.now() - timedelta(days=priority + 1)
            else:
                created = timezone.now() - timedelta(days=20 + pk)
            Exchange.objects.filter(pk=exchange.pk).update(created_at=created)

            ExchangeStatusLog.objects.create(
                exchange=exchange,
                old_status=Exchange.Status.NEW,
                new_status=status,
                changed_by=readers[(pk - 1) % len(readers)],
            )
            if pk <= 35:
                ExchangeStatusLog.objects.create(
                    exchange=exchange,
                    old_status=status,
                    new_status=status,
                    changed_by=readers[pk % len(readers)],
                )

        done_exchanges = list(Exchange.objects.filter(status=Exchange.Status.DONE).order_by('id'))
        ratings = [5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 2, 3]
        for exchange, rating in zip(done_exchanges, ratings):
            Review.objects.create(
                exchange=exchange,
                author=exchange.requester,
                target=exchange.copy.owner,
                rating=rating,
                text='Демонстрационный отзыв после завершённого обмена.',
            )

        for exchange_id in [31, 32, 34, 35]:
            exchange = Exchange.objects.get(pk=exchange_id)
            Complaint.objects.create(
                exchange=exchange,
                author=exchange.requester,
                reason=Complaint.Reason.MISMATCH,
                description='Состояние экземпляра отличается от описания в карточке.',
                decision='',
                moderator=None,
            )

        self.print_counts()

    def print_counts(self):
        self.stdout.write(self.style.SUCCESS(
            'Готово: '
            f'читателей={Reader.objects.count()}, '
            f'профилей={ReaderProfile.objects.count()}, '
            f'произведений={Book.objects.count()}, '
            f'справочник_жанров={Genre.objects.count()}, '
            f'связей_книга_жанр={BookGenre.objects.count()}, '
            f'экземпляров={Copy.objects.count()}, '
            f'обменов={Exchange.objects.count()}, '
            f'историй={ExchangeStatusLog.objects.count()}, '
            f'жалоб={Complaint.objects.count()}, '
            f'отзывов={Review.objects.count()}'
        ))
