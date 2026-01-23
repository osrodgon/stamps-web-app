#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting project reset..."

# 1. DELETE SUPERUSER
echo "🗑️  Deleting superuser..."
python backend/manage.py stamps_delete_superuser admin

# 2. BACKUP DATABASE ADMIN DATA
echo "📦 Backing up admin data..."
python backend/manage.py dumpdata admin auth sessions contenttypes rest_framework_api_key --indent 4 > admin_backup.json

# 3. CLEAN DATABASE AND MIGRATE
echo "🗑️  Resetting database..."
python backend/manage.py reset_db --noinput

echo "🧹 Cleaning migrations..."
python backend/manage.py stamps_clean_migrations

echo "🏗️  Creating new migrations..."
python backend/manage.py makemigrations

echo "⚙️  Applying migrations..."
python backend/manage.py migrate

# 4. CREATE DJANGO SUPERUSER
echo "👤 Creating django superuser (interactive)..."
python backend/manage.py createsuperuser --username admin --email admin@example.com

# 5. CREATE STAMPS ADMIN USER
echo "👤 Creating stamps admin user (interactive)..."
python backend/manage.py stamps_create_admin_user

# 6. RESTORE DATABASE ADMIN DATA
echo "⏪ Restoring admin data..."
python backend/manage.py loaddata admin_backup.json
rm admin_backup.json

# 7. RESTORE DATABASE API DATA ONLY (with csv file)
echo "📥 Importing CSV data..."
python backend/manage.py stamps_import_csv

echo "✅ Project reset complete!"
