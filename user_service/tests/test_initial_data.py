import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from user_service.initial_data import init_db_data
from user_service.models import User, Role, RoleAccess
from unittest.mock import patch
import os

@pytest.mark.asyncio
async def test_init_db_data_fresh_db(db_session: AsyncSession):
    # Ensure DB is empty first (conftest clears it, but good to be sure)
    roles = await db_session.execute(select(Role))
    assert len(roles.scalars().all()) == 0

    # We need to mock the session maker used inside init_db_data
    # because it uses its own AsyncSessionLocal, not the test session.
    # We patch it to return an async context manager that yields our test 'db_session'
    
    # Define a mock context manager
    class MockSessionContext:
        def __init__(self, session):
            self.session = session
        async def __aenter__(self):
            return self.session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Patch AsyncSessionLocal in initial_data.py
    with patch("user_service.initial_data.AsyncSessionLocal", side_effect=lambda: MockSessionContext(db_session)):
        await init_db_data()

    # Verify Roles
    result = await db_session.execute(select(Role).where(Role.name.in_(["admin", "user"])))
    roles = result.scalars().all()
    assert len(roles) == 2
    
    admin_role = next(r for r in roles if r.name == "admin")
    assert admin_role.can_read_all is True
    assert admin_role.can_write_all is True
    
    user_role = next(r for r in roles if r.name == "user")
    assert user_role.can_read_all is False

    # Verify User Role Permissions
    access_result = await db_session.execute(select(RoleAccess).where(RoleAccess.role_id == user_role.id))
    access_list = access_result.scalars().all()
    assert len(access_list) >= 1
    orders_access = next(a for a in access_list if a.resource == "orders")
    assert orders_access.can_read is True
    assert orders_access.can_write is True

    # Verify Admin User
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    user_result = await db_session.execute(select(User).where(User.email == admin_email))
    admin_user = user_result.scalar_one_or_none()
    
    assert admin_user is not None
    assert admin_user.role_id == admin_role.id
    assert admin_user.first_name == "Super"

@pytest.mark.asyncio
async def test_init_db_data_idempotency(db_session: AsyncSession):
    """Running init_db_data twice should not fail or create duplicates."""
    
    class MockSessionContext:
        def __init__(self, session):
            self.session = session
        async def __aenter__(self):
            return self.session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch("user_service.initial_data.AsyncSessionLocal", side_effect=lambda: MockSessionContext(db_session)):
        # Run 1
        await init_db_data()
        # Run 2
        await init_db_data()

    # Verify counts remain the same
    result = await db_session.execute(select(Role))
    assert len(result.scalars().all()) == 2
    
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    user_result = await db_session.execute(select(User).where(User.email == admin_email))
    assert len(user_result.scalars().all()) == 1
