#!/bin/bash

echo "=========================================="
echo "🚀 Starting Vercel build process"
echo "=========================================="

pip install -r requirements.txt
python manage.py collectstatic --noinput
python vercel_build.py

echo "✅ Build complete!"