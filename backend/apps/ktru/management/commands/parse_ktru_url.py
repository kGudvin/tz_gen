from django.core.management.base import BaseCommand

from apps.ktru.models import KtruParseLog
from apps.ktru.services import parse_ktru_print_form


class Command(BaseCommand):
    help = "Fetch and store raw KTRU print form payload for parser development."

    def add_arguments(self, parser):
        parser.add_argument("url")

    def handle(self, *args, **options):
        url = options["url"]
        try:
            data = parse_ktru_print_form(url)
            KtruParseLog.objects.create(source="url", status="success", message=url, raw_response=data.get("raw_text", ""))
            self.stdout.write(self.style.SUCCESS("Fetched KTRU print form"))
        except Exception as exc:
            KtruParseLog.objects.create(source="url", status="failed", message=str(exc))
            raise

