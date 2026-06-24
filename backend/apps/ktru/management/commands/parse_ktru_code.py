from django.core.management.base import BaseCommand

from apps.ktru.models import KtruParseLog


class Command(BaseCommand):
    help = "Record a parse attempt by KTRU code. Live EIS URL resolution is intentionally isolated for MVP."

    def add_arguments(self, parser):
        parser.add_argument("ktru_code")

    def handle(self, *args, **options):
        code = options["ktru_code"]
        KtruParseLog.objects.create(
            source="code",
            ktru_code=code,
            status="pending",
            message="Для MVP используйте seed_ktru fixture или parse_ktru_url с готовой печатной формой ЕИС.",
        )
        self.stdout.write(self.style.WARNING("Code-to-EIS URL resolution is not enabled in offline MVP"))

