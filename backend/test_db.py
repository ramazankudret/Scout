
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from scout.infrastructure.database.session import async_session_factory
from sqlalchemy import text

async def main():
    print("Testing DB connection...")
    try:
        async with async_session_factory() as session:
            print("Session created.")
            result = await session.execute(text("SELECT 1"))
            print(f"Query Result: {result.scalar()}")
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
