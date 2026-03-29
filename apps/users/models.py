from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        DOCTOR = 'doctor', 'Doctor'
        NURSE = 'nurse', 'Nurse'
        RECEPTIONIST = 'receptionist', 'Receptionist'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.RECEPTIONIST)
    license_number = models.CharField(max_length=30, blank=True, null=True, help_text='CRM / COREN / council number')
    specialty = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.get_full_name()} ({self.get_role_display()})'

    @property
    def full_name(self):
        return self.get_full_name()

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_nurse(self):
        return self.role == self.Role.NURSE
