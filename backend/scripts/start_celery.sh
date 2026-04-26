#!/bin/bash
# Celery Worker & Beat Starter Script
# ===================================
# Usage: ./start_celery.sh [worker|beat|both]

set -e

cd "$(dirname "$0")/.."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    if [ -f "../.venv/bin/activate" ]; then
        source ../.venv/bin/activate
    elif [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    fi
fi

# Set Django settings
export DJANGO_SETTINGS_MODULE=config.settings.development

case "${1:-both}" in
    worker)
        echo "🚀 Starting Celery Worker..."
        celery -A config worker -l info -n wellfond-worker@%h
        ;;
    beat)
        echo "⏰ Starting Celery Beat Scheduler..."
        celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;
    both)
        echo "🚀 Starting Celery Worker (background)..."
        celery -A config worker -l info -n wellfond-worker@%h --detach --logfile=logs/celery-worker.log --pidfile=celery-worker.pid

        echo "⏰ Starting Celery Beat Scheduler..."
        celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile=logs/celery-beat.log --pidfile=celery-beat.pid
        ;;
    stop)
        echo "🛑 Stopping Celery Workers..."
        if [ -f "celery-worker.pid" ]; then
            kill $(cat celery-worker.pid) 2>/dev/null || true
            rm -f celery-worker.pid
        fi
        if [ -f "celery-beat.pid" ]; then
            kill $(cat celery-beat.pid) 2>/dev/null || true
            rm -f celery-beat.pid
        fi
        pkill -f "celery -A config" 2>/dev/null || true
        echo "✅ Celery stopped"
        ;;
    status)
        echo "📊 Celery Status:"
        pgrep -f "celery -A config worker" > /dev/null && echo "  Worker: Running ✅" || echo "  Worker: Stopped ❌"
        pgrep -f "celery -A config beat" > /dev/null && echo "  Beat: Running ✅" || echo "  Beat: Stopped ❌"
        ;;
    *)
        echo "Usage: $0 [worker|beat|both|stop|status]"
        echo ""
        echo "Commands:"
        echo "  worker  - Start only the worker"
        echo "  beat    - Start only the scheduler"
        echo "  both    - Start both worker and scheduler (default)"
        echo "  stop    - Stop all Celery processes"
        echo "  status  - Check Celery status"
        exit 1
        ;;
esac
