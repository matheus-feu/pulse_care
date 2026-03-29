from decouple import config
from django.core.management.base import BaseCommand

from apps.users.models import User


class Command(BaseCommand):
    help = 'Create or update the default admin superuser from environment variables.'

    def handle(self, *args, **options):
        username = config('USER_ADMIN', default='admin')
        password = config('USER_ADMIN_PASSWORD', default='AdminPass123')
        email = config('USER_ADMIN_EMAIL', default='admin@pulsecare.com')

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'Admin',
                'last_name': 'PulseCare',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )

        if created:
            user.set_password(password)
            user.save(update_fields=['password'])
            self.stdout.write(self.style.SUCCESS(
                f'✅ Superuser created  →  username={username}  email={email}',
            ))
        else:
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.role = User.Role.ADMIN
            user.save(update_fields=['password', 'is_staff', 'is_superuser', 'role'])
            self.stdout.write(self.style.WARNING(
                f'⚠️  Superuser already exists  →  username={username}  (password updated)',
            ))
