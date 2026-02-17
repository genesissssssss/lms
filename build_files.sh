#!/bin/bash

echo "🚀 Building project..."
echo "Current directory: $(pwd)"

# Install dependencies
pip install -r requirements.txt

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# CRITICAL: Run migrations to create database tables
echo "📦 Running database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Create superuser if it doesn't exist (optional)
echo "👤 Checking if admin user exists..."
python manage.py shell -c "
from django.contrib.auth.models import User;
from accounts.models import UserProfile;
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    UserProfile.objects.create(user=user, role='admin')
    print('✅ Admin user created')
else:
    print('✅ Admin user already exists')
"

echo "✅ Build complete!"