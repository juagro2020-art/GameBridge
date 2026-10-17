import asyncio
from sqlalchemy import select
from app.database import engine, Base, AsyncSessionLocal
from app.models import Game, Badge
from app.utils.logger import logger

DEFAULT_GAMES = [
    {
        "key": "lichess",
        "display_name": "Lichess.org",
        "tier": "A",
        "is_enabled": True,
        "icon_url": "/static/images/lichess.png",
        "rules_json": '{"modes": ["rapid", "blitz", "bullet", "classical"], "verification": "bio_code"}'
    },
    {
        "key": "chess_com",
        "display_name": "Chess.com",
        "tier": "A",
        "is_enabled": True,
        "icon_url": "/static/images/chesscom.png",
        "rules_json": '{"modes": ["rapid", "blitz", "bullet"], "verification": "official_api"}'
    },
    {
        "key": "tier_b",
        "display_name": "Mobile Title (Configurable)",
        "tier": "B",
        "is_enabled": False,  # Disabled by default until game selected as per Section 9
        "icon_url": "/static/images/mobile_game.png",
        "rules_json": '{"modes": ["standard"], "verification": "screenshot"}'
    }
]

DEFAULT_BADGES = [
    {
        "key": "first_win",
        "name": "First Victory",
        "description": "Won your first tournament match on GameBridge.",
        "icon": "trophy"
    },
    {
        "key": "city_champion",
        "name": "City Cup Champion",
        "description": "Won 1st place in an official city grassroots cup.",
        "icon": "crown"
    },
    {
        "key": "streak_10",
        "name": "Decathlete",
        "description": "Maintained an unbroken 10-match win streak.",
        "icon": "zap"
    }
]

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created successfully.")

    async with AsyncSessionLocal() as session:
        # Seed default games if missing
        for g_data in DEFAULT_GAMES:
            res = await session.execute(select(Game).where(Game.key == g_data["key"]))
            if not res.scalar_one_or_none():
                game = Game(**g_data)
                session.add(game)

        # Seed default badges if missing
        for b_data in DEFAULT_BADGES:
            res = await session.execute(select(Badge).where(Badge.key == b_data["key"]))
            if not res.scalar_one_or_none():
                badge = Badge(**b_data)
                session.add(badge)

        await session.commit()
    logger.info("Default games and badges seeded.")

if __name__ == "__main__":
    asyncio.run(init_db())
