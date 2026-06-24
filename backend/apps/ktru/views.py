from django.db.models import Count, Q
from rest_framework import decorators, permissions, response, status, viewsets

from apps.ktru.models import KtruGroup, KtruPosition, KtruPositionRelation
from apps.ktru.serializers import KtruGroupSerializer, KtruPositionDetailSerializer, KtruPositionSerializer


class KtruGroupViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = KtruGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return KtruGroup.objects.annotate(positions_count=Count("positions", filter=Q(positions__is_refined=True)))


class KtruPositionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in {"retrieve", "characteristics"}:
            return KtruPositionDetailSerializer
        return KtruPositionSerializer

    def get_queryset(self):
        queryset = KtruPosition.objects.select_related("group").prefetch_related("characteristics__values")
        group_id = self.request.query_params.get("group_id")
        if group_id:
            queryset = queryset.filter(group_id=group_id, is_refined=True)
        query = self.request.query_params.get("q") or self.request.query_params.get("search")
        if query:
            queryset = queryset.filter(
                Q(code__icontains=query)
                | Q(normalized_code__icontains=query)
                | Q(name__icontains=query)
                | Q(group__name__icontains=query)
                | Q(refine_value__icontains=query)
            )
        return queryset

    @decorators.action(detail=True, methods=["get"])
    def characteristics(self, request, pk=None):
        position = self.get_object()
        return response.Response(KtruPositionDetailSerializer(position).data)


@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.IsAuthenticated])
def resolve_refined(request):
    group_id = request.data.get("group_id")
    group_name = request.data.get("group_name")
    value = str(request.data.get("value", "")).strip()
    if not value:
        return response.Response({"detail": "Не указан уточняющий признак"}, status=status.HTTP_400_BAD_REQUEST)

    relations = KtruPositionRelation.objects.select_related("refined_position", "enlarged_position", "enlarged_position__group")
    if group_id:
        relations = relations.filter(enlarged_position__group_id=group_id)
    elif group_name:
        relations = relations.filter(enlarged_position__group__name__iexact=group_name)
    else:
        return response.Response({"detail": "Не указана группа КТРУ"}, status=status.HTTP_400_BAD_REQUEST)

    matches = list(relations.filter(refine_attribute_value__iexact=value))
    if len(matches) > 1:
        positions = [match.refined_position for match in matches]
        return response.Response(
            {
                "detail": "Уточняющий КТРУ не определен однозначно",
                "matches": len(matches),
                "positions": KtruPositionSerializer(positions, many=True).data,
            },
            status=status.HTTP_409_CONFLICT,
        )
    if not matches:
        return response.Response(
            {"detail": "Уточняющий КТРУ не найден", "matches": 0, "positions": []},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return response.Response(KtruPositionDetailSerializer(matches[0].refined_position).data)
