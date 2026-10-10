import pytest

from backend.config import Settings
from backend.storage.object_store import S3ObjectStore, parse_s3_uri


def test_parse_s3_uri():
    assert parse_s3_uri("s3://bucket/a/b.json") == ("bucket", "a/b.json")


@pytest.mark.parametrize("uri", ["http://x/y", "s3://bucket", "s3:///key", "bucket/key"])
def test_parse_s3_uri_rejects(uri):
    with pytest.raises(ValueError):
        parse_s3_uri(uri)


def test_from_config_minio():
    store = S3ObjectStore.from_config(
        Settings(storage_engine="minio", minio_endpoint="minio:9000", minio_bucket="kb")
    )
    assert store.bucket == "kb"
    assert store._endpoint_url == "http://minio:9000"


def test_from_config_s3_uses_default_endpoint():
    store = S3ObjectStore.from_config(Settings(storage_engine="s3", minio_bucket="kb"))
    assert store._endpoint_url is None
    assert store._access_key is None


def test_from_config_unknown():
    with pytest.raises(ValueError):
        S3ObjectStore.from_config(Settings(storage_engine="gcs"))


def test_put_and_get_use_client():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def put_object(self, **kwargs):
            self.calls.append(kwargs)

        def get_object(self, Bucket, Key):
            import io

            return {"Body": io.BytesIO(b"data")}

    store = S3ObjectStore(bucket="kb")
    store._client = FakeClient()
    assert store.put_bytes("k/x", b"data") == "s3://kb/k/x"
    assert store.get_bytes("s3://kb/k/x") == b"data"
