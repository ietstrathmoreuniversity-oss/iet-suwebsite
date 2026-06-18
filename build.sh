#!/bin/bash
echo "Building Django application..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations (optional, use with caution)
# python manage.py migrate

echo "Build completed!"
