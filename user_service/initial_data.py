import asyncio
import os
from sqlalchemy import select
from user_service.database import AsyncSessionLocal
from user_service.models import User, Role, RoleAccess
from user_service.security import hash_password

async def init_db_data():
    """
    Creates initial roles and a default admin user if they don't exist.
    """
    async with AsyncSessionLocal() as db:
        try:
            # 1. Create Roles
            # Admin Role
            result = await db.execute(select(Role).where(Role.name == "admin"))
            admin_role = result.scalar_one_or_none()
            
            if not admin_role:
                print("Seeding: Creating 'admin' role...")
                admin_role = Role(
                    name="admin",
                    can_read_all=True,
                    can_write_all=True
                )
                db.add(admin_role)
            
            # User Role
            result = await db.execute(select(Role).where(Role.name == "user"))
            user_role = result.scalar_one_or_none()
            
            if not user_role:
                print("Seeding: Creating 'user' role...")
                user_role = Role(
                    name="user",
                    can_read_all=False,
                    can_write_all=False
                )
                db.add(user_role)
                await db.flush() # flush to get ID
                
                # Give user basic access to 'orders'
                user_orders_access = RoleAccess(
                    role_id=user_role.id,
                    resource="orders",
                    can_read=True,
                    can_write=True,
                    can_delete=False
                )
                db.add(user_orders_access)

            await db.commit()

            # 2. Create Admin User
            admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
            result = await db.execute(select(User).where(User.email == admin_email))
            existing_admin = result.scalar_one_or_none()
            
            new_password_hash = hash_password(os.getenv("ADMIN_PASSWORD", "admin123"))

            if not existing_admin:
                print(f"Seeding: Creating admin user '{admin_email}'...")
                admin_user = User(
                    email=admin_email,
                    hashed_password=new_password_hash,
                    first_name="Super",
                    last_name="Admin",
                    role_id=admin_role.id,
                    is_active=True
                )
                db.add(admin_user)
                await db.commit()
                print("Seeding: Admin user created.")
            else:
                # Force update password to ensure we can login
                print("Seeding: Admin user exists. Updating password...")
                existing_admin.hashed_password = new_password_hash
                existing_admin.role_id = admin_role.id # Ensure role is correct
                db.add(existing_admin)
                await db.commit()
                print("Seeding: Admin password updated.")
                
        except Exception as e:
            print(f"Seeding Error: {e}")
            await db.rollback()
