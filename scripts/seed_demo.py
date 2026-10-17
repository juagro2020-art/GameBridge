import asyncio
import os
import sys

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.database_init import init_db
from app.services.demo_service import DemoService

async def main():
    print("Initializing database...")
    await init_db()
    print("Seeding demonstration dataset...")
    async with AsyncSessionLocal() as session:
        res = await DemoService.seed_demo_data(session)
        print(f"Demo data seeded successfully: {res}")

if __name__ == "__main__":
    asyncio.run(main())
