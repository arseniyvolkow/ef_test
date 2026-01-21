# Auth & Authorization System (RBAC)

## Overview
This project implements a custom authentication and authorization system using FastAPI, PostgreSQL, and Redis. It is designed to demonstrate a robust Role-Based Access Control (RBAC) architecture without relying on framework-specific "magic".

## Architecture

### 1. Authentication
*   **Mechanism:** JWT (JSON Web Tokens).
*   **Flow:**
    *   User logs in with Email/Password.
    *   Server validates credentials (bcrypt) and issues an `Access Token` (short-lived) and `Refresh Token` (long-lived).
    *   Tokens are signed with `HS256` and a secret key.
*   **Logout:** Implemented via **Token Blacklisting**. When a user logs out, the JTI (unique token ID) is stored in Redis until it expires. Any subsequent request with this token is rejected.

### 2. Authorization (RBAC)
The system uses a flexible 3-tier structure:

1.  **Users:** Standard accounts with profile data.
2.  **Roles:** Groupings of permissions (e.g., `admin`, `manager`, `guest`). A user has exactly one role.
3.  **Role Access Rules:** Granular permissions linking a **Role** to a **Resource**.

#### Database Schema
*   **`users`**: Stores login credentials (`hashed_password`) and links to `roles.id`.
*   **`roles`**:
    *   `can_read_all` (bool): Global read access.
    *   `can_write_all` (bool): Global write/admin access.
*   **`role_access`**:
    *   `role_id`: Link to the role.
    *   `resource`: String identifier (e.g., "orders", "users").
    *   `can_read` (bool)
    *   `can_write` (bool)
    *   `can_delete` (bool)

### 3. Usage & Access Control
Permissions are enforced using a custom dependency `CheckAccess`.

> **Note:** The `CheckAccess` dependency is located in the `common/` directory. This architectural choice allows the same authorization logic to be reused across multiple microservices as the system grows.

**Example:**
```python
@router.get("/orders", dependencies=[Depends(CheckAccess("orders", "read"))])
```
*   The system checks the User's Role.
*   It checks if the Role has `can_read_all=True`.
*   If not, it looks for a record in `role_access` where `resource="orders"` and checks the `can_read` flag.
*   Returns `403 Forbidden` if checks fail.

## API Endpoints

### Authentication
*   `POST /auth/register`: Create account.
*   `POST /auth/token`: Login (Get Tokens).
*   `POST /auth/refresh`: Refresh Access Token.
*   `POST /auth/logout`: Revoke Token.

### User
*   `GET /user/me`: Profile.
*   `PUT /user/me`: Update Profile.
*   `DELETE /user/me`: Soft Delete (Deactivate).

### Admin (RBAC Management)
*   `GET /admin/roles`: List roles.
*   `POST /admin/roles`: Create role.
*   `POST /admin/roles/{role}/permissions`: Assign resource permissions (e.g., give "manager" write access to "orders").

### Mock Business Logic
*   `GET /business/orders`: Protected resource (Requires "orders" -> read).

## Tech Stack
*   **Language:** Python 3.11+
*   **Framework:** FastAPI
*   **Database:** PostgreSQL (Async SQLAlchemy)
*   **Cache:** Redis (for Blacklist)
*   **Containerization:** Docker & Docker Compose

## Getting Started

### Default Admin Credentials
For testing purposes, the system automatically seeds a superuser on startup:
*   **Email:** `admin@example.com`
*   **Password:** `admin123`

### Running the Project
1.  Ensure Docker is running.
2.  Run `docker compose up --build`.
3.  Access Swagger UI at `http://localhost/api/user-service/docs`.
