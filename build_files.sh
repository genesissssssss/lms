#!/bin/bash

echo "=========================================="
echo "🚀 Starting Vercel build process"
echo "=========================================="

echo "📁 Current directory: $(pwd)"
echo "🐍 Python version: $(python --version)"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Show static directory contents for debugging
echo "📁 Checking static directory..."
ls -la static/ || echo "Static directory not found"
ls -la static/css/ || echo "CSS directory not found"

# Collect static files (THIS IS CRITICAL)
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Show collected static files
echo "📁 Collected static files:"
ls -la staticfiles/ || echo "Staticfiles directory not found"
ls -la staticfiles/css/ || echo "CSS in staticfiles not found"

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

echo "✅ Build complete!"