from django.db import models


class KtruGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    refine_attribute_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class KtruPosition(models.Model):
    class ParseStatus(models.TextChoices):
        PENDING = "pending", "Ожидает"
        SUCCESS = "success", "Успешно"
        FAILED = "failed", "Ошибка"
        FIXTURE = "fixture", "Fixture"

    group = models.ForeignKey(KtruGroup, null=True, blank=True, on_delete=models.SET_NULL, related_name="positions")
    code = models.CharField(max_length=64, unique=True)
    original_code_from_seed = models.CharField(max_length=64, blank=True)
    normalized_code = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=512)
    okpd2_code = models.CharField(max_length=64, blank=True)
    okpd2_name = models.CharField(max_length=512, blank=True)
    unit_name = models.CharField(max_length=128, blank=True)
    unit_code = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    is_enlarged = models.BooleanField(default=False)
    is_refined = models.BooleanField(default=True)
    status = models.CharField(max_length=128, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    source_url = models.URLField(blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    parse_status = models.CharField(max_length=16, choices=ParseStatus.choices, default=ParseStatus.PENDING)
    refine_value = models.CharField(max_length=255, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["group__name", "code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class KtruCharacteristic(models.Model):
    ktru_position = models.ForeignKey(KtruPosition, on_delete=models.CASCADE, related_name="characteristics")
    name = models.CharField(max_length=512)
    is_required = models.BooleanField(default=False)
    is_multiple_choice = models.BooleanField(default=False)
    unit_name = models.CharField(max_length=128, blank=True)
    instruction = models.TextField(blank=True)
    value_type = models.CharField(max_length=64, default="string")
    display_order = models.PositiveIntegerField(default=0)
    group_title = models.CharField(max_length=255, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["display_order", "name"]
        unique_together = ("ktru_position", "name")

    def __str__(self):
        return self.name


class KtruCharacteristicValue(models.Model):
    characteristic = models.ForeignKey(KtruCharacteristic, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=512)
    display_order = models.PositiveIntegerField(default=0)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["display_order", "value"]
        unique_together = ("characteristic", "value")

    def __str__(self):
        return self.value


class KtruPositionRelation(models.Model):
    enlarged_position = models.ForeignKey(KtruPosition, on_delete=models.CASCADE, related_name="refined_relations")
    refined_position = models.ForeignKey(KtruPosition, on_delete=models.CASCADE, related_name="enlarged_relations")
    refine_attribute_name = models.CharField(max_length=255)
    refine_attribute_value = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("enlarged_position", "refined_position", "refine_attribute_value")

    def __str__(self):
        return f"{self.enlarged_position.code} -> {self.refined_position.code}"


class KtruParseLog(models.Model):
    source = models.CharField(max_length=255)
    ktru_code = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=32)
    message = models.TextField(blank=True)
    raw_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source} {self.ktru_code} {self.status}"

