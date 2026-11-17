# Демонстрационная фикстура

После выполнения `python manage.py seed_demo` создайте файл с реальными данными:

```powershell
python manage.py export_demo_fixture
```

Команда сохранит `fixtures/demo.json`. Для восстановления в чистой базе:

```powershell
python manage.py loaddata fixtures/demo.json
```

Файл `demo.json` намеренно создаётся локально: его содержимое зависит от фактического запуска миграций и заполнения базы данных.
