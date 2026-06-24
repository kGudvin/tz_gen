from pathlib import Path

from django.core.management.base import BaseCommand

from apps.ktru.models import KtruParseLog
from apps.ktru.services import load_eis_html_dir, load_fixture, load_seed_excel, upsert_excel_seed_entries


class Command(BaseCommand):
    help = "Load MVP KTRU data from fixture JSON, Excel refined codes, and EIS HTML print forms."

    def add_arguments(self, parser):
        parser.add_argument("--fixture", default="/app/fixtures/ktru_fixture.json")
        parser.add_argument("--excel", default="/app/fixtures/Краткое КТРУ.xlsx")
        parser.add_argument("--html-dir", default="/app/fixtures/eis_html")

    def handle(self, *args, **options):
        fixture = Path(options["fixture"])
        if not fixture.exists():
            fixture = Path.cwd().parent / "fixtures" / "ktru_fixture.json"
        load_fixture(fixture)
        self.stdout.write(self.style.SUCCESS(f"Loaded fixture: {fixture}"))

        excel = options.get("excel")
        if excel:
            try:
                excel_path = Path(excel)
                if not excel_path.exists():
                    excel_path = Path.cwd().parent / "fixtures" / "Краткое КТРУ.xlsx"
                entries = load_seed_excel(excel_path)
                upsert_excel_seed_entries(entries)
                KtruParseLog.objects.create(source="excel", status="success", message=f"Loaded {len(entries)} rows from {excel_path}")
                self.stdout.write(self.style.SUCCESS(f"Loaded {len(entries)} refined codes from seed Excel"))
            except Exception as exc:
                KtruParseLog.objects.create(source="excel", status="failed", message=str(exc))
                self.stdout.write(self.style.WARNING(f"Excel read failed: {exc}"))

        html_dir = Path(options["html_dir"])
        if not html_dir.exists():
            html_dir = Path.cwd().parent / "fixtures" / "eis_html"
        loaded_html = load_eis_html_dir(html_dir)
        if loaded_html:
            self.stdout.write(self.style.SUCCESS(f"Loaded EIS HTML print forms: {loaded_html}"))
