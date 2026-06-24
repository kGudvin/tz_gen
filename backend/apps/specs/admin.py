from django.contrib import admin

from apps.specs.models import (
    DocumentExport,
    PostscriptTemplate,
    TechnicalSpec,
    TechnicalSpecItem,
    TechnicalSpecItemCharacteristic,
)


class TechnicalSpecItemCharacteristicInline(admin.TabularInline):
    model = TechnicalSpecItemCharacteristic
    extra = 0


class TechnicalSpecItemInline(admin.TabularInline):
    model = TechnicalSpecItem
    extra = 0


@admin.register(TechnicalSpec)
class TechnicalSpecAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "user__email")
    inlines = [TechnicalSpecItemInline]


@admin.register(TechnicalSpecItem)
class TechnicalSpecItemAdmin(admin.ModelAdmin):
    list_display = ("technical_spec", "position_number", "object_name", "ktru_position", "quantity", "unit_name")
    search_fields = ("technical_spec__title", "object_name", "ktru_position__code")
    inlines = [TechnicalSpecItemCharacteristicInline]


@admin.register(TechnicalSpecItemCharacteristic)
class TechnicalSpecItemCharacteristicAdmin(admin.ModelAdmin):
    list_display = ("item", "characteristic_name_snapshot", "display_value", "is_active", "is_required_snapshot")
    list_filter = ("is_active", "is_required_snapshot")
    search_fields = ("characteristic_name_snapshot", "display_value")


@admin.register(DocumentExport)
class DocumentExportAdmin(admin.ModelAdmin):
    list_display = ("technical_spec", "format", "created_at", "created_by")
    list_filter = ("format",)
    search_fields = ("technical_spec__title",)


@admin.register(PostscriptTemplate)
class PostscriptTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "text")

