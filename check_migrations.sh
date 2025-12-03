#!/bin/bash
# Check migration status between local and database

echo "🔍 Checking migration status..."
echo ""

cd /home/mg/Deploy/az_sunshine/backend
source /home/mg/Deploy/az_sunshine/venv/bin/activate

echo "📋 Local migration files:"
ls -1 transparency/migrations/*.py | grep -v __pycache__ | tail -5
echo ""

echo "🗄️  Applied migrations in database:"
python manage.py showmigrations transparency --plan | tail -10
echo ""

echo "⚠️  Unapplied migrations:"
python manage.py showmigrations transparency | grep "\[ \]" || echo "✅ All migrations applied"
echo ""

echo "📊 Migration status:"
python manage.py migrate --plan | tail -20
