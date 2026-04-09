"""
Management command to create default admin accounts for Pandeli System.
Run: python manage.py create_default_admins
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile


class Command(BaseCommand):
    help = 'Creates default admin accounts: Main Branch (Owner) and Production Admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='Pandeli@2025',
            help='Default password for both accounts (change in production!)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Reset password if users already exist'
        )

    def handle(self, *args, **options):
        password = options['password']
        force = options['force']
        
        accounts = [
            {
                'username': 'admin_main',
                'email': 'admin@pandeli.com',
                'first_name': 'Main',
                'last_name': 'Branch',
                'role': 'admin',
                'description': 'Main Branch (Owner)',
            },
            {
                'username': 'admin_production',
                'email': 'production@pandeli.com',
                'first_name': 'Production',
                'last_name': 'Admin',
                'role': 'production_admin',
                'description': 'Production Admin',
            },
        ]
        
        for acc in accounts:
            user, created = User.objects.get_or_create(
                username=acc['username'],
                defaults={
                    'email': acc['email'],
                    'first_name': acc['first_name'],
                    'last_name': acc['last_name'],
                    'is_staff': True,
                    'is_superuser': acc['role'] == 'admin',
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.role = acc['role']
                profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Created {acc['description']}: {acc['username']} / {password}")
                )
            else:
                if force:
                    user.set_password(password)
                    user.save()
                    profile, _ = UserProfile.objects.get_or_create(user=user)
                    profile.role = acc['role']
                    profile.save()
                    self.stdout.write(
                        self.style.WARNING(f"Reset password for {acc['username']}")
                    )
                else:
                    self.stdout.write(
                        self.style.NOTICE(f"User {acc['username']} already exists (use --force to reset password)")
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f"\nDefault login credentials:")
        )
        self.stdout.write("  Main Branch (Owner):     admin_main / " + password)
        self.stdout.write("  Production Admin:        admin_production / " + password)
        self.stdout.write("\n  IMPORTANT: Change these passwords in production!")
