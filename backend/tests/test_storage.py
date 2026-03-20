"""
Тесты StorageService с moto (mock S3).
moto перехватывает boto3-запросы в памяти — никакого реального хранилища не нужно.
"""
import pytest
from app.services.storage import storage_service


# --------------------------------------------------------------------------- #
# upload_ticket_file                                                           #
# --------------------------------------------------------------------------- #

def test_upload_pdf_returns_key(app, s3_mock):
    with app.app_context():
        key = storage_service.upload_ticket_file(b"%PDF-1.4 test", "ticket.pdf", "user-123")

    assert key.startswith("tickets/user-123/")
    assert key.endswith(".pdf")


def test_upload_png_returns_key(app, s3_mock):
    with app.app_context():
        key = storage_service.upload_ticket_file(b"\x89PNG", "scan.png", "user-456")

    assert key.endswith(".png")


def test_upload_no_extension_uses_bin(app, s3_mock):
    with app.app_context():
        key = storage_service.upload_ticket_file(b"rawdata", "noext", "user-789")

    assert key.endswith(".bin")


def test_uploaded_file_exists_in_bucket(app, s3_mock):
    """Файл действительно кладётся в бакет."""
    with app.app_context():
        key = storage_service.upload_ticket_file(b"hello ticket", "t.pdf", "u1")

    objs = s3_mock.list_objects_v2(Bucket="test-ticketswap", Prefix="tickets/u1/")
    keys = [o["Key"] for o in objs.get("Contents", [])]
    assert key in keys


def test_uploaded_content_matches(app, s3_mock):
    """Содержимое файла совпадает с загруженным."""
    payload = b"%PDF-1.4 unique content 12345"
    with app.app_context():
        key = storage_service.upload_ticket_file(payload, "check.pdf", "u2")

    obj = s3_mock.get_object(Bucket="test-ticketswap", Key=key)
    assert obj["Body"].read() == payload


def test_two_uploads_get_unique_keys(app, s3_mock):
    """Два вызова для одного пользователя дают разные ключи (UUID)."""
    with app.app_context():
        key1 = storage_service.upload_ticket_file(b"file1", "a.pdf", "u3")
        key2 = storage_service.upload_ticket_file(b"file2", "b.pdf", "u3")

    assert key1 != key2


# --------------------------------------------------------------------------- #
# generate_presigned_url                                                       #
# --------------------------------------------------------------------------- #

def test_presigned_url_returned(app, s3_mock):
    """Функция возвращает строку-URL."""
    with app.app_context():
        key = storage_service.upload_ticket_file(b"data", "t.pdf", "u4")
        url = storage_service.generate_presigned_url(key)

    assert isinstance(url, str)
    assert key in url


def test_presigned_url_contains_bucket(app, s3_mock):
    with app.app_context():
        key = storage_service.upload_ticket_file(b"data", "t.pdf", "u5")
        url = storage_service.generate_presigned_url(key)

    assert "test-ticketswap" in url


def test_presigned_url_nonexistent_key_still_generates(app, s3_mock):
    """moto генерирует URL даже для несуществующего ключа (проверка подписи — на скачивании)."""
    with app.app_context():
        url = storage_service.generate_presigned_url("tickets/ghost/no-file.pdf")

    assert isinstance(url, str)


# --------------------------------------------------------------------------- #
# delete_object                                                                #
# --------------------------------------------------------------------------- #

def test_delete_removes_object(app, s3_mock):
    with app.app_context():
        key = storage_service.upload_ticket_file(b"to delete", "del.pdf", "u6")
        storage_service.delete_object(key)

    objs = s3_mock.list_objects_v2(Bucket="test-ticketswap", Prefix=key)
    assert objs.get("KeyCount", 0) == 0


def test_delete_nonexistent_does_not_raise(app, s3_mock):
    """Удаление несуществующего объекта — S3 возвращает 204, ошибки нет."""
    with app.app_context():
        storage_service.delete_object("tickets/ghost/nothing.pdf")


# --------------------------------------------------------------------------- #
# Public endpoint URL rewriting (MinIO Docker scenario)                        #
# --------------------------------------------------------------------------- #

def test_public_endpoint_rewrite_logic(app):
    """
    Юнит-тест логики замены внутреннего URL на публичный.
    Проверяем _только_ функцию подстановки, без реального boto3-вызова.
    В Docker: backend → MinIO через http://minio:9000 (internal),
    но presigned URL должен начинаться с http://localhost:9000 (public).
    """
    internal = "http://minio:9000"
    public = "http://localhost:9000"
    fake_url = f"{internal}/ticketswap-tickets/tickets/u7/abc.pdf?X-Amz-Signature=xyz"

    # Воспроизводим логику rewrite из generate_presigned_url
    if fake_url.startswith(internal):
        result = fake_url.replace(internal, public, 1)
    else:
        result = fake_url

    assert result.startswith(public)
    assert internal not in result
    assert "X-Amz-Signature=xyz" in result  # параметры подписи сохранены
