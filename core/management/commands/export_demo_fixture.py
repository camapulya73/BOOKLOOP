from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = 'Экспортирует данные приложения core в fixtures/demo.json.'

    def handle(self, *args, **options):
        fixture_dir = Path(settings.BASE_DIR) / 'fixtures'
        fixture_dir.mkdir(parents=True, exist_ok=True)
        output_path = fixture_dir / 'demo.json'
        call_command('dumpdata', 'core', indent=2, output=str(output_path))
        self.stdout.write(self.style.SUCCESS(f'Фикстура сохранена: {output_path}'))
