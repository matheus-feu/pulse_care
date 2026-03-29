from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from .models import User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField())
    def get_full_name(self, obj):
        return obj.get_full_name()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'license_number', 'specialty', 'phone', 'avatar',
            'is_active', 'is_staff', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, label='Confirm password')

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'license_number', 'specialty', 'phone',
            'password', 'confirm_password',
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'A user with this email already exists.',
                code='email_already_exists',
            )
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                'A user with this username already exists.',
                code='username_already_exists',
            )
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match.'},
                code='password_mismatch',
            )

        role = attrs.get('role')
        license_number = attrs.get('license_number')
        if role in (User.Role.DOCTOR, User.Role.NURSE) and not license_number:
            raise serializers.ValidationError(
                {'license_number': f'License number is required for the {role} role.'},
                code='license_required',
            )

        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'avatar',
            'license_number', 'specialty',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {'confirm_new_password': 'Passwords do not match.'},
                code='password_mismatch',
            )
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {'new_password': 'New password must be different from the current password.'},
                code='same_password',
            )
        return attrs

