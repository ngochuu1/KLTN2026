from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import BinaryIO

import boto3
from botocore.client import BaseClient
from botocore.config import Config

from app.core.config import get_settings


class StorageService:
    """Minimal S3-compatible boundary used by chat business logic."""

    def __init__(self, client: BaseClient, bucket: str) -> None:
        self.client = client
        self.bucket = bucket

    async def check_bucket(self) -> None:
        await asyncio.to_thread(self.client.head_bucket, Bucket=self.bucket)

    async def upload(self, key: str, body: BinaryIO, content_type: str) -> None:
        body.seek(0)
        await asyncio.to_thread(
            self.client.upload_fileobj, body, self.bucket, key,
            ExtraArgs={"ContentType": content_type},
        )

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self.client.delete_object, Bucket=self.bucket, Key=key)

    async def temporary_download_url(self, key: str, filename: str) -> str:
        safe_filename = filename.replace('"', "")
        disposition = f'attachment; filename="{safe_filename}"'
        return await asyncio.to_thread(
            self.client.generate_presigned_url,
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ResponseContentDisposition": disposition,
            },
            ExpiresIn=300,
        )


@lru_cache
def get_storage_service() -> StorageService:
    settings = get_settings()
    if not all((
        settings.object_storage_endpoint.strip(),
        settings.object_storage_access_key.get_secret_value(),
        settings.object_storage_secret_key.get_secret_value(),
        settings.object_storage_bucket.strip(),
    )):
        raise RuntimeError("Object storage environment variables are required")
    endpoint = settings.object_storage_endpoint.rstrip("/")
    if settings.object_storage_secure and endpoint.startswith("http://"):
        endpoint = "https://" + endpoint.removeprefix("http://")
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.object_storage_access_key.get_secret_value(),
        aws_secret_access_key=settings.object_storage_secret_key.get_secret_value(),
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    return StorageService(client, settings.object_storage_bucket)
