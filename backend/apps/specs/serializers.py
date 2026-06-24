from django.db import transaction
from rest_framework import serializers

from apps.ktru.models import KtruCharacteristic, KtruCharacteristicValue, KtruPosition
from apps.ktru.serializers import KtruPositionSerializer
from apps.specs.instructions import instruction_for_unit
from apps.specs.models import PostscriptTemplate, TechnicalSpec, TechnicalSpecItem, TechnicalSpecItemCharacteristic


class PostscriptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostscriptTemplate
        fields = ("id", "name", "text", "is_active")


class SpecItemCharacteristicInputSerializer(serializers.Serializer):
    characteristic_id = serializers.IntegerField()
    selected_values = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    is_active = serializers.BooleanField(default=True)


class TechnicalSpecItemCharacteristicSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalSpecItemCharacteristic
        fields = (
            "id",
            "ktru_characteristic",
            "selected_values",
            "display_value",
            "is_active",
            "is_required_snapshot",
            "characteristic_name_snapshot",
            "unit_name_snapshot",
            "instruction_snapshot",
            "display_order",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["instruction_snapshot"] = instruction_for_unit(instance.unit_name_snapshot, instance.instruction_snapshot)
        return data


class TechnicalSpecItemSerializer(serializers.ModelSerializer):
    ktru_position_detail = KtruPositionSerializer(source="ktru_position", read_only=True)
    selected_characteristics = TechnicalSpecItemCharacteristicSerializer(many=True, read_only=True)
    characteristics = SpecItemCharacteristicInputSerializer(many=True, write_only=True)

    class Meta:
        model = TechnicalSpecItem
        fields = (
            "id",
            "technical_spec",
            "position_number",
            "ktru_position",
            "ktru_position_detail",
            "object_name",
            "quantity",
            "unit_name",
            "display_order",
            "characteristics",
            "selected_characteristics",
        )
        read_only_fields = ("technical_spec",)

    def validate(self, attrs):
        position = attrs.get("ktru_position") or getattr(self.instance, "ktru_position", None)
        if not position:
            raise serializers.ValidationError("Не указан КТРУ")
        if position.is_enlarged:
            raise serializers.ValidationError("Укрупненный КТРУ нельзя сохранить в итоговое ТЗ")
        if not attrs.get("unit_name") and not getattr(self.instance, "unit_name", ""):
            raise serializers.ValidationError("Единица измерения обязательна")
        if attrs.get("quantity") is None and not self.instance:
            raise serializers.ValidationError("Количество обязательно")

        characteristic_inputs = attrs.get("characteristics")
        if characteristic_inputs is None and self.instance:
            return attrs
        self._validate_characteristics(position, characteristic_inputs or [])
        return attrs

    def _validate_characteristics(self, position, characteristic_inputs):
        by_id = {item["characteristic_id"]: item for item in characteristic_inputs}
        characteristics = list(position.characteristics.prefetch_related("values"))
        characteristic_ids = {char.id for char in characteristics}
        unknown_ids = set(by_id) - characteristic_ids
        if unknown_ids:
            raise serializers.ValidationError(f"Характеристики не относятся к выбранному КТРУ: {sorted(unknown_ids)}")

        for characteristic in characteristics:
            item = by_id.get(characteristic.id)
            selected = item.get("selected_values", []) if item else []
            active = item.get("is_active", True) if item else True
            if characteristic.is_required and (not active or not selected):
                raise serializers.ValidationError(f"Не выбрана обязательная характеристика: {characteristic.name}")
            if selected:
                allowed = {value.value for value in characteristic.values.all()}
                invalid = [value for value in selected if value not in allowed]
                if invalid:
                    raise serializers.ValidationError(f"Недопустимые значения для {characteristic.name}: {', '.join(invalid)}")
                if not characteristic.is_multiple_choice and len(selected) > 1:
                    raise serializers.ValidationError(f"Для {characteristic.name} можно выбрать только одно значение")

    @transaction.atomic
    def create(self, validated_data):
        characteristic_inputs = validated_data.pop("characteristics", [])
        item = TechnicalSpecItem.objects.create(**validated_data)
        self._replace_characteristics(item, characteristic_inputs)
        return item

    @transaction.atomic
    def update(self, instance, validated_data):
        characteristic_inputs = validated_data.pop("characteristics", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if characteristic_inputs is not None:
            self._replace_characteristics(instance, characteristic_inputs)
        return instance

    def _replace_characteristics(self, item, characteristic_inputs):
        item.selected_characteristics.all().delete()
        by_id = {entry["characteristic_id"]: entry for entry in characteristic_inputs}
        for characteristic in item.ktru_position.characteristics.prefetch_related("values"):
            entry = by_id.get(characteristic.id, {})
            selected = entry.get("selected_values", [])
            active = bool(entry.get("is_active", True))
            if not characteristic.is_required and (not active or not selected):
                continue
            instruction = instruction_for_unit(characteristic.unit_name, characteristic.instruction)
            TechnicalSpecItemCharacteristic.objects.create(
                item=item,
                ktru_characteristic=characteristic,
                selected_values=selected,
                display_value="\n".join(selected) if characteristic.is_multiple_choice else (selected[0] if selected else ""),
                is_active=active,
                is_required_snapshot=characteristic.is_required,
                characteristic_name_snapshot=characteristic.name,
                unit_name_snapshot=characteristic.unit_name,
                instruction_snapshot=instruction,
                display_order=characteristic.display_order,
            )


class TechnicalSpecSerializer(serializers.ModelSerializer):
    items = TechnicalSpecItemSerializer(many=True, read_only=True)
    postscript_templates = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=PostscriptTemplate.objects.filter(is_active=True),
        required=False,
    )
    postscript_template_details = PostscriptTemplateSerializer(source="postscript_templates", many=True, read_only=True)

    class Meta:
        model = TechnicalSpec
        fields = (
            "id",
            "title",
            "status",
            "custom_postscript",
            "postscript_templates",
            "postscript_template_details",
            "created_at",
            "updated_at",
            "items",
        )
        read_only_fields = ("created_at", "updated_at")
