from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.ktru.views import KtruGroupViewSet, KtruPositionViewSet, resolve_refined
from apps.specs.views import PostscriptTemplateViewSet, TechnicalSpecViewSet

router = DefaultRouter()
router.register("ktru/groups", KtruGroupViewSet, basename="ktru-groups")
router.register("ktru/positions", KtruPositionViewSet, basename="ktru-positions")
router.register("specs", TechnicalSpecViewSet, basename="specs")
router.register("postscript-templates", PostscriptTemplateViewSet, basename="postscript-templates")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/ktru/resolve-refined/", resolve_refined, name="resolve-refined"),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
