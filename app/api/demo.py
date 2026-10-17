from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.demo_service import DemoService
from app.auth.dependencies import require_admin

router = APIRouter(prefix="/api/demo", tags=["demo"])

@router.post("/reset")
async def reset_demo(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin)
):
    """
    Safely resets the demo dataset (wiping only is_demo=True records) and re-seeds.
    Restricted to platform administrators; only demo records are removed.
    """
    await DemoService.safe_demo_wipe(db)
    res = await DemoService.seed_demo_data(db)
    return {"success": True, "message": "Demo data safely reset and freshly re-seeded!", "data": res}
