#!/bin/bash
# =============================================================================
# Wellfond BMS - Database Seeding Script
# =============================================================================
# Seeds initial data for development:
# - Holdings entity (parent)
# - Katong entity (AVS-licensed)
# - Thomson entity (AVS-licensed)
# - Admin user
# =============================================================================

set -e

echo "========================================"
echo "Wellfond BMS - Database Seeding"
echo "========================================"

# Check if running from project root
if [ ! -f "backend/manage.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

cd backend

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Run migrations
echo "🗄️ Running migrations..."
python manage.py migrate

# Create superuser from environment variables if provided
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "👤 Creating superuser from environment variables..."
    python manage.py createsuperuser --noinput \
        --email "$DJANGO_SUPERUSER_EMAIL" \
        --first_name "${DJANGO_SUPERUSER_FIRST_NAME:-Admin}" \
        --last_name "${DJANGO_SUPERUSER_LAST_NAME:-User}" \
        2>/dev/null || echo "Superuser already exists"
else
    echo "⚠️  Environment variables not set. Manual superuser creation required."
    echo "   Run: python manage.py createsuperuser"
fi

# Load entity fixtures if they exist
if [ -d "apps/core/fixtures" ]; then
    echo "🏢 Loading entity fixtures..."
    for fixture in apps/core/fixtures/*.json; do
        if [ -f "$fixture" ]; then
            echo "   Loading: $(basename $fixture)"
            python manage.py loaddata "$fixture" || echo "   ⚠️ Failed to load $(basename $fixture)"
        fi
    done
fi

echo ""
echo "========================================"
echo "✅ Seeding complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Start Django: python manage.py runserver"
echo "  2. Start Next.js: cd ../frontend && npm run dev"
echo "  3. Start Celery: celery -A config worker -l info"
echo ""
