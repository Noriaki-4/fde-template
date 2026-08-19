"""MCP server exposing read-only tools against the mock business API and
the shared Postgres database. Runs over the Streamable HTTP transport so
it can be reached as a regular network service by other containers.
"""

import os

import httpx
from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine, text

MOCK_API_URL = os.getenv("MOCK_API_URL", "http://mock-api:8100")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@postgresql:5432/fde_poc"
)

_engine = create_engine(DATABASE_URL)

mcp = FastMCP(
    name="fde-mcp-server",
    instructions="Tools for querying the mock business API and the shared document store.",
    host="0.0.0.0",
    port=8200,
)


@mcp.tool()
async def get_customer(customer_id: str) -> dict:
    """Look up a customer by ID from the mock business API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MOCK_API_URL}/customers/{customer_id}", timeout=10.0)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def list_orders(customer_id: str | None = None) -> list[dict]:
    """List orders from the mock business API, optionally filtered by customer_id."""
    async with httpx.AsyncClient() as client:
        params = {"customer_id": customer_id} if customer_id else {}
        response = await client.get(f"{MOCK_API_URL}/orders", params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()


@mcp.tool()
def search_documents(query: str, limit: int = 10) -> list[dict]:
    """Search the shared documents table by title/content substring match."""
    with _engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, title, content FROM documents "
                "WHERE title ILIKE :q OR content ILIKE :q LIMIT :limit"
            ),
            {"q": f"%{query}%", "limit": limit},
        )
        return [dict(row._mapping) for row in rows]


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
