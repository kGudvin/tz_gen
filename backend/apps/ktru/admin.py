import tempfile
from pathlib import Path

from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from apps.ktru.models import (
    KtruCharacteristic,
    KtruCharacteristicValue,
    KtruGroup,
    KtruParseLog,
    KtruPosition,
    KtruPositionRelation,
)
from apps.ktru.services import load_eis_html_dir, load_fixture, load_seed_excel, upsert_excel_seed_entries


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(MultipleFileField, self).clean(file, initial) for file in files]


class KtruImportForm(forms.Form):
    fixture_json = forms.FileField(label="Fixture JSON", required=False)
    excel = forms.FileField(label="Excel с уточненными КТРУ", required=False)
    html_files = MultipleFileField(label="HTML-печатные формы ЕИС", required=False)


class KtruCharacteristicValueInline(admin.TabularInline):
    model = KtruCharacteristicValue
    extra = 0


@admin.register(KtruCharacteristic)
class KtruCharacteristicAdmin(admin.ModelAdmin):
    list_display = ("name", "ktru_position", "is_required", "is_multiple_choice", "unit_name", "display_order")
    list_filter = ("is_required", "is_multiple_choice", "unit_name")
    search_fields = ("name", "ktru_position__code", "ktru_position__name")
    inlines = [KtruCharacteristicValueInline]


@admin.register(KtruGroup)
class KtruGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "refine_attribute_name", "refined_positions", "import_link")
    search_fields = ("name",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-ktru/", self.admin_site.admin_view(self.import_ktru), name="ktru_import"),
        ]
        return custom_urls + urls

    @admin.display(description="Уточненных позиций")
    def refined_positions(self, obj):
        return obj.positions.filter(is_refined=True).count()

    @admin.display(description="Импорт")
    def import_link(self, obj):
        url = reverse("admin:ktru_import")
        return format_html('<a class="button" href="{}">Обновить КТРУ</a>', url)

    def import_ktru(self, request):
        if request.method == "POST":
            form = KtruImportForm(request.POST, request.FILES)
            if form.is_valid():
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_dir = Path(tmp)
                    if form.cleaned_data["fixture_json"]:
                        fixture_path = tmp_dir / form.cleaned_data["fixture_json"].name
                        _save_uploaded_file(form.cleaned_data["fixture_json"], fixture_path)
                        load_fixture(fixture_path)
                        messages.success(request, f"Fixture загружен: {fixture_path.name}")

                    if form.cleaned_data["excel"]:
                        excel_path = tmp_dir / form.cleaned_data["excel"].name
                        _save_uploaded_file(form.cleaned_data["excel"], excel_path)
                        entries = load_seed_excel(excel_path)
                        upsert_excel_seed_entries(entries)
                        messages.success(request, f"Excel загружен, уточненных кодов: {len(entries)}")

                    html_files = form.cleaned_data["html_files"]
                    if html_files:
                        html_dir = tmp_dir / "html"
                        html_dir.mkdir()
                        for html_file in html_files:
                            _save_uploaded_file(html_file, html_dir / html_file.name)
                        loaded = load_eis_html_dir(html_dir)
                        messages.success(request, f"HTML-форм ЕИС загружено: {loaded}")

                    if not any((form.cleaned_data["fixture_json"], form.cleaned_data["excel"], form.cleaned_data["html_files"])):
                        messages.warning(request, "Файлы не выбраны.")
                return redirect("admin:ktru_ktrugroup_changelist")
        else:
            form = KtruImportForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Импорт КТРУ",
            "form": form,
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/ktru/import.html", context)


def _save_uploaded_file(uploaded_file, path: Path) -> None:
    with path.open("wb") as fh:
        for chunk in uploaded_file.chunks():
            fh.write(chunk)


@admin.register(KtruPosition)
class KtruPositionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "group", "refine_value", "is_enlarged", "is_refined", "parse_status")
    list_filter = ("group", "is_enlarged", "is_refined", "parse_status")
    search_fields = ("code", "name", "okpd2_code", "refine_value")


@admin.register(KtruCharacteristicValue)
class KtruCharacteristicValueAdmin(admin.ModelAdmin):
    list_display = ("value", "characteristic", "display_order")
    search_fields = ("value", "characteristic__name")


@admin.register(KtruPositionRelation)
class KtruPositionRelationAdmin(admin.ModelAdmin):
    list_display = ("enlarged_position", "refined_position", "refine_attribute_name", "refine_attribute_value")
    search_fields = ("enlarged_position__code", "refined_position__code", "refine_attribute_value")


@admin.register(KtruParseLog)
class KtruParseLogAdmin(admin.ModelAdmin):
    list_display = ("source", "ktru_code", "status", "created_at")
    list_filter = ("source", "status")
    search_fields = ("ktru_code", "message")
    readonly_fields = ("source", "ktru_code", "status", "message", "raw_response", "created_at")
