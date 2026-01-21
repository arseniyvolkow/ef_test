from fastapi import APIRouter, Depends
from typing import List, Dict
from common.security import CheckAccess

router = APIRouter(prefix="/business", tags=["Mock Business Logic"])

# Mock Database
FAKE_ORDERS = [
    {"id": 1, "item": "Laptop", "price": 1200, "owner": "user_1"},
    {"id": 2, "item": "Mouse", "price": 25, "owner": "user_2"},
    {"id": 3, "item": "Keyboard", "price": 100, "owner": "user_1"},
]

@router.get("/orders", dependencies=[Depends(CheckAccess("orders", "read"))])
async def get_orders() -> List[Dict]:
    """
    Returns a list of orders.
    Requires 'read' permission on 'orders' resource.
    """
    return FAKE_ORDERS

@router.post("/orders", dependencies=[Depends(CheckAccess("orders", "write"))])
async def create_order(order: Dict) -> Dict:
    """
    Creates a new order.
    Requires 'write' permission on 'orders' resource.
    """
    return {"msg": "Order created", "order": order}

@router.delete("/orders/{order_id}", dependencies=[Depends(CheckAccess("orders", "delete"))])
async def delete_order(order_id: int) -> Dict:
    """
    Deletes an order.
    Requires 'delete' permission on 'orders' resource.
    """
    return {"msg": f"Order {order_id} deleted"}
