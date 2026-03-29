import re
from datetime import date

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    created_by = serializers.StringRelatedField(read_only=True)

    @extend_schema_field(serializers.CharField())
    def get_full_name(self, obj):
        return obj.full_name

    @extend_schema_field(serializers.IntegerField())
    def get_age(self, obj):
        return obj.age

    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate_cpf(self, value):
        digits = re.sub(r'\D', '', value)
        if len(digits) != 11:
            raise serializers.ValidationError(
                'CPF must have exactly 11 digits.',
                code='cpf_invalid_length',
            )

        formatted = f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'
        qs = Patient.objects.filter(cpf=formatted)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'A patient with this CPF already exists.',
                code='cpf_already_exists',
            )
        return formatted

    def validate_date_of_birth(self, value):
        if value >= date.today():
            raise serializers.ValidationError(
                'Date of birth must be in the past.',
                code='dob_in_future',
            )
        return value

    def validate_email(self, value):
        if not value:
            return value
        qs = Patient.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'A patient with this email already exists.',
                code='email_already_exists',
            )
        return value.lower()


class PatientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField())
    def get_full_name(self, obj):
        return obj.full_name

    @extend_schema_field(serializers.IntegerField())
    def get_age(self, obj):
        return obj.age

    class Meta:
        model = Patient
        fields = [
            'id', 'full_name', 'cpf', 'date_of_birth', 'age',
            'gender', 'phone', 'blood_type', 'is_active',
        ]
