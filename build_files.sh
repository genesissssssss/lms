#!/bin/bash

echo "=========================================="
echo "🚀 Starting Vercel build process"
echo "=========================================="

# Display current directory and Python version
echo "📁 Current directory: $(pwd)"
echo "🐍 Python version: $(python --version)"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Show installed packages
echo "📋 Installed packages:"
pip list | grep -E "Django|psycopg2|cloudinary|whitenoise"

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# CRITICAL: Run migrations to create database tables
echo "=========================================="
echo "🗄️  Running database migrations..."
echo "=========================================="

# Make migrations for all apps
echo "🔨 Creating migrations..."
python manage.py makemigrations accounts --noinput
python manage.py makemigrations core --noinput
python manage.py makemigrations --noinput

# Apply migrations to the database
echo "🔄 Applying migrations..."
python manage.py migrate --noinput

# Verify migrations
echo "✅ Verifying migrations..."
python manage.py showmigrations

# Create superuser if it doesn't exist
echo "=========================================="
echo "👤 Setting up admin user..."
echo "=========================================="

python manage.py shell <<EOF
from django.contrib.auth.models import User
from accounts.models import UserProfile
import os

username = 'admin'
password = 'admin123'
email = 'admin@example.com'

# Check if admin user exists
if not User.objects.filter(username=username).exists():
    print(f"Creating admin user: {username}")
    user = User.objects.create_superuser(username, email, password)
    UserProfile.objects.create(user=user, role='admin')
    print("✅ Admin user created successfully")
else:
    print("✅ Admin user already exists")
    
    # Ensure admin has correct role
    user = User.objects.get(username=username)
    profile, created = UserProfile.objects.get_or_create(user=user, defaults={'role': 'admin'})
    if not created and profile.role != 'admin':
        profile.role = 'admin'
        profile.save()
        print("✅ Updated admin role")
EOF

echo "=========================================="
echo "✅ Build completed successfully!"
echo "=========================================="