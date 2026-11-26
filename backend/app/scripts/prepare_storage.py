"""
Create the storage bucket if it is missing (first deploy). Outside development the app
never creates buckets on its own, so this runs once per deploy before the API starts.

Usage: python -m app.scripts.prepare_storage
"""

from __future__ import annotations

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings


def main() -> None:
    client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}),
    )
    try:
        client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        print("Storage bucket ready.")
    except ClientError:
        client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
        print("Storage bucket created.")


if __name__ == "__main__":
    main()
