import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="KtruGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("refine_attribute_name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="KtruParseLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(max_length=255)),
                ("ktru_code", models.CharField(blank=True, max_length=64)),
                ("status", models.CharField(max_length=32)),
                ("message", models.TextField(blank=True)),
                ("raw_response", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="KtruPosition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("original_code_from_seed", models.CharField(blank=True, max_length=64)),
                ("normalized_code", models.CharField(db_index=True, max_length=64)),
                ("name", models.CharField(max_length=512)),
                ("okpd2_code", models.CharField(blank=True, max_length=64)),
                ("okpd2_name", models.CharField(blank=True, max_length=512)),
                ("unit_name", models.CharField(blank=True, max_length=128)),
                ("unit_code", models.CharField(blank=True, max_length=64)),
                ("description", models.TextField(blank=True)),
                ("is_enlarged", models.BooleanField(default=False)),
                ("is_refined", models.BooleanField(default=True)),
                ("status", models.CharField(blank=True, max_length=128)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("source_url", models.URLField(blank=True)),
                ("raw_data", models.JSONField(blank=True, default=dict)),
                ("parse_status", models.CharField(choices=[("pending", "Ожидает"), ("success", "Успешно"), ("failed", "Ошибка"), ("fixture", "Fixture")], default="pending", max_length=16)),
                ("refine_value", models.CharField(blank=True, db_index=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("group", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="positions", to="ktru.ktrugroup")),
            ],
            options={"ordering": ["group__name", "code"]},
        ),
        migrations.CreateModel(
            name="KtruCharacteristic",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=512)),
                ("is_required", models.BooleanField(default=False)),
                ("is_multiple_choice", models.BooleanField(default=False)),
                ("unit_name", models.CharField(blank=True, max_length=128)),
                ("instruction", models.TextField(blank=True)),
                ("value_type", models.CharField(default="string", max_length=64)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("group_title", models.CharField(blank=True, max_length=255)),
                ("raw_data", models.JSONField(blank=True, default=dict)),
                ("ktru_position", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="characteristics", to="ktru.ktruposition")),
            ],
            options={"ordering": ["display_order", "name"], "unique_together": {("ktru_position", "name")}},
        ),
        migrations.CreateModel(
            name="KtruCharacteristicValue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("value", models.CharField(max_length=512)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("raw_data", models.JSONField(blank=True, default=dict)),
                ("characteristic", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="values", to="ktru.ktrucharacteristic")),
            ],
            options={"ordering": ["display_order", "value"], "unique_together": {("characteristic", "value")}},
        ),
        migrations.CreateModel(
            name="KtruPositionRelation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("refine_attribute_name", models.CharField(max_length=255)),
                ("refine_attribute_value", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("enlarged_position", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="refined_relations", to="ktru.ktruposition")),
                ("refined_position", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enlarged_relations", to="ktru.ktruposition")),
            ],
            options={"unique_together": {("enlarged_position", "refined_position", "refine_attribute_value")}},
        ),
    ]

