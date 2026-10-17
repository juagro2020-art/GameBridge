from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_, func
from app.models.ratings import PlatformRating, RatingSnapshot
from app.models.game import GameAccount
from app.models.user import User
from app.adapters.registry import registry
from app.ratings.elo import calculate_elo_change, determine_tier
from app.utils.logger import logger

class RatingService:
    @staticmethod
    async def sync_external_rating(
        db: AsyncSession,
        game_account_id: str,
        mode: str = "rapid"
    ) -> Optional[RatingSnapshot]:
        stmt = select(GameAccount).where(GameAccount.id == game_account_id)
        acc = (await db.execute(stmt)).scalar_one_or_none()
        if not acc:
            return None

        adapter = registry.get(acc.game_key)
        if not adapter:
            return None

        ext_result = await adapter.fetch_rating(acc.external_username, mode)
        if not ext_result:
            return None

        # Add snapshot
        snapshot = RatingSnapshot(
            game_account_id=acc.id,
            mode=mode,
            rating=ext_result.rating,
            games_played=ext_result.games_played,
            provisional=ext_result.provisional,
            recorded_at=datetime.utcnow()
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        return snapshot

    @staticmethod
    async def apply_match_elo_update(
        db: AsyncSession,
        player1_id: str,
        player2_id: str,
        winner_id: Optional[str],
        game_key: str = "lichess",
        mode: str = "rapid"
    ) -> Dict[str, Any]:
        """
        Calculates and applies Elo updates transactionally for both participants.
        """
        # Fetch or initialize platform ratings
        stmt1 = select(PlatformRating).where(
            PlatformRating.user_id == player1_id,
            PlatformRating.game_key == game_key,
            PlatformRating.mode == mode
        )
        stmt2 = select(PlatformRating).where(
            PlatformRating.user_id == player2_id,
            PlatformRating.game_key == game_key,
            PlatformRating.mode == mode
        )
        pr1 = (await db.execute(stmt1)).scalar_one_or_none()
        pr2 = (await db.execute(stmt2)).scalar_one_or_none()

        if not pr1:
            pr1 = PlatformRating(user_id=player1_id, game_key=game_key, mode=mode, elo=1200.0, matches_played=0, tier="Bronze")
            db.add(pr1)
        if not pr2:
            pr2 = PlatformRating(user_id=player2_id, game_key=game_key, mode=mode, elo=1200.0, matches_played=0, tier="Bronze")
            db.add(pr2)

        # Determine score
        if winner_id == player1_id:
            score1 = 1.0
        elif winner_id == player2_id:
            score1 = 0.0
        else:
            score1 = 0.5  # Draw

        new_elo1, new_elo2, delta1, delta2 = calculate_elo_change(
            rating_a=pr1.elo,
            rating_b=pr2.elo,
            score_a=score1,
            matches_a=pr1.matches_played,
            matches_b=pr2.matches_played
        )

        pr1.elo = new_elo1
        pr1.matches_played += 1
        pr1.tier = determine_tier(new_elo1)

        pr2.elo = new_elo2
        pr2.matches_played += 1
        pr2.tier = determine_tier(new_elo2)

        await db.commit()
        return {
            "player1": {"new_elo": new_elo1, "delta": delta1, "tier": pr1.tier},
            "player2": {"new_elo": new_elo2, "delta": delta2, "tier": pr2.tier}
        }

    @staticmethod
    async def get_platform_leaderboard(
        db: AsyncSession,
        game_key: str = "lichess",
        mode: str = "rapid",
        city: Optional[str] = None,
        limit: int = 50,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        ranked_query = select(
            PlatformRating.user_id.label("user_id"),
            PlatformRating.elo.label("elo"),
            PlatformRating.matches_played.label("matches_played"),
            PlatformRating.tier.label("tier"),
            User.display_name.label("display_name"),
            User.username.label("username"),
            User.public_identifier.label("public_identifier"),
            User.city.label("city"),
            User.is_demo.label("is_demo"),
            func.row_number().over(
                order_by=(desc(PlatformRating.elo), User.id)
            ).label("rank")
        ).join(User, PlatformRating.user_id == User.id)\
            .where(PlatformRating.game_key == game_key, PlatformRating.mode == mode)
        
        if city and city.lower() != "all":
            ranked_query = ranked_query.where(User.city == city)

        ranked_players = ranked_query.subquery()
        query = select(ranked_players)

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            query = query.where(or_(
                ranked_players.c.display_name.ilike(pattern),
                ranked_players.c.username.ilike(pattern)
            ))

        query = query.order_by(ranked_players.c.rank).limit(limit)
        results = (await db.execute(query)).mappings().all()

        leaderboard = []
        for result in results:
            leaderboard.append({
                "rank": result["rank"],
                "user_id": result["user_id"],
                "display_name": result["display_name"],
                "username": result["username"],
                "public_identifier": result["public_identifier"],
                "city": result["city"],
                "elo": result["elo"],
                "matches_played": result["matches_played"],
                "tier": result["tier"],
                "is_demo": result["is_demo"]
            })
        return leaderboard
