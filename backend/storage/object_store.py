"""S3-API object storage (MinIO locally, S3 on AWS) — same code, endpoint differs."""

from abc import ABC, abstractmethod
from urllib.parse import urlparse

from backend.config import Settings


class ObjectStore(ABC):
    @abstractmethod
    def put_bytes(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        """Store data under key and return its s3:// URI."""

    @abstractmethod
    def get_bytes(self, uri: str) -> bytes:
        """Read data from an s3:// URI."""


def parse_s3_uri(uri: str) -> tuple[str, str]:
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc or not parsed.path.lstrip("/"):
        raise ValueError(f"Not an s3:// object URI: {uri}")
    return parsed.netloc, parsed.path.lstrip("/")


class S3ObjectStore(ObjectStore):
    """boto3 S3 client. The client is created lazily so jobs that never touch
    storage can run without MinIO / AWS credentials."""

    def __init__(
        self,
        bucket: str,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str | None = None,
    ):
        self.bucket = bucket
        self._endpoint_url = endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key
        self._region = region
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client(
                "s3",
                endpoint_url=self._endpoint_url,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                region_name=self._region,
            )
        return self._client

    def put_bytes(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return f"s3://{self.bucket}/{key}"

    def get_bytes(self, uri: str) -> bytes:
        bucket, key = parse_s3_uri(uri)
        return self.client.get_object(Bucket=bucket, Key=key)["Body"].read()

    @classmethod
    def from_config(cls, config: Settings) -> "S3ObjectStore":
        if config.storage_engine == "s3":
            # AWS: default endpoint, credentials from the task role
            return cls(bucket=config.minio_bucket, region=config.aws_region)
        if config.storage_engine == "minio":
            scheme = "https" if config.minio_use_ssl else "http"
            return cls(
                bucket=config.minio_bucket,
                endpoint_url=f"{scheme}://{config.minio_endpoint}",
                access_key=config.minio_access_key,
                secret_key=config.minio_secret_key,
                region="us-east-1",
            )
        raise ValueError(f"Unknown storage_engine: {config.storage_engine}")
