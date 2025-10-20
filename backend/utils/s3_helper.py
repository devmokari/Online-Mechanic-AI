"""Utility helpers for interacting with Amazon S3."""
from __future__ import annotations

import base64
import binascii
import mimetypes
import os
import time
from dataclasses import dataclass

try:
    import boto3
except ImportError:  # pragma: no cover - handled at runtime
    boto3 = None  # type: ignore[assignment]


def _get_s3_client():
    """Return an S3 client, ensuring boto3 is available."""

    if boto3 is None:
        raise RuntimeError(
            "boto3 is required to upload media. Install it with 'pip3 install boto3'."
        )
    return boto3.client("s3")


@dataclass
class S3Object:
    """Represents an object stored in S3."""

    bucket: str
    key: str
    presigned_url: str


def _guess_content_type(filename: str) -> str:
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"


def upload_media_from_base64(bucket: str, base64_payload: str, filename: str) -> S3Object:
    """Upload a base64 encoded media payload to S3."""
    s3 = _get_s3_client()
    try:
        binary_data = base64.b64decode(base64_payload)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid base64 payload provided") from exc

    content_type = _guess_content_type(filename)
    timestamp = int(time.time())
    key = f"uploads/{timestamp}-{os.path.basename(filename)}"

    s3.put_object(Bucket=bucket, Key=key, Body=binary_data, ContentType=content_type)

    presigned_url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=3600
    )

    return S3Object(bucket=bucket, key=key, presigned_url=presigned_url)
