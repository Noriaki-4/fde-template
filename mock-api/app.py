"""Mock Business API — simulates a fictional client's business system
(customers/orders) for local PoC development before real API access exists.
In-memory data only; not backed by a database.
"""

from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Mock Business API",
    description="Fake ERP/CRM-style business system for FDE PoC development",
    version="0.1.0",
)

_CUSTOMERS = {
    "cust-001": {"id": "cust-001", "name": "Acme Corp", "email": "contact@acme.example", "tier": "enterprise"},
    "cust-002": {"id": "cust-002", "name": "Globex Inc", "email": "info@globex.example", "tier": "standard"},
    "cust-003": {"id": "cust-003", "name": "Initech LLC", "email": "sales@initech.example", "tier": "standard"},
}

_ORDERS = [
    {"id": "ord-1001", "customer_id": "cust-001", "item": "Widget A", "quantity": 50, "status": "shipped"},
    {"id": "ord-1002", "customer_id": "cust-001", "item": "Widget B", "quantity": 10, "status": "pending"},
    {"id": "ord-1003", "customer_id": "cust-002", "item": "Gadget X", "quantity": 5, "status": "delivered"},
    {"id": "ord-1004", "customer_id": "cust-003", "item": "Widget A", "quantity": 100, "status": "pending"},
]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/customers")
async def list_customers() -> list[dict]:
    return list(_CUSTOMERS.values())


@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str) -> dict:
    customer = _CUSTOMERS.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.get("/orders")
async def list_orders(customer_id: str | None = None) -> list[dict]:
    if customer_id:
        return [o for o in _ORDERS if o["customer_id"] == customer_id]
    return _ORDERS
