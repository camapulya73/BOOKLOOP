"""Регистронезависимый LIKE для SQLite.

Встроенный LIKE в SQLite игнорирует регистр только у символов ASCII, поэтому
Django-запросы icontains не находили кириллицу, набранную в другом регистре
(например, «оруэлл» вместо «Оруэлл»). Подменяем функцию like() на вариант,
который учитывает Unicode. На PostgreSQL этот код не используется.
"""
import re
from functools import lru_cache

from django.db.backends.signals import connection_created


@lru_cache(maxsize=256)
def _compile(pattern, escape):
    parts = []
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if escape and ch == escape and i + 1 < len(pattern):
            parts.append(re.escape(pattern[i + 1]))
            i += 2
            continue
        if ch == '%':
            parts.append('.*')
        elif ch == '_':
            parts.append('.')
        else:
            parts.append(re.escape(ch))
        i += 1
    return re.compile(''.join(parts), re.IGNORECASE | re.DOTALL)


def unicode_like(pattern, value, escape=None):
    if pattern is None or value is None:
        return None
    return 1 if _compile(pattern, escape).fullmatch(str(value)) else 0


def register_unicode_like(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        raw = connection.connection
        raw.create_function('like', 2, unicode_like, deterministic=True)
        raw.create_function('like', 3, unicode_like, deterministic=True)


def connect():
    connection_created.connect(register_unicode_like, dispatch_uid='core_unicode_like')
