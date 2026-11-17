from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinLengthValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from pathlib import Path


PHONE_VALIDATOR = RegexValidator(
    regex=r'^\+7\d{10}$',
    message='Введите номер в формате +79991234567.',
)


def validate_copy_image(image):
    extension = Path(image.name).suffix.lower()
    if extension not in {'.jpg', '.jpeg', '.png', '.webp'}:
        raise ValidationError('Допустимые форматы: JPG, PNG, WEBP.')
    if image.size > 2 * 1024 * 1024:
        raise ValidationError('Размер изображения не должен превышать 2 МБ.')


class ReaderManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Для читателя необходимо указать email.')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', Reader.Role.ADMIN)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class Reader(AbstractBaseUser):
    class Role(models.TextChoices):
        READER = 'reader', 'Читатель'
        MODERATOR = 'moderator', 'Модератор'
        ADMIN = 'admin', 'Администратор'

    email = models.EmailField('Email', max_length=254, unique=True)
    role = models.CharField('Роль', max_length=10, choices=Role.choices, default=Role.READER)
    is_active = models.BooleanField('Активен', default=True)
    date_joined = models.DateTimeField('Дата регистрации', auto_now_add=True)

    objects = ReaderManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Читатель'
        verbose_name_plural = 'Читатели'
        ordering = ['email']

    @property
    def is_superuser(self):
        return self.role == self.Role.ADMIN

    @property
    def is_staff(self):
        return self.is_superuser or self.role == self.Role.MODERATOR

    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_staff

    def has_perms(self, perm_list, obj=None):
        return self.is_active and self.is_staff

    def has_module_perms(self, app_label):
        return self.is_active and self.is_staff

    @property
    def username(self):
        try:
            return self.readerprofile.display_name or self.email.split('@')[0]
        except ReaderProfile.DoesNotExist:
            return self.email.split('@')[0]

    def __str__(self):
        return self.email


class ReaderProfile(models.Model):
    reader = models.OneToOneField(
        Reader,
        on_delete=models.CASCADE,
        related_name='readerprofile',
        verbose_name='Участник',
    )
    city = models.CharField('Город', max_length=80)
    phone = models.CharField('Телефон', max_length=20, blank=True, validators=[PHONE_VALIDATOR])
    balance = models.PositiveIntegerField('Баланс баллов', default=0)
    display_name = models.CharField('Отображаемое имя', max_length=60)
    about = models.TextField('О себе', max_length=500, blank=True)

    class Meta:
        verbose_name = 'Профиль читателя'
        verbose_name_plural = 'Профили читателей'

    @property
    def username(self):
        return self.reader.username

    def __str__(self):
        return self.display_name


class Genre(models.Model):
    name = models.CharField('Название жанра', max_length=60, unique=True)
    description = models.CharField('Описание', max_length=240, blank=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField('Название', max_length=200)
    author = models.CharField('Автор', max_length=150)
    isbn = models.CharField(
        'ISBN', max_length=17, blank=True,
        validators=[RegexValidator(r'^97[89](?:-?\d){10,13}$', 'ISBN должен содержать 13 цифр и начинаться с 978 или 979.')],
    )
    year = models.PositiveSmallIntegerField(
        'Год издания', null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(2100)],
    )
    description = models.TextField('Описание', max_length=3000, blank=True)
    genres = models.ManyToManyField('Genre', through='BookGenre', related_name='books', blank=True)

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ['title', 'author']
        constraints = [
            models.UniqueConstraint(fields=['title', 'author'], name='core_unique_book_title_author'),
        ]
        indexes = [models.Index(fields=['author', 'title'], name='core_book_author_title_idx')]

    def __str__(self):
        return f'{self.title} — {self.author}'


class BookGenre(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='bookgenre_set', related_query_name='bookgenre')
    genre = models.ForeignKey(
        Genre, on_delete=models.PROTECT, to_field='name', db_column='genre',
        related_name='bookgenre_set', related_query_name='bookgenre', verbose_name='Жанр',
    )

    class Meta:
        verbose_name = 'Жанр произведения'
        verbose_name_plural = 'Жанры произведений'
        constraints = [models.UniqueConstraint(fields=['book', 'genre'], name='core_unique_book_genre')]
        ordering = ['genre']

    def __str__(self):
        return f'{self.book.title}: {self.genre.name}'


class Copy(models.Model):
    class ModerationStatus(models.TextChoices):
        PENDING = 'pending', 'На модерации'
        APPROVED = 'approved', 'Одобрена'
        REJECTED = 'rejected', 'Отклонена'

    class Condition(models.TextChoices):
        NEW = 'new', 'Новое'
        GOOD = 'good', 'Хорошее'
        FAIR = 'fair', 'Удовлетворительное'
        POOR = 'poor', 'Есть заметные повреждения'

    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='copies')
    owner = models.ForeignKey(ReaderProfile, on_delete=models.PROTECT, related_name='copies')
    condition = models.CharField('Состояние', max_length=15, choices=Condition.choices, default=Condition.GOOD)
    city = models.CharField('Город', max_length=80)
    is_available = models.BooleanField('Доступен для обмена', default=True)
    moderation_status = models.CharField('Статус модерации', max_length=10, choices=ModerationStatus.choices, default=ModerationStatus.PENDING)
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Экземпляр'
        verbose_name_plural = 'Экземпляры'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['city', 'is_available'], name='idx_copy_city_avail')]

    @property
    def title(self):
        return self.book.title

    @property
    def author(self):
        return self.book.author

    @property
    def description(self):
        return self.book.description

    @property
    def category(self):
        return self.book.genres.first()

    @property
    def cover(self):
        photo = self.photos.first()
        return photo.image if photo else None

    def __str__(self):
        return f'{self.book.title} ({self.condition})'


