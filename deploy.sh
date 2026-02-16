#!/bin/bash

echo "🚀 Deploying LMS to Vercel..."

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Run tests
echo "🧪 Running tests..."
python manage.py test

if [ $? -eq 0 ]; then
    echo "✅ Tests passed!"
    
    # Collect static files
    echo "📁 Collecting static files..."
    python manage.py collectstatic --noinput
    
    # Deploy to Vercel
    echo "☁️ Deploying to Vercel..."
    vercel --prod
    
    echo "✅ Deployment complete!"
else
    echo "❌ Tests failed. Aborting deployment."
    exit 1
fi