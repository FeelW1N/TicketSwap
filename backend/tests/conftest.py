"""Конфигурация pytest — тестовое Flask-приложение с SQLite в памяти и moto S3."""
import pytest
import boto3
from moto import mock_aws
from app import create_app
from app.extensions import db as _db
from app.config import Config

TEST_BUCKET = "test-ticketswap"


class TestConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    STRIPE_SECRET_KEY = "sk_test_dummy"
    STRIPE_WEBHOOK_SECRET = "whsec_dummy"
    # moto перехватывает boto3-вызовы — endpoint не нужен
    AWS_ACCESS_KEY_ID = "testing"
    AWS_SECRET_ACCESS_KEY = "testing"
    AWS_S3_BUCKET = TEST_BUCKET
    AWS_S3_REGION = "us-east-1"
    S3_ENDPOINT_URL = None          # moto работает без кастомного endpoint
    S3_PUBLIC_ENDPOINT_URL = None


@pytest.fixture(scope="session")
def app():
    flask_app = create_app(TestConfig)
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Регистрирует пользователя (или логинится если уже существует) и возвращает JWT."""
    creds = {"email": "test@example.com", "password": "password123", "full_name": "Test User"}
    resp = client.post("/auth/register", json=creds)
    if resp.status_code == 409:
        resp = client.post("/auth/login", json={"email": creds["email"], "password": creds["password"]})
    token = resp.json["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def s3_mock(app):
    """
    Фикстура moto: поднимает фейковый S3 в памяти на время теста.
    Создаёт бакет и сбрасывает кэш клиента StorageService после теста.
    """
    with mock_aws():
        # Создаём бакет в фейковом S3
        s3 = boto3.client(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        s3.create_bucket(Bucket=TEST_BUCKET)

        # Сбрасываем кэшированный клиент StorageService, чтобы он пересоздался внутри mock_aws
        from app.services.storage import storage_service
        storage_service._client = None
        storage_service._bucket_ensured = True  # бакет уже создан выше

        yield s3

        # Чистим после теста
        storage_service._client = None
        storage_service._bucket_ensured = False
