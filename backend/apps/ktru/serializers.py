from rest_framework import serializers

from apps.ktru.models import KtruCharacteristic, KtruCharacteristicValue, KtruGroup, KtruPosition


class KtruCharacteristicValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = KtruCharacteristicValue
        fields = ("id", "value", "display_order")


class KtruCharacteristicSerializer(serializers.ModelSerializer):
    values = KtruCharacteristicValueSerializer(many=True, read_only=True)

    class Meta:
        model = KtruCharacteristic
        fields = (
            "id",
            "name",
            "is_required",
            "is_multiple_choice",
            "unit_name",
            "instruction",
            "value_type",
            "display_order",
            "group_title",
            "values",
        )


class KtruGroupSerializer(serializers.ModelSerializer):
    positions_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = KtruGroup
        fields = ("id", "name", "refine_attribute_name", "positions_count")


class KtruPositionSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = KtruPosition
        fields = (
            "id",
            "group",
            "group_name",
            "code",
            "name",
            "okpd2_code",
            "okpd2_name",
            "unit_name",
            "unit_code",
            "description",
            "is_enlarged",
            "is_refined",
            "status",
            "source_url",
            "refine_value",
            "parse_status",
        )


class KtruPositionDetailSerializer(KtruPositionSerializer):
    characteristics = KtruCharacteristicSerializer(many=True, read_only=True)

    class Meta(KtruPositionSerializer.Meta):
        fields = KtruPositionSerializer.Meta.fields + ("characteristics",)

