from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.game import Game, GameAccount
from app.models.user import User
from app.schemas.game import GameAccountLinkRequest
from app.services.user_service import UserService
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/games", tags=["games"])

@router.get("")
async def list_games(db: AsyncSession = Depends(get_db)):
    stmt = select(Game)
    games = (await db.execute(stmt)).scalars().all()
    return [{
        "key": g.key,
        "display_name": g.display_name,
        "tier": g.tier,
        "is_enabled": g.is_enabled
    } for g in games]

@router.post("/link")
async def link_game_account(
    data: GameAccountLinkRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not data.consent:
        raise HTTPException(status_code=400, detail="Account-linking consent is required.")
    try:
        acc, code = await UserService.request_game_account_link(
            db=db,
            user_id=user.id,
            game_key=data.game_key,
            external_username=data.external_username
        )
        return {
            "success": True,
            "game_account_id": acc.id,
            "verification_code": code,
            "instructions": f"Place '{code}' anywhere in your official {acc.game_key} profile bio, then click Verify."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify/{game_account_id}")
async def verify_account(
    game_account_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    success, message = await UserService.verify_game_account(db, game_account_id, user.id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}
