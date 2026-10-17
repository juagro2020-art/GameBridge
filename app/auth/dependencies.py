from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.database import get_db
from app.models.user import User
from app.models.hub import HubMembership
from app.auth.session import verify_session_token

async def get_current_user_optional(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    token = request.cookies.get("gb_session")
    if not token:
        # Also check Authorization Bearer header if available
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            
    if not token:
        return None

    payload = verify_session_token(token)
    if not payload:
        return None

    user_id = payload.get("uid")
    if not user_id:
        return None

    stmt = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_current_user(user: Optional[User] = Depends(get_current_user_optional)) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

def require_role(allowed_roles: List[str]):
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles and user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation"
            )
        return user
    return role_checker

require_captain = require_role(["hub_captain", "super_admin"])
require_admin = require_role(["super_admin"])

async def get_managed_hub_ids(db: AsyncSession, user: User) -> Optional[List[str]]:
    if user.role == "super_admin":
        return None
    stmt = select(HubMembership.hub_id).where(
        HubMembership.user_id == user.id,
        HubMembership.role == "captain"
    )
    return list((await db.execute(stmt)).scalars().all())

async def user_manages_hub(db: AsyncSession, user: User, hub_id: Optional[str]) -> bool:
    if user.role == "super_admin":
        return True
    if not hub_id:
        return False
    stmt = select(HubMembership.id).where(
        HubMembership.user_id == user.id,
        HubMembership.hub_id == hub_id,
        HubMembership.role == "captain"
    )
    return (await db.execute(stmt)).scalar_one_or_none() is not None
