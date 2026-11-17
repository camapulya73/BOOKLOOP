from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Заполняет демонстрационными данными каноническую схему BOOKLOOP.'

    def handle(self, *args, **kwargs):
        call_command('seed_core_demo')
