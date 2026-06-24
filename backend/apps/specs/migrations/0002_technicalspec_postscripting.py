from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("specs", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="technicalspec",
            name="custom_postscript",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="technicalspec",
            name="postscript_templates",
            field=models.ManyToManyField(blank=True, related_name="technical_specs", to="specs.postscripttemplate"),
        ),
    ]
