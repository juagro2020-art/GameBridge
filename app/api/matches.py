from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.match import Match, MatchEvidence
from app.models.user import User
from app.schemas.match import MatchResultSubmit, DisputeCreate, DisputeResolve
from app.services.match_service import MatchService
from app.services.dispute_service import DisputeService
from app.auth.dependencies import get_current_user, require_captain, user_manages_hub
from app.config import settings
import os
import uuid
from pathlib import Path

router = APIRouter(prefix="/api/matches", tags=["matches"])

@router.post("/{match_id}/submit-lichess")
async def submit_lichess_result(
    match_id: str,
    data: MatchResultSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not data.game_link:
        raise HTTPException(status_code=400, detail="Missing Lichess game URL or ID")

    res = await MatchService.submit_lichess_result(
        db=db,
        match_id=match_id,
        user_id=user.id,
        game_link=data.game_link
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/{match_id}/submit-screenshot")
async def submit_screenshot_report(
    match_id: str,
    data: MatchResultSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    res = await MatchService.submit_screenshot_report(
        db=db,
        match_id=match_id,
        user_id=user.id,
        claimed_winner_id=data.winner_id,
        score_p1=data.score_p1,
        score_p2=data.score_p2,
        comments=data.comments
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Could not submit match report."))
    return res

@router.post("/{match_id}/upload-evidence")
async def upload_evidence(
    match_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    match_stmt = select(Match).where(Match.id == match_id)
    match = (await db.execute(match_stmt)).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")
    if user.id not in (match.player1_id, match.player2_id):
        raise HTTPException(status_code=403, detail="Only match participants can upload evidence.")
    if match.status not in ["pending", "scheduled", "in_progress", "disputed"]:
        raise HTTPException(status_code=400, detail="This match is not accepting evidence.")

    allowed_extensions = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    if file.content_type not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported image format. Allowed: JPEG, PNG, WebP.")

    content = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Upload exceeds 3MB limit.")
    signatures = {
        "image/jpeg": content.startswith(b"\xff\xd8\xff"),
        "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    }
    if not signatures[file.content_type]:
        raise HTTPException(status_code=400, detail="The uploaded file content does not match its image type.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    random_filename = f"{uuid.uuid4().hex}{allowed_extensions[file.content_type]}"
    filepath = str(Path(settings.UPLOAD_DIR) / random_filename)

    with open(filepath, "wb") as f:
        f.write(content)

    evidence = MatchEvidence(
        match_id=match_id,
        user_id=user.id,
        file_path=filepath,
        file_name=random_filename,
        file_size=len(content),
        content_type=file.content_type
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)

    return {"success": True, "evidence_id": evidence.id, "file_name": random_filename}

@router.get("/{match_id}/evidence/{evidence_id}")
async def view_match_evidence(
    match_id: str,
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    captain: User = Depends(require_captain)
):
    match = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")

    from app.models.tournament import Tournament
    tournament = (await db.execute(
        select(Tournament).where(Tournament.id == match.tournament_id)
    )).scalar_one_or_none()
    if not tournament or not await user_manages_hub(db, captain, tournament.hub_id):
        raise HTTPException(status_code=403, detail="Evidence is restricted to captains of the assigned hub.")

    evidence = (await db.execute(select(MatchEvidence).where(
        MatchEvidence.id == evidence_id,
        MatchEvidence.match_id == match_id
    ))).scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found.")

    upload_root = Path(settings.UPLOAD_DIR).resolve()
    evidence_path = Path(evidence.file_path).resolve()
    if upload_root not in evidence_path.parents or not evidence_path.is_file():
        raise HTTPException(status_code=404, detail="Evidence file is unavailable.")

    return FileResponse(
        evidence_path,
        media_type=evidence.content_type,
        filename=evidence.file_name,
        content_disposition_type="inline",
        headers={"Cache-Control": "private, no-store"}
    )
