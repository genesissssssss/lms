import os
import sys
import django

print("🚀 Vercel build script running...")

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from accounts.models import UserProfile

print("📦 Running migrations...")
call_command('makemigrations', 'accounts', interactive=False)
call_command('makemigrations', 'core', interactive=False)
call_command('makemigrations', interactive=False)
call_command('migrate', interactive=False)

print("✅ Migrations complete!")

print("👤 Creating admin user...")
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    UserProfile.objects.create(user=user, role='admin')
    print("✅ Admin user created")
else:
    print("✅ Admin user already exists")

print("✅ Build script complete!")