"""CLI helper for provisioning the project's S3 bucket."""
from __future__ import annotations

import argparse
import sys

import boto3
from botocore.exceptions import ClientError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an S3 bucket for storing diagnostic uploads."
    )
    parser.add_argument(
        "bucket",
        help="Name of the S3 bucket to create (must be globally unique).",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region for the bucket (defaults to us-east-1).",
    )
    parser.add_argument(
        "--acl",
        default="private",
        help="Canned ACL to apply to the new bucket (defaults to private).",
    )
    return parser.parse_args()


def bucket_exists(s3_client, bucket_name: str) -> bool:
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as exc:  # pragma: no cover - boto handles error codes
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchBucket", "NotFound"}:
            return False
        if error_code == "403":
            # Bucket exists but is owned by someone else.
            return True
        raise
    return True


def create_bucket(bucket_name: str, region: str, acl: str) -> None:
    session = boto3.session.Session()
    region = region or session.region_name or "us-east-1"
    s3_client = session.client("s3", region_name=region)

    if bucket_exists(s3_client, bucket_name):
        print(f"⚠️ Bucket '{bucket_name}' already exists. Skipping creation.")
        return

    create_kwargs = {"Bucket": bucket_name, "ACL": acl}
    if region != "us-east-1":
        create_kwargs["CreateBucketConfiguration"] = {
            "LocationConstraint": region
        }

    s3_client.create_bucket(**create_kwargs)
    print(f"✅ Created S3 bucket '{bucket_name}' in region '{region}'.")


def main() -> int:
    args = parse_args()
    try:
        create_bucket(bucket_name=args.bucket, region=args.region, acl=args.acl)
    except ClientError as exc:
        print(f"❌ Failed to create bucket: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
