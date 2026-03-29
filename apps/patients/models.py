from django.db import models
from django.conf import settings

from core.utils import calculate_age


class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'
        PREFER_NOT_TO_SAY = 'prefer_not_to_say', 'Prefer not to say'

    class BloodType(models.TextChoices):
        A_POS = 'A+', 'A+'
        A_NEG = 'A-', 'A-'
        B_POS = 'B+', 'B+'
        B_NEG = 'B-', 'B-'
        AB_POS = 'AB+', 'AB+'
        AB_NEG = 'AB-', 'AB-'
        O_POS = 'O+', 'O+'
        O_NEG = 'O-', 'O-'
        UNKNOWN = 'unknown', 'Unknown'

    # Personal info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=Gender.choices, default=Gender.PREFER_NOT_TO_SAY)
    cpf = models.CharField(max_length=14, unique=True, help_text='Brazilian CPF (e.g. 000.000.000-00)')
    rg = models.CharField(max_length=20, blank=True, null=True, verbose_name='RG')

    # Contact
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    # Address
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    street = models.CharField(max_length=200, blank=True, null=True)
    number = models.CharField(max_length=10, blank=True, null=True)
    complement = models.CharField(max_length=100, blank=True, null=True)
    neighborhood = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)

    # Medical info
    blood_type = models.CharField(max_length=10, choices=BloodType.choices, default=BloodType.UNKNOWN)
    allergies = models.TextField(blank=True, null=True)
    chronic_conditions = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True, verbose_name='General notes')

    # Emergency contact
    emergency_contact_name = models.CharField(max_length=150, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True)

    # Insurance
    insurance_provider = models.CharField(max_length=100, blank=True, null=True)
    insurance_plan = models.CharField(max_length=100, blank=True, null=True)
    insurance_number = models.CharField(max_length=50, blank=True, null=True)

    # Meta
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='patients_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def age(self):
        return calculate_age(self.date_of_birth)

