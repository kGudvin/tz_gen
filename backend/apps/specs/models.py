from django.conf import settings
from django.db import models

from apps.ktru.models import KtruCharacteristic, KtruPosition


class TechnicalSpec(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        SAVED = "saved", "Сохранено"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="technical_specs")
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    postscript_templates = models.ManyToManyField("PostscriptTemplate", blank=True, related_name="technical_specs")
    custom_postscript = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class TechnicalSpecItem(models.Model):
    technical_spec = models.ForeignKey(TechnicalSpec, on_delete=models.CASCADE, related_name="items")
    position_number = models.PositiveIntegerField(default=1)
    ktru_position = models.ForeignKey(KtruPosition, on_delete=models.PROTECT)
    object_name = models.CharField(max_length=512)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_name = models.CharField(max_length=128)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "position_number", "id"]

    def __str__(self):
        return f"{self.position_number}. {self.object_name}"


class TechnicalSpecItemCharacteristic(models.Model):
    item = models.ForeignKey(TechnicalSpecItem, on_delete=models.CASCADE, related_name="selected_characteristics")
    ktru_characteristic = models.ForeignKey(KtruCharacteristic, on_delete=models.PROTECT)
    selected_values = models.JSONField(default=list, blank=True)
    display_value = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_required_snapshot = models.BooleanField(default=False)
    characteristic_name_snapshot = models.CharField(max_length=512)
    unit_name_snapshot = models.CharField(max_length=128, blank=True)
    instruction_snapshot = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.characteristic_name_snapshot


class PostscriptTemplate(models.Model):
    name = models.CharField(max_length=255)
    text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class DocumentExport(models.Model):
    class Format(models.TextChoices):
        DOCX = "docx", "DOCX"
        XLSX = "xlsx", "XLSX"
        PDF = "pdf", "PDF"

    technical_spec = models.ForeignKey(TechnicalSpec, on_delete=models.CASCADE, related_name="exports")
    format = models.CharField(max_length=8, choices=Format.choices)
    file = models.FileField(upload_to="exports/")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.technical_spec_id}.{self.format}"
