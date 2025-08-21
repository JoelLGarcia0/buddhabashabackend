#!/usr/bin/env python
"""
Debug script to check deployment configuration
Run this on your production server to identify issues
"""
import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.production')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

# Check environment variables
print("\n🔍 Environment Variables Check:")
env_vars = [
    'DJANGO_SECRET_KEY',
    'DB_NAME',
    'DB_USER', 
    'DB_PWD',
    'DB_HOST',
    'DB_PORT',
    'ALLOWED_HOSTS',
    'CLOUDINARY_URL',
    'STRIPE_SECRET_KEY',
    'SHIPPO_API_KEY',
    'CLERK_JWKS_URL'
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if 'KEY' in var or 'PWD' in var or 'SECRET' in var:
            display_value = f"{value[:8]}..." if len(value) > 8 else "***"
        else:
            display_value = value
        print(f"✅ {var}: {display_value}")
    else:
        print(f"❌ {var}: NOT SET")

# Check database connection
print("\n🗄️ Database Connection Test:")
try:
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    if result and result[0] == 1:
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
except Exception as e:
    print(f"❌ Database connection error: {e}")

# Check static files
print("\n📁 Static Files Check:")
static_root = os.path.join(backend_dir, 'staticfiles')
if os.path.exists(static_root):
    print(f"✅ Static files directory exists: {static_root}")
    print(f"   Files count: {len(os.listdir(static_root))}")
else:
    print(f"❌ Static files directory missing: {static_root}")

# Check imports
print("\n📦 Package Import Test:")
packages = [
    'django',
    'rest_framework',
    'corsheaders',
    'cloudinary',
    'whitenoise',
    'psycopg2',
    'stripe',
    'shippo'
]

for package in packages:
    try:
        __import__(package)
        print(f"✅ {package}: OK")
    except ImportError as e:
        print(f"❌ {package}: {e}")

print("\n🎯 Deployment Check Complete!")
print("If you see any ❌ errors above, those are likely causing your 500 errors.")
