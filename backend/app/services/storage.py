"""Сервис хранения файлов билетов.

Использует boto3 с поддержкой MinIO (self-hosted, бесплатно) и AWS S3.
MinIO — S3-совместимое хранилище, запускается локально через Docker.
Для подключения MinIO достаточно указать S3_ENDPOINT_URL=http://minio:9000.
"""
import uuid
import logging
import boto3
from botocore.exceptions import ClientError
from flask import current_app

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self._client = None
        self._bucket_ensured = False

    def _get_client(self):
        if self._client is None:
            kwargs = dict(
                region_name=current_app.config["AWS_S3_REGION"],
                aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
            )
            # MinIO / любой S3-совместимый сервис задаётся через S3_ENDPOINT_URL
            endpoint_url = current_app.config.get("S3_ENDPOINT_URL")
            if endpoint_url:
                kwargs["endpoint_url"] = endpoint_url
            self._client = boto3.client("s3", **kwargs)
        return self._client

    def _ensure_bucket(self) -> None:
        """Создаёт бакет при первом обращении, если он ещё не существует."""
        if self._bucket_ensured:
            return
        bucket = current_app.config["AWS_S3_BUCKET"]
        client = self._get_client()
        try:
            client.head_bucket(Bucket=bucket)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                client.create_bucket(Bucket=bucket)
                logger.info("Created storage bucket: %s", bucket)
            else:
                raise
        self._bucket_ensured = True

    def upload_ticket_file(self, file_data: bytes, filename: str, user_id: str) -> str:
        """Загружает файл билета, возвращает s3_key."""
        self._ensure_bucket()
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        s3_key = f"tickets/{user_id}/{uuid.uuid4()}.{ext}"
        bucket = current_app.config["AWS_S3_BUCKET"]

        content_type_map = {"pdf": "application/pdf", "png": "image/png",
                            "jpg": "image/jpeg", "jpeg": "image/jpeg"}
        content_type = content_type_map.get(ext, "application/octet-stream")

        self._get_client().put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=file_data,
            ContentType=content_type,
        )
        return s3_key

    def generate_presigned_url(self, s3_key: str) -> str:
        """Генерирует временную подписанную ссылку на скачивание файла.

        MinIO: если внутренний endpoint (minio:9000) отличается от внешнего
        (localhost:9000), подменяем хост через S3_PUBLIC_ENDPOINT_URL.
        """
        bucket = current_app.config["AWS_S3_BUCKET"]
        expiry = current_app.config["S3_PRESIGNED_URL_EXPIRY"]
        try:
            url = self._get_client().generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": s3_key},
                ExpiresIn=expiry,
            )
            # Заменяем внутренний хост на публичный (нужно при работе в Docker)
            public_endpoint = current_app.config.get("S3_PUBLIC_ENDPOINT_URL")
            internal_endpoint = current_app.config.get("S3_ENDPOINT_URL")
            if public_endpoint and internal_endpoint and url.startswith(internal_endpoint):
                url = url.replace(internal_endpoint, public_endpoint, 1)
            return url
        except ClientError as e:
            raise RuntimeError(f"Failed to generate presigned URL: {e}") from e

    def delete_object(self, s3_key: str) -> None:
        bucket = current_app.config["AWS_S3_BUCKET"]
        self._get_client().delete_object(Bucket=bucket, Key=s3_key)


storage_service = StorageService()
