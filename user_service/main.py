from fastapi import FastAPI
from user_service.database import engine
from user_service.models import Base
from user_service.routers import user, admin, auth, business
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from user_service.initial_data import init_db_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Application startup: Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created or already exist.")

    # Seed initial data (Roles, Admin User)
    await init_db_data()

    # Yield control to the application
    yield

    # Shutdown logic (executed after the application stops receiving requests)
    print("Application shutdown: Disposing database engine...")
    await engine.dispose()
    print("Database engine disposed.")


app = FastAPI(root_path="/api/user-service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(admin.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(business.router)
