import os
from datetime import timedelta


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ticketswap"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Redis / Celery
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )

    # Legacy-переменные платёжного провайдера оставлены для совместимости конфигов.
    YOOKASSA_SHOP_ID = os.environ.get("YOOKASSA_SHOP_ID", "debug-shop-id")
    YOOKASSA_SECRET_KEY = os.environ.get("YOOKASSA_SECRET_KEY", "debug-secret-key")

    # S3-совместимое хранилище (MinIO локально или AWS S3 в проде)
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin")
    AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "ticketswap-tickets")
    AWS_S3_REGION = os.environ.get("AWS_S3_REGION", "us-east-1")
    S3_PRESIGNED_URL_EXPIRY = int(os.environ.get("S3_PRESIGNED_URL_EXPIRY", "3600"))
    # MinIO: внутренний URL (для backend/celery внутри Docker-сети)
    S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
    # MinIO: публичный URL (для presigned-ссылок, открываемых браузером)
    S3_PUBLIC_ENDPOINT_URL = os.environ.get(
        "S3_PUBLIC_ENDPOINT_URL", "http://localhost:9000"
    )

    # Email (SMTP). Если не задан SMTP_HOST — письма только в лог (dev-режим).
    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@ticketswap.ru")

    # Organizer API (mock)
    ORGANIZER_API_BASE_URL = os.environ.get(
        "ORGANIZER_API_BASE_URL", "http://localhost:8001"
    )
    ORGANIZER_API_KEY = os.environ.get("ORGANIZER_API_KEY", "mock-api-key")

    # Business rules
    MAX_RESALE_MARKUP_PERCENT = 20  # цена перепродажи не более +20% от исходной
    ALLOWED_FILE_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
    MAX_FILE_SIZE_MB = 10
