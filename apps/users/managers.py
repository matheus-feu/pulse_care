from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models


class UserQuerySet(models.QuerySet):
    """Reusable, chainable query methods for User."""

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def doctors(self):
        return self.filter(role='doctor')

    def nurses(self):
        return self.filter(role='nurse')

    def admins(self):
        return self.filter(role='admin')

    def receptionists(self):
        return self.filter(role='receptionist')

    def by_role(self, role):
        return self.filter(role=role)

    def search_by_name(self, name):
        return self.filter(
            models.Q(first_name__icontains=name)
            | models.Q(last_name__icontains=name)
        )

    def ordered(self):
        return self.order_by('first_name', 'last_name')


class UserManager(DjangoUserManager):
    """
    Custom manager for User that keeps Django's create_user / create_superuser
    while exposing chainable QuerySet helpers.
    """

    def get_queryset(self) -> UserQuerySet:
        return UserQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()

    def doctors(self):
        return self.get_queryset().doctors()

    def nurses(self):
        return self.get_queryset().nurses()

    def admins(self):
        return self.get_queryset().admins()

    def receptionists(self):
        return self.get_queryset().receptionists()

    def by_role(self, role):
        return self.get_queryset().by_role(role)

    def search_by_name(self, name):
        return self.get_queryset().search_by_name(name)

    def ordered(self):
        return self.get_queryset().ordered()

