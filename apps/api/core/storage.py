import logging
from typing import Any

import aioboto3
from apps.api.core.config import settings
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger("api.storage")

UPLOAD_URL_TTL_SECONDS = 600
DOWNLOAD_URL_TTL_SECONDS = 300


class ImmutableObjectConflictError(RuntimeError):
    """Raised when an immutable key already contains different bytes."""


class StorageIntegrityError(RuntimeError):
    """Raised when object metadata does not match the expected content."""


class StorageService:
    def __init__(self) -> None:
        self.session = aioboto3.Session()
        self.endpoint_url = settings.storage_endpoint
        self.aws_access_key_id = settings.storage_access_key
        self.aws_secret_access_key = settings.storage_secret_key
        self.bucket_name = settings.storage_bucket
        self.config = Config(signature_version="s3v4")

    def _client(self):
        return self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            config=self.config,
        )

    async def create_bucket_if_not_exists(self) -> None:
        async with self._client() as s3:
            try:
                await s3.head_bucket(Bucket=self.bucket_name)
            except ClientError as exc:
                code = str(exc.response.get("Error", {}).get("Code", ""))
                if code not in {"404", "NoSuchBucket", "NotFound"}:
                    raise
                await s3.create_bucket(Bucket=self.bucket_name)

    async def generate_presigned_upload_url(
        self,
        object_key: str,
        mime_type: str,
        expires_in: int = UPLOAD_URL_TTL_SECONDS,
    ) -> str:
        async with self._client() as s3:
            return await s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_key,
                    "ContentType": mime_type,
                },
                ExpiresIn=min(expires_in, UPLOAD_URL_TTL_SECONDS),
            )

    async def generate_presigned_download_url(
        self,
        object_key: str,
        expires_in: int = DOWNLOAD_URL_TTL_SECONDS,
    ) -> str:
        async with self._client() as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=min(expires_in, DOWNLOAD_URL_TTL_SECONDS),
            )

    @staticmethod
    def _is_not_found(exc: ClientError) -> bool:
        return str(exc.response.get("Error", {}).get("Code", "")) in {
            "404",
            "NoSuchKey",
            "NotFound",
        }

    async def get_object_metadata(self, object_key: str) -> dict[str, Any] | None:
        async with self._client() as s3:
            try:
                response = await s3.head_object(Bucket=self.bucket_name, Key=object_key)
            except ClientError as exc:
                if self._is_not_found(exc):
                    return None
                raise
        return {
            "size": response.get("ContentLength", 0),
            "content_type": response.get("ContentType", ""),
            "etag": str(response.get("ETag", "")).strip('"'),
            "metadata": response.get("Metadata", {}),
        }

    async def get_object_bytes(
        self, object_key: str, max_bytes: int | None = None
    ) -> bytes | None:
        async with self._client() as s3:
            try:
                response = await s3.get_object(Bucket=self.bucket_name, Key=object_key)
            except ClientError as exc:
                if self._is_not_found(exc):
                    return None
                raise
            stream = response["Body"]
            if max_bytes is not None:
                return await stream.read(max_bytes)
            return await stream.read()

    async def promote_quarantine_object(
        self,
        quarantine_key: str,
        immutable_key: str,
        *,
        validated_body: bytes,
        sha256: str,
        mime_type: str,
        size_bytes: int,
    ) -> bool:
        """Copy validated bytes to a content-addressed key without replacement.

        Returns ``False`` for an idempotent retry when the destination already
        has the same hash and size. A conflicting destination is never replaced.
        """
        existing = await self.get_object_metadata(immutable_key)
        if existing is not None:
            metadata = existing.get("metadata", {})
            if existing.get("size") == size_bytes and metadata.get("sha256") == sha256:
                return False
            raise ImmutableObjectConflictError(
                f"Immutable object key already exists with different content: {immutable_key}"
            )

        import hashlib

        if (
            len(validated_body) != size_bytes
            or hashlib.sha256(validated_body).hexdigest() != sha256
        ):
            raise StorageIntegrityError(
                "Validated quarantine bytes do not match the expected hash and size"
            )

        await self.put_immutable_bytes(
            immutable_key,
            validated_body,
            sha256=sha256,
            mime_type=mime_type,
        )

        promoted = await self.get_object_metadata(immutable_key)
        if (
            promoted is None
            or promoted.get("size") != size_bytes
            or promoted.get("metadata", {}).get("sha256") != sha256
        ):
            raise StorageIntegrityError("Immutable object verification failed")
        return True

    async def put_immutable_bytes(
        self,
        object_key: str,
        body: bytes,
        *,
        sha256: str,
        mime_type: str,
    ) -> bool:
        existing = await self.get_object_metadata(object_key)
        if existing is not None:
            if (
                existing.get("size") == len(body)
                and existing.get("metadata", {}).get("sha256") == sha256
            ):
                return False
            raise ImmutableObjectConflictError(
                f"Immutable object key already exists with different content: {object_key}"
            )

        async with self._client() as s3:
            await s3.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=body,
                ContentType=mime_type,
                Metadata={"sha256": sha256, "immutable": "true"},
            )
        return True

    async def delete_quarantine_object(self, object_key: str) -> None:
        if not object_key.startswith("quarantine/"):
            raise ValueError("Only quarantine objects may be deleted by this method")
        async with self._client() as s3:
            await s3.delete_object(Bucket=self.bucket_name, Key=object_key)


storage_service = StorageService()
