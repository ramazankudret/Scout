
import asyncio
from sqlalchemy import text
import asyncio
from sqlalchemy import text
from scout.infrastructure.database import engine

async def fix_schema():
    print("Connecting to database...")
    # engine is already an AsyncEngine instance
    
    async with engine.begin() as conn:
        print("Checking if 'agent_name' column exists in 'learned_lessons'...")
        # Check if column exists
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='learned_lessons' AND column_name='agent_name'"
        ))
        if result.fetchone():
            print("Column 'agent_name' already exists.")
        else:
            print("Adding 'agent_name' column...")
            await conn.execute(text("ALTER TABLE learned_lessons ADD COLUMN agent_name VARCHAR(50)"))
            print("Column added successfully.")

    await engine.dispose()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(fix_schema())
