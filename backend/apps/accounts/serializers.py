from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.accounts.crypto import encrypt_password_for_admin
from apps.accounts.models import RegistrationRequest, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "role", "is_approved", "is_staff")


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value.lower()

    def create(self, validated_data):
        raw_password = validated_data["password"]
        user = User.objects.create_user(
            email=validated_data["email"],
            password=raw_password,
            is_active=True,
            is_approved=False,
            encrypted_password_for_admin=encrypt_password_for_admin(raw_password),
        )
        RegistrationRequest.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["email"].lower(), password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Неверный email или пароль")
        if not user.is_approved and not user.is_superuser:
            raise serializers.ValidationError("Аккаунт ожидает одобрения администратора")
        attrs["user"] = user
        return attrs

