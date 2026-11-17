from django.contrib import admin

from .models import (
    Book, BookGenre, Complaint, Copy, CopyPhoto, Exchange, Genre,
    ExchangeStatusLog, Reader, ReaderProfile, Review,
)


@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    ordering = ('email',)
    list_display = ('email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    search_fields = ('email',)
    fields = ('email', 'password', 'role', 'is_active', 'last_login', 'date_joined')
    readonly_fields = ('date_joined',)

    def save_model(self, request, obj, form, change):
        if obj.password and not obj.password.startswith(('pbkdf2_sha256$', 'argon2$', 'bcrypt$', 'scrypt$')):
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)


@admin.register(ReaderProfile)
class ReaderProfileAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'reader', 'city', 'balance')
    search_fields = ('display_name', 'reader__email', 'city')
    list_filter = ('city',)


@admin.register(Book)
class CoreBookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'year', 'isbn')
    search_fields = ('title', 'author', 'isbn')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(BookGenre)
class BookGenreAdmin(admin.ModelAdmin):
    list_display = ('book', 'genre')
    list_filter = ('genre',)
    search_fields = ('book__title', 'genre__name')


@admin.register(Copy)
class CopyAdmin(admin.ModelAdmin):
    list_display = ('book', 'owner', 'city', 'condition', 'is_available', 'moderation_status', 'created_at')
    list_filter = ('city', 'condition', 'is_available', 'moderation_status')
    search_fields = ('book__title', 'book__author', 'owner__reader__email')


@admin.register(CopyPhoto)
class CopyPhotoAdmin(admin.ModelAdmin):
    list_display = ('copy', 'uploaded_at')


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ('id', 'copy', 'requester', 'status', 'method', 'created_at')
    list_filter = ('status', 'method')
    search_fields = ('copy__book__title', 'requester__reader__email')


@admin.register(ExchangeStatusLog)
class ExchangeStatusLogAdmin(admin.ModelAdmin):
    list_display = ('exchange', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('old_status', 'new_status')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('exchange', 'author', 'reason', 'decision', 'moderator', 'created_at')
    list_filter = ('reason', 'decision')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('exchange', 'author', 'target', 'rating', 'created_at')
    list_filter = ('rating',)
