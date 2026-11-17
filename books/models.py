from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import Copy


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    copy = models.ForeignKey(Copy, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [models.UniqueConstraint(fields=['user', 'copy'], name='unique_user_favorite_copy')]

    def __str__(self):
        return f'{self.user} ♥ {self.copy}'


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=500)
    url = models.CharField(max_length=250, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
