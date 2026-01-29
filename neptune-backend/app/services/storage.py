from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Optional
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.settings import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StorageStatus:
    enabled: bool
    ok: bool
    error: Optional[str] = None


class StorageClient:
    def __init__(self) -> None:
        self.endpoint_url = self._resolve_endpoint(settings.s3_endpoint, settings.s3_secure)
        self.bucket = settings.s3_bucket
        self.enabled = bool(self.endpoint_url and settings.s3_access_key and settings.s3_secret_key and self.bucket)
        self.client = None

        if self.enabled:
            self.client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region or "us-east-1",
                config=Config(
                    connect_timeout=settings.s3_connect_timeout_seconds,
                    read_timeout=settings.s3_read_timeout_seconds,
                    retries={"max_attempts": settings.s3_max_retries},
                ),
            )
            logger.info("Storage client enabled for bucket %s", self.bucket)
        else:
            logger.info("Storage client disabled (missing S3 config)")

    def _resolve_endpoint(self, endpoint: Optional[str], secure: bool) -> Optional[str]:
        if not endpoint:
            return None
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        scheme = "https" if secure else "http"
        return f"{scheme}://{endpoint}"

    def healthcheck(self) -> StorageStatus:
        if not self.enabled or not self.client:
            return StorageStatus(enabled=False, ok=True)
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return StorageStatus(enabled=True, ok=True)
        except (ClientError, BotoCoreError) as e:
            return StorageStatus(enabled=True, ok=False, error=str(e))

    def put_object(self, key: str, data: bytes, content_type: str | None = None) -> None:
        if not self.enabled or not self.client:
            raise RuntimeError("Storage client not configured")
        extra_args = {"ContentType": content_type} if content_type else None
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, **(extra_args or {}))

    def get_object(self, key: str) -> bytes:
        if not self.enabled or not self.client:
            raise RuntimeError("Storage client not configured")
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()


storage_client = StorageClient()
