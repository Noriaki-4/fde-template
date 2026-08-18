"""NoSQL Database Module"""

from backend.database.nosql.base import NoSQLRepository
from backend.database.nosql.dynamodb import DynamoDBRepository
from backend.database.nosql.scylladb import ScyllaDBRepository

__all__ = ["NoSQLRepository", "DynamoDBRepository", "ScyllaDBRepository"]
