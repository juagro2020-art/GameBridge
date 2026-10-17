from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.dispute import Dispute
from app.models.match import Match
from app.models.tournament import Tournament
from app.models.user import User
from app.schemas.match import DisputeCreate, DisputeResolve
from app.services.dispute_service import DisputeService
from app.auth.dependencies import get_current_user, require_captain, get_managed_hub_ids, user_manages_hub

router = APIRouter(prefix="/api/disputes", tags=["disputes"])

@router.post("")
async def create_dispute(
    data: DisputeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        return await DisputeService.open_dispute(
            db=db,
            match_id=data.match_id,
            user_id=user.id,
            reason=data.reason
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
async def list_disputes(
    db: AsyncSession = Depends(get_db),
    captain: User = Depends(require_captain)
):
    stmt = select(Dispute).order_by(desc(Dispute.created_at))
    hub_ids = await get_managed_hub_ids(db, captain)
    if hub_ids is not None:
        if not hub_ids:
            raise HTTPException(status_code=403, detail="No hub captain membership is assigned to this account.")
        stmt = stmt.join(Match, Dispute.match_id == Match.id).join(
            Tournament, Match.tournament_id == Tournament.id
        ).where(Tournament.hub_id.in_(hub_ids))
    disputes = (await db.execute(stmt)).scalars().all()
    return [{
        "id": d.id,
        "match_id": d.match_id,
        "status": d.status,
        "reason": d.reason,
        "captain_decision": d.captain_decision,
        "created_at": d.created_at.isoformat()
    } for d in disputes]

@router.post("/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: str,
    data: DisputeResolve,
    db: AsyncSession = Depends(get_db),
    captain: User = Depends(require_captain)
):
    try:
        scope_stmt = select(Tournament.hub_id).join(
            Match, Tournament.id == Match.tournament_id
        ).join(Dispute, Match.id == Dispute.match_id).where(Dispute.id == dispute_id)
        hub_id = (await db.execute(scope_stmt)).scalar_one_or_none()
        if hub_id is None and captain.role != "super_admin":
            raise HTTPException(status_code=403, detail="This dispute is not assigned to one of your hubs.")
        if not await user_manages_hub(db, captain, hub_id):
            raise HTTPException(status_code=403, detail="You can only resolve disputes in your assigned hub.")
        res = await DisputeService.resolve_dispute(
            db=db,
            dispute_id=dispute_id,
            captain_id=captain.id,
            decision=data.decision,
            reason=data.reason
        )
        return res
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
