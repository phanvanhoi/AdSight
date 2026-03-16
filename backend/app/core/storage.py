import asyncio
import functools

import boto3
from botocore.client import Config

from app.config import settings

_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if settings.minio_use_ssl else 'http'}://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
    return _s3_client


def _sync_ensure_bucket():
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.minio_bucket)
    except client.exceptions.ClientError:
        client.create_bucket(Bucket=settings.minio_bucket)


def _sync_upload_file(file_bytes: bytes, key: str, content_type: str) -> str:
    client = get_s3_client()
    client.put_object(
        Bucket=settings.minio_bucket,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return key


def _sync_get_file_url(key: str, expires_in: int) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def _sync_delete_file(key: str):
    client = get_s3_client()
    client.delete_object(Bucket=settings.minio_bucket, Key=key)


async def ensure_bucket():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_ensure_bucket)


async def upload_file(file_bytes: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(_sync_upload_file, file_bytes, key, content_type))


async def get_file_url(key: str, expires_in: int = 3600) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(_sync_get_file_url, key, expires_in))


async def delete_file(key: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, functools.partial(_sync_delete_file, key))
