import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.services.demo_service import DemoService

async def main():
    print("Safely wiping demo dataset (preserving real pilot records)...")
    async with AsyncSessionLocal() as session:
        res = await DemoService.safe_demo_wipe(session)
        print(f"Demo wipe result: {res}")
        print("Re-seeding pristine demo dataset...")
        seed_res = await DemoService.seed_demo_data(session)
        print(f"Re-seeded successfully: {seed_res}")

if __name__ == "__main__":
    asyncio.run(main())
