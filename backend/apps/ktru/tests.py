from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import User
from apps.ktru.models import KtruGroup, KtruPosition, KtruPositionRelation


class ResolveRefinedTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="password", is_approved=True)
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.group = KtruGroup.objects.create(name="монитор", refine_attribute_name="Диагональ")
        self.enlarged = KtruPosition.objects.create(
            group=self.group,
            code="26.20.17.110-00000000",
            normalized_code="26.20.17.110-00000000",
            name="монитор",
            is_enlarged=True,
            is_refined=False,
        )

    def create_refined(self, code):
        position = KtruPosition.objects.create(
            group=self.group,
            code=code,
            normalized_code=code,
            name=f"монитор {code}",
            is_enlarged=False,
            is_refined=True,
            refine_value="27",
        )
        KtruPositionRelation.objects.create(
            enlarged_position=self.enlarged,
            refined_position=position,
            refine_attribute_name="Диагональ",
            refine_attribute_value="27",
        )
        return position

    def test_ambiguous_refine_returns_choices(self):
        self.create_refined("26.20.17.110-00000001")
        self.create_refined("26.20.17.110-00000002")

        response = self.client.post(reverse("resolve-refined"), {"group_id": self.group.id, "value": "27"}, format="json")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["matches"], 2)
        self.assertEqual(len(response.data["positions"]), 2)
