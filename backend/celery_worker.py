"""Точка входа для Celery-воркера.
Запуск: celery -A celery_worker.celery worker --loglevel=info
"""
from app import create_app

app = create_app()
celery = app.extensions["celery"]

# Регистрируем задачи
import app.tasks.reissue_tasks  # noqa: F401
