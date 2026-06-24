import tempfile
from pathlib import Path

from django.test import TestCase

from apps.accounts.models import User
from apps.exports.services import build_docx
from apps.ktru.models import KtruCharacteristic, KtruCharacteristicValue, KtruGroup, KtruPosition
from apps.specs.instructions import DEFAULT_IMMUTABLE_INSTRUCTION, DEFAULT_MUTABLE_INSTRUCTION
from apps.specs.models import TechnicalSpec, TechnicalSpecItem
from apps.specs.serializers import TechnicalSpecItemSerializer


class SpecInstructionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="password", is_approved=True)
        self.group = KtruGroup.objects.create(name="системный блок", refine_attribute_name="ОЗУ")
        self.position = KtruPosition.objects.create(
            group=self.group,
            code="26.20.15.000-00000001",
            normalized_code="26.20.15.000-00000001",
            name="Системный блок",
            unit_name="Штука",
            is_refined=True,
            refine_value="8",
        )
        self.required = KtruCharacteristic.objects.create(
            ktru_position=self.position,
            name="Объем оперативной памяти",
            is_required=True,
            unit_name="Гигабайт",
            display_order=1,
        )
        KtruCharacteristicValue.objects.create(characteristic=self.required, value="8", display_order=1)
        self.no_unit = KtruCharacteristic.objects.create(
            ktru_position=self.position,
            name="Тип корпуса",
            is_required=True,
            unit_name="",
            display_order=2,
        )
        KtruCharacteristicValue.objects.create(characteristic=self.no_unit, value="Mini Tower", display_order=1)
        self.spec = TechnicalSpec.objects.create(user=self.user, title="ТЗ")

    def test_no_unit_characteristic_gets_immutable_instruction(self):
        serializer = TechnicalSpecItemSerializer(
            data={
                "position_number": 1,
                "ktru_position": self.position.id,
                "object_name": "Системный блок",
                "quantity": "1",
                "unit_name": "Штука",
                "display_order": 1,
                "characteristics": [
                    {"characteristic_id": self.required.id, "selected_values": ["8"], "is_active": True},
                    {"characteristic_id": self.no_unit.id, "selected_values": ["Mini Tower"], "is_active": True},
                ],
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        item = serializer.save(technical_spec=self.spec)

        with_unit = item.selected_characteristics.get(ktru_characteristic=self.required)
        without_unit = item.selected_characteristics.get(ktru_characteristic=self.no_unit)
        self.assertEqual(with_unit.instruction_snapshot, DEFAULT_MUTABLE_INSTRUCTION)
        self.assertEqual(without_unit.instruction_snapshot, DEFAULT_IMMUTABLE_INSTRUCTION)

    def test_docx_export_creates_file(self):
        item = TechnicalSpecItem.objects.create(
            technical_spec=self.spec,
            position_number=1,
            ktru_position=self.position,
            object_name="Системный блок",
            quantity=1,
            unit_name="Штука",
            display_order=1,
        )
        serializer = TechnicalSpecItemSerializer()
        serializer._replace_characteristics(
            item,
            [
                {"characteristic_id": self.required.id, "selected_values": ["8"], "is_active": True},
                {"characteristic_id": self.no_unit.id, "selected_values": ["Mini Tower"], "is_active": True},
            ],
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spec.docx"
            build_docx(self.spec, path)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)
