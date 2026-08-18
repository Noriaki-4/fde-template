"""ScyllaDB Alternator (DynamoDB-compatible) Adapter"""

from typing import Any
import boto3
from botocore.exceptions import ClientError

from backend.database.nosql.base import NoSQLRepository


class ScyllaDBRepository(NoSQLRepository):
    """ScyllaDB Alternator (DynamoDB API-compatible) Implementation"""

    def __init__(self, endpoint_url: str, table_name: str, region: str = "local"):
        self.endpoint_url = endpoint_url
        self.table_name = table_name
        self.region = region
        self.dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id="dummy",
            aws_secret_access_key="dummy",
        )
        self.table = self.dynamodb.Table(table_name)

    async def put_item(self, key: str, item: dict[str, Any]) -> bool:
        """Insert or update item"""
        try:
            self.table.put_item(Item={"pk": key, **item})
            return True
        except ClientError as e:
            print(f"Error putting item: {e}")
            return False

    async def get_item(self, key: str) -> dict[str, Any] | None:
        """Retrieve item by key"""
        try:
            response = self.table.get_item(Key={"pk": key})
            item = response.get("Item")
            if item:
                item.pop("pk", None)
            return item
        except ClientError:
            return None

    async def query(
        self, index: str, condition: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Query items (Alternator compatibility mode)"""
        try:
            kwargs = {"KeyConditionExpression": "pk = :pk", "ExpressionAttributeValues": {":pk": index}}

            response = self.table.query(**kwargs)
            items = response.get("Items", [])
            for item in items:
                item.pop("pk", None)
            return items
        except ClientError:
            return []

    async def delete_item(self, key: str) -> bool:
        """Delete item"""
        try:
            self.table.delete_item(Key={"pk": key})
            return True
        except ClientError:
            return False

    async def batch_write(self, items: list[dict[str, Any]]) -> bool:
        """Batch write multiple items"""
        try:
            with self.table.batch_writer(batch_size=25) as batch:
                for item in items:
                    pk = item.pop("pk", None)
                    if pk:
                        batch.put_item(Item={"pk": pk, **item})
            return True
        except ClientError:
            return False

    async def health_check(self) -> bool:
        """Check ScyllaDB Alternator health"""
        try:
            self.table.table_status
            return True
        except Exception:
            return False
