#!/usr/bin/env python
"""
Production setup script for Buddha Basha
Run this after deploying to set up the production environment
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Buddha Basha Production Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: Please run this script from the backend directory")
        sys.exit(1)
    
    # 1. Collect static files
    if not run_command("python manage.py collectstatic --noinput", "Collecting static files"):
        print("⚠️ Static files collection failed, but continuing...")
    
    # 2. Run migrations
    if not run_command("python manage.py migrate", "Running database migrations"):
        print("❌ Migrations failed - this is critical!")
        sys.exit(1)
    
    # 3. Create superuser if needed (optional)
    print("\n🤔 Do you want to create a superuser? (y/n): ", end="")
    response = input().lower().strip()
    if response in ['y', 'yes']:
        run_command("python manage.py createsuperuser", "Creating superuser")
    
    # 4. Check environment variables
    print("\n🔍 Environment Variables Status:")
    critical_vars = ['DJANGO_SECRET_KEY', 'ALLOWED_HOSTS']
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            if 'SECRET' in var or 'KEY' in var:
                print(f"✅ {var}: {value[:8]}...")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET - This will cause 500 errors!")
    
    # 5. Test Django setup
    print("\n🧪 Testing Django Production Setup...")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.production')
        import django
        django.setup()
        print("✅ Django production setup successful!")
    except Exception as e:
        print(f"❌ Django production setup failed: {e}")
        sys.exit(1)
    
    print("\n🎉 Production setup completed!")
    print("\n📋 Next steps:")
    print("1. Ensure DJANGO_SECRET_KEY is set in your environment")
    print("2. Set ALLOWED_HOSTS to your actual domain(s)")
    print("3. Restart your application server")
    print("4. Test your endpoints")

if __name__ == "__main__":
    main()
