# BOOKLOOP — Django · вариант 18

Учебный проект BookCrossing с адаптивным интерфейсом BOOKLOOP (DM Sans, зелёная
палитра, карточки книг) и отдельной канонической моделью базы данных `core`,
соответствующей ER-модели отчёта №5 (с отдельным справочником Genre для корректной связи M:N).

## Важно перед первым запуском

В проекте используется собственная модель пользователя `core.Reader`.
Если вы запускали предыдущую версию BOOKLOOP, **удалите старый `db.sqlite3`** до
создания миграций: схему пользователя нельзя безопасно менять в уже созданной БД.

## Запуск на Windows PowerShell

Откройте терминал в папке с `manage.py` и выполните команды по порядку:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py check
python manage.py makemigrations core books
python manage.py migrate
python manage.py seed_demo
python manage.py export_demo_fixture
python manage.py test
python manage.py runserver
```

Откройте `http://127.0.0.1:8000/` и админку `http://127.0.0.1:8000/admin/`.

### Демонстрационная учётная запись

Команда `seed_demo` создаёт 20 читателей в `core` и тестового администратора:

- Email: `reader01@example.com`
- Пароль: `BookloopDemo2026!`

Для проверки обычного читателя используйте `reader02@example.com` с тем же
демонстрационным паролем. Не используйте эти пароли в реальном развёртывании.

## Каноническая схема отчёта №5 — приложение `core`

1. Reader
2. ReaderProfile
3. Book
4. Genre
5. BookGenre
6. Copy
7. CopyPhoto
8. Exchange
9. ExchangeStatusLog
10. Complaint
11. Review

Миграции создаются локально через `makemigrations core books`. Команда
`seed_demo` заполняет канонические таблицы `core_*` и демонстрационные данные,
которые использует текущий интерфейс.

Для выгрузки фикстуры после заполнения базы выполните:

```powershell
python manage.py export_demo_fixture
```

Файл появится в `fixtures/demo.json`. Для восстановления в пустой БД после миграций:

```powershell
python manage.py loaddata fixtures/demo.json
```

## Пять запросов для отчёта

В `docs/queries.py` находятся запросы 9.1–9.5: фильтрация, сортировка,
агрегация, `select_related` и `prefetch_related`. Запуск:

```powershell
python manage.py shell < docs/queries.py
```

Вывод консоли нужно скопировать в отчёт после реального запуска на своём ПК.

## Страницы интерфейса

`/` главная · `/catalog/` каталог · `/books/<id>/` карточка · `/books/add/`
добавление · `/exchanges/` обмены · `/profile/` профиль · `/moderation/`
модерация · `/accounts/login/` вход · `/register/` регистрация.

## Структура проекта

- `core/` — каноническая ER-модель, пользователь, экземпляры и данные отчёта №5.
- `books/` — веб-интерфейс, формы, представления, избранное и уведомления.
- `docs/er_model.dbml` — ER-модель `core`.
- `docs/queries.py` — пять ORM/SQL-запросов.
- `docs/relations.md`, `docs/normalization.md` — связи и нормализация.
- `docs/mobile_test_checklist.md` — ручная проверка адаптивности.

Веб-интерфейс работает с каноническими моделями `core.Book`, `core.Copy`, `core.Exchange` и `core.Review`. В приложении `books` остаются только вспомогательные модели избранного и уведомлений.
## Перед сдачей

- Выполнить команды запуска без ошибок.
- Сделать скриншот списка таблиц `core_*` после `migrate`.
- Сделать скриншот заполненных `core_exchange` и `core_review` после `seed_demo`.
- Выполнить пять запросов из `docs/queries.py`, вставить реальный SQL и результаты.
- Проверить страницы на ширинах 360, 375, 768, 1024 и 1440 px.
- Проверить тесты и заполнить чек-лист `docs/acceptance_checklist.md`.

Для production задайте `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`,
настройте HTTPS, почту, резервное копирование и безопасное хранение media.
