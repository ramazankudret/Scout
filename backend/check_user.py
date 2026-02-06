
import asyncio
from sqlalchemy import text
from scout.infrastructure.database import engine
from scout.core.security import get_password_hash

async def check_users():
    print("Connecting to database...")
    async with engine.begin() as conn:
        # 1. Check schema
        print("Checking 'users' table columns...")
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users'"
        ))
        columns = [row[0] for row in result.fetchall()]
        print(f"Found columns: {columns}")
        
        required = ["id", "username", "email", "hashed_password", "is_active"]
        missing = [c for c in required if c not in columns]
        if missing:
            print(f"CRITICAL: Missing columns in users table: {missing}")
        else:
            print("Users table schema looks OK.")

        # 2. Check user
        print("Checking for user 'erkscoutt'...")
        result = await conn.execute(text(
            "SELECT id, username, email FROM users WHERE username='erkscoutt'"
        ))
        user = result.fetchone()
        
        if user:
            print(f"User found: {user}")
        else:
            print("User 'erkscoutt' NOT found. Creating it...")
            from uuid import uuid4
            import uuid
            
            pwd_hash = get_password_hash("erkancan123") # Default password
            
            # Simple insert
            await conn.execute(text(
                "INSERT INTO users (id, username, email, hashed_password, is_active, is_superuser, created_at, updated_at) "
                "VALUES (:id, :username, :email, :pwd, :active, :superuser, NOW(), NOW())"
            ), {
                "id": uuid4(),
                "username": "erkscoutt",
                "email": "erkscoutt@example.com",
                "pwd": pwd_hash,
                "active": True,
                "superuser": True
            })
            print("User 'erkscoutt' created with password 'erkancan123'.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_users())
