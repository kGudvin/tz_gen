from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import decorators, response, status, viewsets

from apps.exports.services import export_spec
from apps.specs.models import PostscriptTemplate, TechnicalSpec, TechnicalSpecItem
from apps.specs.permissions import IsApprovedUser, IsOwnerOrAdmin
from apps.specs.serializers import PostscriptTemplateSerializer, TechnicalSpecItemSerializer, TechnicalSpecSerializer


class PostscriptTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PostscriptTemplateSerializer
    permission_classes = [IsApprovedUser]

    def get_queryset(self):
        return PostscriptTemplate.objects.filter(is_active=True).order_by("name", "id")


class TechnicalSpecViewSet(viewsets.ModelViewSet):
    serializer_class = TechnicalSpecSerializer
    permission_classes = [IsApprovedUser, IsOwnerOrAdmin]

    def get_queryset(self):
        queryset = TechnicalSpec.objects.prefetch_related(
            "items__ktru_position",
            "items__selected_characteristics",
            "postscript_templates",
        )
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(user=self.request.user)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @decorators.action(detail=True, methods=["post"])
    def copy(self, request, pk=None):
        source = self.get_object()
        with transaction.atomic():
            clone = TechnicalSpec.objects.create(
                user=request.user,
                title=f"{source.title} (копия)",
                status=TechnicalSpec.Status.DRAFT,
                custom_postscript=source.custom_postscript,
            )
            clone.postscript_templates.set(source.postscript_templates.all())
            for item in source.items.prefetch_related("selected_characteristics"):
                new_item = TechnicalSpecItem.objects.create(
                    technical_spec=clone,
                    position_number=item.position_number,
                    ktru_position=item.ktru_position,
                    object_name=item.object_name,
                    quantity=item.quantity,
                    unit_name=item.unit_name,
                    display_order=item.display_order,
                )
                for characteristic in item.selected_characteristics.all():
                    characteristic.pk = None
                    characteristic.item = new_item
                    characteristic.save()
        return response.Response(TechnicalSpecSerializer(clone).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        spec = self.get_object()
        return response.Response(TechnicalSpecSerializer(spec).data)

    @decorators.action(detail=True, methods=["post"], url_path="items")
    def add_item(self, request, pk=None):
        spec = self.get_object()
        serializer = TechnicalSpecItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(technical_spec=spec)
        return response.Response(TechnicalSpecItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=["patch", "delete"], url_path=r"items/(?P<item_id>\d+)")
    def item_detail(self, request, pk=None, item_id=None):
        spec = self.get_object()
        item = get_object_or_404(TechnicalSpecItem, pk=item_id, technical_spec=spec)
        if request.method == "DELETE":
            item.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        serializer = TechnicalSpecItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return response.Response(TechnicalSpecItemSerializer(item).data)

    @decorators.action(detail=True, methods=["get"], url_path=r"export/(?P<fmt>docx|xlsx|pdf)")
    def export(self, request, pk=None, fmt=None):
        spec = self.get_object()
        document_export = export_spec(spec, fmt, request.user)
        url = request.build_absolute_uri(document_export.file.url)
        return response.Response({"url": url, "format": fmt, "export_id": document_export.id})
