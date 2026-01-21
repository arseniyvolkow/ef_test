import pytest
from httpx import AsyncClient
from fastapi import status
from user_service.main import app
from common.security import get_token_payload

@pytest.mark.asyncio
async def test_get_orders_success(client: AsyncClient):
    # User has 'read' permission on 'orders'
    payload = {
        "sub": "user_id",
        "email": "test@example.com",
        "role": "user",
        "g_perms": {"r_all": False},
        "access": {"orders": {"r": True}}
    }
    
    app.dependency_overrides[get_token_payload] = lambda: payload
    
    response = await client.get(
        "/business/orders", 
        headers={"Authorization": "Bearer fake_token"}
    )
        
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["item"] == "Laptop"
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_orders_forbidden(client: AsyncClient):
    # User explicitly has NO read permission on 'orders'
    payload = {
        "sub": "user_id",
        "email": "test@example.com",
        "role": "guest",
        "g_perms": {},
        "access": {"orders": {"r": False}}
    }
    
    app.dependency_overrides[get_token_payload] = lambda: payload
    
    response = await client.get(
        "/business/orders", 
        headers={"Authorization": "Bearer fake_token"}
    )
        
    assert response.status_code == status.HTTP_403_FORBIDDEN
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_orders_missing_resource_access(client: AsyncClient):
    # User has no entry for 'orders' in access list
    payload = {
        "sub": "user_id",
        "email": "test@example.com",
        "access": {} # Empty access
    }
    
    app.dependency_overrides[get_token_payload] = lambda: payload
    
    response = await client.get(
        "/business/orders", 
        headers={"Authorization": "Bearer fake_token"}
    )
        
    assert response.status_code == status.HTTP_403_FORBIDDEN
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_order_success(client: AsyncClient):
    # User has 'write' permission
    payload = {
        "sub": "user_id", 
        "access": {"orders": {"w": True}}
    }
    
    app.dependency_overrides[get_token_payload] = lambda: payload
    
    new_order = {"item": "Phone", "price": 800}
    
    response = await client.post(
        "/business/orders",
        json=new_order,
        headers={"Authorization": "Bearer fake_token"}
    )
        
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["order"]["item"] == "Phone"
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_order_forbidden(client: AsyncClient):
    # User has 'read' but not 'write'
    payload = {
        "sub": "user_id", 
        "access": {"orders": {"r": True, "w": False}}
    }
    
    app.dependency_overrides[get_token_payload] = lambda: payload
    
    response = await client.post(
        "/business/orders",
        json={"item": "Phone"},
        headers={"Authorization": "Bearer fake_token"}
    )
        
    assert response.status_code == status.HTTP_403_FORBIDDEN
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_admin_global_access(client: AsyncClient):
    # Admin with w_all=True should be able to delete orders even without specific resource entry
    payload = {
        "sub": "admin_id",
        "g_perms": {"w_all": True}, # Global Write/Admin
        "access": {} 
    }
    
    app.dependency_overrides[get_token_payload] = lambda: payload
    
    response = await client.delete(
        "/business/orders/1",
        headers={"Authorization": "Bearer fake_token"}
    )
        
    assert response.status_code == status.HTTP_200_OK
    assert "deleted" in response.json()["msg"]
    app.dependency_overrides.clear()
