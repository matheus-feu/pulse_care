import hashlib
import logging
import random
from hmac import compare_digest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
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

    def _otp_key(self, email):
        return f'accounts:password-reset:otp:{email}'

    def _attempt_key(self, email):
        return f'accounts:password-reset:attempts:{email}'

    def _cooldown_key(self, email):
        return f'accounts:password-reset:cooldown:{email}'

    def _otp_hash(self, email, otp):
        base = f'{email}:{otp}:{settings.SECRET_KEY}'
        return hashlib.sha256(base.encode('utf-8')).hexdigest()

    def _generate_otp(self):
        return f'{random.SystemRandom().randint(0, 999999):06d}'

    def validate_email(self, value):
        """
        Always succeed (don't reveal whether the email exists).
        Store the user on the serializer for the view to use.
        """
        self._user = User.objects.filter(email__iexact=value, is_active=True).first()
        return value.lower()

    def save(self):
        """Generate and store OTP for active users while keeping anti-enumeration behavior."""
        email = self.validated_data['email']
        user = getattr(self, '_user', None)
        if user is None:
            return None

        if cache.get(self._cooldown_key(email)):
            logger.info(f'Password reset OTP requested within cooldown period email={email}')
            return {'user': user, 'otp': None, 'throttled': True, 'throttled_email': email}

        otp = self._generate_otp()
        otp_hash = self._otp_hash(email, otp)

        cache.set(
            self._otp_key(email),
            otp_hash,
            timeout=getattr(settings, 'PASSWORD_RESET_OTP_TTL_SECONDS', 300),
        )
        cache.delete(self._attempt_key(email))
        cache.set(
            self._cooldown_key(email),
            '1',
            timeout=getattr(settings, 'PASSWORD_RESET_OTP_RESEND_SECONDS', 60),
        )

        return {'user': user, 'otp': otp, 'throttled': False}


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )
    confirm_new_password = serializers.CharField(write_only=True)

    def _otp_key(self, email):
        return f'accounts:password-reset:otp:{email}'

    def _attempt_key(self, email):
        return f'accounts:password-reset:attempts:{email}'

    def _otp_hash(self, email, otp):
        base = f'{email}:{otp}:{settings.SECRET_KEY}'
        return hashlib.sha256(base.encode('utf-8')).hexdigest()

    def validate_email(self, value):
        return value.lower()

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('OTP must contain only digits.', code='invalid_otp')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {'confirm_new_password': 'Passwords do not match.'},
                code='password_mismatch',
            )

        email = attrs['email']
        max_attempts = getattr(settings, 'PASSWORD_RESET_OTP_MAX_ATTEMPTS', 5)
        current_attempts = cache.get(self._attempt_key(email), 0)
        if current_attempts >= max_attempts:
            raise serializers.ValidationError(
                {'otp': 'Too many invalid attempts. Request a new OTP.'},
                code='otp_attempts_exceeded',
            )

        stored_hash = cache.get(self._otp_key(email))
        provided_hash = self._otp_hash(email, attrs['otp'])

        if not stored_hash or not compare_digest(stored_hash, provided_hash):
            cache.set(
                self._attempt_key(email),
                current_attempts + 1,
                timeout=getattr(settings, 'PASSWORD_RESET_OTP_TTL_SECONDS', 300),
            )
            raise serializers.ValidationError(
                {'otp': 'Invalid or expired OTP.'},
                code='invalid_otp',
            )

        try:
            user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'otp': 'Invalid or expired OTP.'},
                code='invalid_otp',
            )

        attrs['user'] = user
        return attrs

    def save(self):
        email = self.validated_data['email']
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])

        cache.delete(self._otp_key(email))
        cache.delete(self._attempt_key(email))

        return user
