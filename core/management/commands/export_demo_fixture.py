from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = 'Экспортирует данные приложения core в fixtures/demo.json.'

    def handle(self, *args, **options):
        fixture_dir = Path(settings.BASE_DIR) / 'fixtures'
        fixture_dir.mkdir(parents=True, exist_ok=True)
        output_path = fixture_dir / 'demo.json'
        with open(output_path, 'w', encoding='utf-8') as stream:
            call_command('dumpdata', 'core', indent=2, stdout=stream)
        self.stdout.write(self.style.SUCCESS(f'Фикстура сохранена: {output_path}'))
