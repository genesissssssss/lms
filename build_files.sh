#!/bin/bash

echo "=========================================="
echo "🚀 Starting Vercel build process"
echo "=========================================="

echo "📁 Current directory: $(pwd)"
echo "🐍 Python version: $(python --version)"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# CRITICAL: Make sure static directory exists
echo "📁 Checking static directory..."
mkdir -p static/css

# If you have a CSS file somewhere else, copy it to the right place
if [ -f "staticfiles/css/styles.css" ]; then
    echo "📋 Copying CSS file from staticfiles to static..."
    cp staticfiles/css/styles.css static/css/ 2>/dev/null || echo "No CSS file to copy"
fi

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run migrations
echo "=========================================="
echo "🗄️  Running database migrations..."
echo "=========================================="

python manage.py makemigrations accounts --noinput
python manage.py makemigrations core --noinput
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "=========================================="
echo "👤 Setting up admin user..."
echo "=========================================="

python manage.py shell <<EOF
from django.contrib.auth.models import User
from accounts.models import UserProfile

username = 'admin'
password = 'admin123'
email = 'admin@example.com'

print(f"Checking if admin user exists...")
if not User.objects.filter(username=username).exists():
    print(f"Creating admin user: {username}")
    user = User.objects.create_superuser(username, email, password)
    UserProfile.objects.create(user=user, role='admin')
    print("✅ Admin user created successfully")
else:
    print("✅ Admin user already exists")
EOF

echo "=========================================="
echo "✅ Build completed successfully!"
echo "=========================================="