class CopyPhoto(models.Model):
    copy = models.ForeignKey(Copy, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField('Фотография экземпляра', upload_to='copies/%Y/%m/', validators=[validate_copy_image])
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)

    class Meta:
        verbose_name = 'Фото экземпляра'
        verbose_name_plural = 'Фотографии экземпляров'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'Фото: {self.copy}'


class Exchange(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        ACCEPTED = 'accepted', 'Принята'
        SENT = 'sent', 'Отправлена'
        DONE = 'done', 'Завершена'
        CANCELLED = 'cancelled', 'Отменена'
        DISPUTE = 'dispute', 'Спор'

    class Method(models.TextChoices):
        MEET = 'meet', 'Личная встреча'
        POST = 'post', 'Почта'

    copy = models.ForeignKey(Copy, on_delete=models.PROTECT, related_name='exchanges')
    requester = models.ForeignKey(ReaderProfile, on_delete=models.PROTECT, related_name='exchanges')
    status = models.CharField('Статус', max_length=12, choices=Status.choices, default=Status.NEW)
    method = models.CharField('Способ передачи', max_length=10, choices=Method.choices, blank=True)
    meet_place = models.CharField('Место встречи', max_length=255, blank=True)
    meet_at = models.DateTimeField('Дата встречи', null=True, blank=True)
    track_no = models.CharField('Трек-номер', max_length=40, blank=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Обмен'
        verbose_name_plural = 'Обмены'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', 'created_at'], name='idx_exchange_status_created')]
        constraints = [
            models.CheckConstraint(
                check=(Q(method='') | (Q(method='meet') & ~Q(meet_place='') & Q(meet_at__isnull=False)) | Q(method='post')),
                name='exchange_method_fields',
            ),
            models.CheckConstraint(
                check=~(Q(method='post') & Q(status__in=['sent', 'done']) & Q(track_no='')),
                name='exchange_post_needs_track',
            ),
        ]

    def clean(self):
        super().clean()
        if self.method == self.Method.MEET and self.meet_at and self.created_at and self.meet_at < self.created_at:
            raise ValidationError({'meet_at': 'Дата встречи не может быть раньше даты создания заявки.'})

    @property
    def book(self):
        return self.copy

    @property
    def owner(self):
        return self.copy.owner.reader

    @property
    def owner_id(self):
        return self.copy.owner.reader_id

    @property
    def requester_reader(self):
        return self.requester.reader

    def __str__(self):
        return f'Обмен №{self.pk}: {self.copy}'


class ExchangeStatusLog(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField('Предыдущий статус', max_length=12, choices=Exchange.Status.choices)
    new_status = models.CharField('Новый статус', max_length=12, choices=Exchange.Status.choices)
    changed_by = models.ForeignKey(Reader, on_delete=models.PROTECT, related_name='status_changes')
    changed_at = models.DateTimeField('Дата изменения', auto_now_add=True)

    class Meta:
        verbose_name = 'История статуса обмена'
        verbose_name_plural = 'История статусов обмена'
        ordering = ['changed_at']

    def __str__(self):
        return f'Обмен №{self.exchange_id}: {self.old_status} → {self.new_status}'


class Complaint(models.Model):
    class Reason(models.TextChoices):
        NOT_RECEIVED = 'not_received', 'Книга не получена'
        MISMATCH = 'mismatch', 'Не соответствует описанию'
        DAMAGED = 'damaged', 'Повреждена'
        OTHER = 'other', 'Другое'

    class Decision(models.TextChoices):
        FOR_REQUESTER = 'for_requester', 'В пользу получателя'
        FOR_OWNER = 'for_owner', 'В пользу владельца'
        REJECTED = 'rejected', 'Отклонена'

    exchange = models.OneToOneField(Exchange, on_delete=models.CASCADE, related_name='complaint')
    author = models.ForeignKey(ReaderProfile, on_delete=models.PROTECT, related_name='complaints')
    reason = models.CharField('Причина', max_length=30, choices=Reason.choices)
    description = models.TextField('Описание', validators=[MinLengthValidator(10), MaxLengthValidator(2000)])
    decision = models.CharField('Решение', max_length=15, choices=Decision.choices, blank=True)
    moderator = models.ForeignKey(Reader, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_complaints')
    decided_at = models.DateTimeField('Дата решения', null=True, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Жалоба'
        verbose_name_plural = 'Жалобы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Жалоба по обмену №{self.exchange_id}'


class Review(models.Model):
    exchange = models.OneToOneField(Exchange, on_delete=models.CASCADE, related_name='review')
    author = models.ForeignKey(ReaderProfile, on_delete=models.PROTECT, related_name='written_reviews')
    target = models.ForeignKey(ReaderProfile, on_delete=models.PROTECT, related_name='received_reviews')
    rating = models.PositiveSmallIntegerField('Оценка', validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField('Текст отзыва', max_length=1000, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        constraints = [models.CheckConstraint(check=Q(rating__gte=1) & Q(rating__lte=5), name='review_rating_1_5')]

    def __str__(self):
        return f'{self.rating}/5 — {self.author}'
