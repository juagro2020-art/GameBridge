from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.badge import Badge, UserBadge
from app.models.match import Match
from app.utils.logger import logger

class BadgeService:
    @staticmethod
    async def award_badge(db: AsyncSession, user_id: str, badge_key: str):
        # Fetch badge
        b_stmt = select(Badge).where(Badge.key == badge_key)
        badge = (await db.execute(b_stmt)).scalar_one_or_none()
        if not badge:
            return

        # Check if user already has it
        ub_stmt = select(UserBadge).where(UserBadge.user_id == user_id, UserBadge.badge_id == badge.id)
        existing = (await db.execute(ub_stmt)).scalar_one_or_none()
        if existing:
            return

        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge.id,
            awarded_at=datetime.utcnow()
        )
        db.add(user_badge)
        await db.commit()
        logger.info(f"Awarded badge '{badge_key}' to user {user_id}")

    @staticmethod
    async def check_and_award_win_badges(db: AsyncSession, user_id: str):
        # Count total wins
        stmt = select(Match).where(Match.winner_id == user_id, Match.status == "completed")
        wins = (await db.execute(stmt)).scalars().all()
        win_count = len(wins)

        if win_count >= 1:
            await BadgeService.award_badge(db, user_id, "first_win")

        if win_count >= 10:
            # Check last 10 completed matches for this user
            all_matches_stmt = select(Match).where(
                (Match.player1_id == user_id) | (Match.player2_id == user_id),
                Match.status == "completed"
            ).order_by(Match.updated_at.desc()).limit(10)
            recent_10 = (await db.execute(all_matches_stmt)).scalars().all()
            if len(recent_10) == 10 and all(m.winner_id == user_id for m in recent_10):
                await BadgeService.award_badge(db, user_id, "streak_10")
