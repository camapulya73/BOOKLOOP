from django.contrib import admin

from .models import Favorite, Notification


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'copy', 'created_at')
    search_fields = ('user__email', 'copy__book__title')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('user__email', 'title', 'body')


admin.site.site_header = 'BOOKLOOP · Управление'
