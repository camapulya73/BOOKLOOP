from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from core.models import Book, BookGenre, Copy, CopyPhoto, Genre, Reader, ReaderProfile


class RegisterForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'autocomplete': 'email'}))
    display_name = forms.CharField(max_length=60, min_length=2, label='Имя в профиле', widget=forms.TextInput(attrs={'minlength': 2}))
    city = forms.CharField(max_length=80, min_length=2, label='Город', widget=forms.TextInput(attrs={'minlength': 2}))
    phone = forms.CharField(max_length=20, required=False, label='Телефон', widget=forms.TelInput(attrs={'placeholder': '+79991234567'}))
    password1 = forms.CharField(min_length=8, label='Пароль', widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'minlength': 8}))
    password2 = forms.CharField(min_length=8, label='Повторите пароль', widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'minlength': 8}))

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Reader.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def clean_display_name(self):
        value = self.cleaned_data['display_name'].strip()
        if len(value) < 2:
            raise forms.ValidationError('Имя должно содержать не менее 2 символов.')
        return value

    def clean_city(self):
        value = self.cleaned_data['city'].strip()
        if len(value) < 2:
            raise forms.ValidationError('Укажите город (не менее 2 символов).')
        return value

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and (len(phone) != 12 or not phone.startswith('+7') or not phone[2:].isdigit()):
            raise forms.ValidationError('Введите номер в формате +79991234567.')
        return phone

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Пароли не совпадают.')
        if password1:
            try:
                validate_password(password1)
            except ValidationError as error:
                self.add_error('password1', error)
        return cleaned

    def save(self):
        reader = Reader.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            role=Reader.Role.READER,
        )
        ReaderProfile.objects.create(
            reader=reader,
            display_name=self.cleaned_data['display_name'],
            city=self.cleaned_data['city'],
            phone=self.cleaned_data.get('phone', ''),
        )
        return reader


class BookForm(forms.Form):
    title = forms.CharField(max_length=200, min_length=2, label='Название', widget=forms.TextInput(attrs={'minlength': 2}))
    author = forms.CharField(max_length=150, min_length=2, label='Автор', widget=forms.TextInput(attrs={'minlength': 2}))
    description = forms.CharField(max_length=3000, required=False, label='Описание', widget=forms.Textarea(attrs={'rows': 4}))
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(), required=True, label='Жанры', widget=forms.CheckboxSelectMultiple,
    )
    condition = forms.ChoiceField(choices=Copy.Condition.choices, label='Состояние')
    city = forms.CharField(max_length=80, min_length=2, label='Город', widget=forms.TextInput(attrs={'minlength': 2}))
    cover = forms.ImageField(required=False, label='Фотография экземпляра')

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 2:
            raise forms.ValidationError('Название должно содержать не менее 2 символов.')
        return title

    def clean_author(self):
        value = self.cleaned_data['author'].strip()
        if len(value) < 2:
            raise forms.ValidationError('Укажите автора (не менее 2 символов).')
        return value

    def clean_city(self):
        value = self.cleaned_data['city'].strip()
        if len(value) < 2:
            raise forms.ValidationError('Укажите город (не менее 2 символов).')
        return value

    def clean_cover(self):
        image = self.cleaned_data.get('cover')
        if image and image.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Размер изображения не должен превышать 2 МБ.')
        if image and image.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
            raise forms.ValidationError('Загрузите JPG, PNG или WebP.')
        return image

    def save(self, owner_profile):
        book, _ = Book.objects.get_or_create(
            title=self.cleaned_data['title'].strip(),
            author=self.cleaned_data['author'].strip(),
            defaults={'description': self.cleaned_data.get('description', '').strip()},
        )
        BookGenre.objects.bulk_create(
            [BookGenre(book=book, genre=genre) for genre in self.cleaned_data['genres']],
            ignore_conflicts=True,
        )
        copy = Copy.objects.create(
            book=book, owner=owner_profile, condition=self.cleaned_data['condition'],
            city=self.cleaned_data['city'].strip(), is_available=False,
            moderation_status=Copy.ModerationStatus.PENDING,
        )
        image = self.cleaned_data.get('cover')
        if image:
            CopyPhoto.objects.create(copy=copy, image=image)
        return copy


class ProfileForm(forms.Form):
    display_name = forms.CharField(max_length=60, min_length=2, label='Имя', widget=forms.TextInput(attrs={'minlength': 2}))
    email = forms.EmailField(max_length=254, label='Email')
    city = forms.CharField(max_length=80, min_length=2, label='Город', widget=forms.TextInput(attrs={'minlength': 2}))
    phone = forms.CharField(max_length=20, required=False, label='Телефон', widget=forms.TelInput(attrs={'placeholder': '+79991234567'}))

    def __init__(self, *args, reader=None, **kwargs):
        self.reader = reader
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Reader.objects.exclude(pk=self.reader.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError('Этот email уже используется другим пользователем.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and (len(phone) != 12 or not phone.startswith('+7') or not phone[2:].isdigit()):
            raise forms.ValidationError('Введите номер в формате +79991234567.')
        return phone

    def clean_display_name(self):
        value = self.cleaned_data['display_name'].strip()
        if len(value) < 2:
            raise forms.ValidationError('Имя должно содержать не менее 2 символов.')
        return value

    def clean_city(self):
        value = self.cleaned_data['city'].strip()
        if len(value) < 2:
            raise forms.ValidationError('Город должен содержать не менее 2 символов.')
        return value

    def save(self):
        self.reader.email = self.cleaned_data['email']
        self.reader.save(update_fields=['email'])
        profile = self.reader.readerprofile
        profile.display_name = self.cleaned_data['display_name']
        profile.city = self.cleaned_data['city']
        profile.phone = self.cleaned_data['phone']
        profile.save(update_fields=['display_name', 'city', 'phone'])
        return profile
