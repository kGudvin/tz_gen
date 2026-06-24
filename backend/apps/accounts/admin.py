from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.html import format_html

from apps.accounts.crypto import decrypt_password_for_admin
from apps.accounts.models import RegistrationRequest, User


def mark_registration(user, status, reviewer):
    registration = getattr(user, "registration_request", None)
    if not registration:
        return
    registration.status = status
    registration.reviewed_at = timezone.now()
    registration.reviewed_by = reviewer
    registration.save(update_fields=["status", "reviewed_at", "reviewed_by"])


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "role", "is_approved", "registration_status", "is_staff", "date_joined")
    list_filter = ("role", "is_approved", "is_staff", "is_superuser")
    search_fields = ("email",)
    ordering = ("email",)
    readonly_fields = ("admin_password_preview",)
    actions = ("approve_users", "reject_users", "make_admins", "make_regular_users")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Права", {"fields": ("role", "is_approved", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Компромиссное бизнес-требование", {"fields": ("admin_password_preview",)}),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "role", "is_approved", "is_staff", "is_superuser")}),
    )

    @admin.display(description="Заявка")
    def registration_status(self, obj):
        registration = getattr(obj, "registration_request", None)
        return registration.get_status_display() if registration else "—"

    def admin_password_preview(self, obj):
        if not obj or not obj.encrypted_password_for_admin:
            return "Нет сохраненного зашифрованного значения"
        value = decrypt_password_for_admin(obj.encrypted_password_for_admin)
        if not value:
            return "Не удалось расшифровать"
        return format_html(
            '<details><summary style="cursor:pointer">Показать пароль</summary><code>{}</code></details>',
            value,
        )

    @admin.action(description="Одобрить выбранных пользователей")
    def approve_users(self, request, queryset):
        updated = queryset.update(is_approved=True, is_active=True)
        for user in queryset:
            mark_registration(user, RegistrationRequest.Status.APPROVED, request.user)
        self.message_user(request, f"Одобрено пользователей: {updated}", messages.SUCCESS)

    @admin.action(description="Отклонить и заблокировать выбранных пользователей")
    def reject_users(self, request, queryset):
        updated = queryset.update(is_approved=False, is_active=False)
        for user in queryset:
            mark_registration(user, RegistrationRequest.Status.REJECTED, request.user)
        self.message_user(request, f"Отклонено пользователей: {updated}", messages.WARNING)

    @admin.action(description="Сделать выбранных пользователей админами")
    def make_admins(self, request, queryset):
        updated = queryset.update(role=User.Role.ADMIN, is_staff=True, is_approved=True, is_active=True)
        self.message_user(request, f"Админами назначено: {updated}", messages.SUCCESS)

    @admin.action(description="Сделать выбранных пользователей обычными")
    def make_regular_users(self, request, queryset):
        updated = queryset.filter(is_superuser=False).update(role=User.Role.USER, is_staff=False)
        self.message_user(request, f"Роль изменена: {updated}", messages.SUCCESS)


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "created_at", "reviewed_at", "reviewed_by")
    list_filter = ("status",)
    search_fields = ("user__email",)
    actions = ("approve_requests", "reject_requests")

    @admin.action(description="Одобрить выбранные заявки")
    def approve_requests(self, request, queryset):
        for registration in queryset.select_related("user"):
            registration.status = RegistrationRequest.Status.APPROVED
            registration.reviewed_at = timezone.now()
            registration.reviewed_by = request.user
            registration.save(update_fields=["status", "reviewed_at", "reviewed_by"])
            registration.user.is_approved = True
            registration.user.is_active = True
            registration.user.save(update_fields=["is_approved", "is_active"])
        self.message_user(request, f"Одобрено заявок: {queryset.count()}", messages.SUCCESS)

    @admin.action(description="Отклонить выбранные заявки")
    def reject_requests(self, request, queryset):
        for registration in queryset.select_related("user"):
            registration.status = RegistrationRequest.Status.REJECTED
            registration.reviewed_at = timezone.now()
            registration.reviewed_by = request.user
            registration.save(update_fields=["status", "reviewed_at", "reviewed_by"])
            registration.user.is_approved = False
            registration.user.is_active = False
            registration.user.save(update_fields=["is_approved", "is_active"])
        self.message_user(request, f"Отклонено заявок: {queryset.count()}", messages.WARNING)
