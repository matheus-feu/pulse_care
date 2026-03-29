import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import serializers

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone', 'password', 'confirm_password',
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
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data.get('phone', ''),
            password=validated_data['password'],
            role=User.Role.RECEPTIONIST,
            is_staff=False,
            is_superuser=False,
        )
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        """
        Always succeed (don't reveal whether the email exists).
        Store the user on the serializer for the view to use.
        """
        self._user = User.objects.filter(email__iexact=value, is_active=True).first()
        return value.lower()

    def get_reset_data(self):
        """Return uid + token if user was found, else None."""
        user = getattr(self, '_user', None)
        if user is None:
            return None
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return {'uid': uid, 'token': token, 'user': user}


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {'confirm_new_password': 'Passwords do not match.'},
                code='password_mismatch',
            )

        try:
            user_id = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(
                {'uid': 'Invalid or expired reset link.'},
                code='invalid_uid',
            )

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError(
                {'token': 'Invalid or expired reset token.'},
                code='invalid_token',
            )

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user
