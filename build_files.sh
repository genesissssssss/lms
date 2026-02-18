#!/bin/bash

echo "=========================================="
echo "🚀 Starting Vercel build process"
echo "=========================================="

echo "📁 Current directory: $(pwd)"
echo "🐍 Python version: $(python --version)"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Collect static files (THIS IS CRITICAL)
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

echo "✅ Build complete!"