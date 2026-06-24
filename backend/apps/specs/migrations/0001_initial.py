import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ktru", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PostscriptTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("text", models.TextField()),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="TechnicalSpec",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("draft", "Черновик"), ("saved", "Сохранено")], default="draft", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="technical_specs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="TechnicalSpecItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position_number", models.PositiveIntegerField(default=1)),
                ("object_name", models.CharField(max_length=512)),
                ("quantity", models.DecimalField(decimal_places=2, max_digits=12)),
                ("unit_name", models.CharField(max_length=128)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("ktru_position", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="ktru.ktruposition")),
                ("technical_spec", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="specs.technicalspec")),
            ],
            options={"ordering": ["display_order", "position_number", "id"]},
        ),
        migrations.CreateModel(
            name="TechnicalSpecItemCharacteristic",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("selected_values", models.JSONField(blank=True, default=list)),
                ("display_value", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_required_snapshot", models.BooleanField(default=False)),
                ("characteristic_name_snapshot", models.CharField(max_length=512)),
                ("unit_name_snapshot", models.CharField(blank=True, max_length=128)),
                ("instruction_snapshot", models.TextField(blank=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="selected_characteristics", to="specs.technicalspecitem")),
                ("ktru_characteristic", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="ktru.ktrucharacteristic")),
            ],
            options={"ordering": ["display_order", "id"]},
        ),
        migrations.CreateModel(
            name="DocumentExport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("format", models.CharField(choices=[("docx", "DOCX"), ("xlsx", "XLSX"), ("pdf", "PDF")], max_length=8)),
                ("file", models.FileField(upload_to="exports/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("technical_spec", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exports", to="specs.technicalspec")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]

