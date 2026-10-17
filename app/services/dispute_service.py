from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.dispute import Dispute
from app.models.match import Match, MatchResultEvent
from app.models.audit import AuditLog
from app.services.rating_service import RatingService
from app.services.match_service import MatchService
from app.utils.logger import logger

class DisputeService:
    @staticmethod
    async def open_dispute(
        db: AsyncSession,
        match_id: str,
        user_id: str,
        reason: str
    ) -> Dict[str, Any]:
        match_stmt = select(Match).where(Match.id == match_id)
        match = (await db.execute(match_stmt)).scalar_one_or_none()
        if not match:
            raise ValueError("Match not found.")
        if user_id not in (match.player1_id, match.player2_id):
            raise PermissionError("Only match participants can open a dispute.")
        if match.status in ["completed", "forfeited", "bye"]:
            raise ValueError("This match can no longer be disputed.")
        normalized_reason = reason.strip()
        if len(normalized_reason) < 5:
            raise ValueError("A dispute reason must contain at least 5 characters.")

        existing_stmt = select(Dispute).where(Dispute.match_id == match_id, Dispute.status == "open")
        if (await db.execute(existing_stmt)).scalar_one_or_none():
            raise ValueError("This match already has an open dispute.")

        dispute = Dispute(
            match_id=match_id,
            opened_by_id=user_id,
            status="open",
            reason=normalized_reason
        )
        match.status = "disputed"
        db.add(dispute)
        await db.commit()
        await db.refresh(dispute)
        return {
            "success": True,
            "message": "Dispute submitted for Hub Captain review.",
            "dispute_id": dispute.id
        }

    @staticmethod
    async def resolve_dispute(
        db: AsyncSession,
        dispute_id: str,
        captain_id: str,
        decision: str,  # 'confirm_p1', 'confirm_p2', 'forfeit_p1', 'forfeit_p2'
        reason: str
    ) -> Dict[str, Any]:
        stmt = select(Dispute).where(Dispute.id == dispute_id)
        dispute = (await db.execute(stmt)).scalar_one_or_none()
        if not dispute:
            raise ValueError("Dispute not found.")
        if dispute.status != "open":
            raise ValueError("Dispute has already been resolved.")
        if decision not in {"confirm_p1", "confirm_p2", "forfeit_p1", "forfeit_p2"}:
            raise ValueError("Unsupported dispute decision.")
        normalized_reason = reason.strip()
        if len(normalized_reason) < 5:
            raise ValueError("A resolution reason must contain at least 5 characters.")

        match_stmt = select(Match).where(Match.id == dispute.match_id)
        match = (await db.execute(match_stmt)).scalar_one_or_none()
        if not match:
            raise ValueError("Match associated with dispute not found.")

        # Determine winner
        winner_id = None
        outcome = "dispute_resolved"
        if decision == "confirm_p1" or decision == "forfeit_p2":
            winner_id = match.player1_id
            outcome = "player1_win"
        elif decision == "confirm_p2" or decision == "forfeit_p1":
            winner_id = match.player2_id
            outcome = "player2_win"

        # Check prior result event if one exists
        last_event_stmt = select(MatchResultEvent).where(
            MatchResultEvent.match_id == match.id
        ).order_by(MatchResultEvent.created_at.desc())
        last_event = (await db.execute(last_event_stmt)).scalars().first()

        # Append new MatchResultEvent (Append-only guarantee!)
        new_event = MatchResultEvent(
            match_id=match.id,
            prior_event_id=last_event.id if last_event else None,
            acting_user_id=captain_id,
            outcome=outcome,
            winner_id=winner_id,
            reason=f"Captain decision ({decision}): {normalized_reason}"
        )
        db.add(new_event)

        # Update match and dispute
        match.status = "completed"
        match.winner_id = winner_id

        dispute.status = "resolved"
        dispute.captain_decision = decision
        dispute.resolved_by_id = captain_id
        dispute.resolved_at = datetime.utcnow()

        # Advance bracket
        await MatchService._advance_bracket_winner(db, match, winner_id)

        # Apply Elo ratings
        if winner_id:
            await RatingService.apply_match_elo_update(
                db, match.player1_id, match.player2_id, winner_id, "tier_b", "standard"
            )

        # Log audit action
        audit = AuditLog(
            user_id=captain_id,
            action="resolve_dispute",
            resource_type="dispute",
            resource_id=dispute.id,
            details_json=f'{{"decision": "{decision}", "reason": "{normalized_reason}", "winner_id": "{winner_id}"}}'
        )
        db.add(audit)

        await db.commit()
        return {
            "success": True,
            "message": "Dispute successfully resolved by Hub Captain.",
            "winner_id": winner_id,
            "decision": decision
        }
