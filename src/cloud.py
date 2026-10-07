"""Object-storage adapter: GCP by default, AWS when CLOUD_PROVIDER=aws."""
import os
from pathlib import Path


def _object(key):
    provider = os.getenv("CLOUD_PROVIDER", "gcp")
    bucket = os.environ["ARTIFACT_BUCKET"]
    if provider == "aws":
        import boto3
        return provider, boto3.client("s3"), bucket
    if provider == "gcp":
        from google.cloud import storage
        return provider, storage.Client().bucket(bucket).blob(key), bucket
    raise ValueError(f"Unsupported CLOUD_PROVIDER: {provider}")


def exists(key):
    provider, obj, bucket = _object(key)
    if provider == "gcp":
        return obj.exists()
    from botocore.exceptions import ClientError
    try:
        obj.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
            return False
        raise


def download(key, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    provider, obj, bucket = _object(key)
    if provider == "gcp":
        obj.download_to_filename(str(path))
    else:
        obj.download_file(bucket, key, str(path))


def upload(path, key):
    provider, obj, bucket = _object(key)
    if provider == "gcp":
        obj.upload_from_filename(str(path))
    else:
        obj.upload_file(str(path), bucket, key)


def delete(key):
    provider, obj, bucket = _object(key)
    if provider == "gcp":
        obj.delete()
    else:
        obj.delete_object(Bucket=bucket, Key=key)
