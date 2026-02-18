#!/bin/bash

echo "🚀 Starting build process..."

# Install dependencies
echo "📦 Installing dependencies..."
python3.9 -m pip install -r requirements.txt

# Show environment (debug)
echo "🔍 Python version: $(python3.9 --version)"
echo "🔍 Current directory: $(pwd)"
echo "🔍 Files in directory: $(ls -la)"

# Run migrations
echo "🔄 Running migrations..."
python3.9 manage.py makemigrations accounts --noinput
python3.9 manage.py makemigrations core --noinput
python3.9 manage.py makemigrations --noinput
python3.9 manage.py migrate --noinput

# Check if migration worked
echo "✅ Checking database tables..."
python3.9 manage.py shell -c "
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT tablename FROM pg_tables WHERE schemaname=\\'public\\';')
        tables = cursor.fetchall()
        print(f'Tables in database: {[t[0] for t in tables]}')
except Exception as e:
    print(f'Error checking tables: {e}')
"

# Create superuser if not exists
echo "👤 Creating superuser (if not exists)..."
python3.9 manage.py shell -c "
from django.contrib.auth.models import User
from accounts.models import UserProfile
import os

username = os.environ.get('ADMIN_USERNAME', 'admin')
password = os.environ.get('ADMIN_PASSWORD', 'admin123')
email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')

if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(username, email, password)
    UserProfile.objects.create(user=user, role='admin')
    print(f'✅ Admin user created: {username}')
else:
    print(f'✅ Admin user already exists: {username}')
"

# Collect static files
echo "🎨 Collecting static files..."
python3.9 manage.py collectstatic --noinput --clear

# Create a test file to verify static files
echo "📝 Creating test static file..."
mkdir -p static/css
echo "/* Test CSS file */" > static/css/test.css

echo "✅ Build completed successfully!"