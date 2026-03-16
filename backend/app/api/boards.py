from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.board import Board
from app.models.board_ad import BoardAd
from app.models.ad import Ad
from app.models.user import User
from app.schemas.board import BoardCreate, BoardResponse, BoardListResponse

router = APIRouter()


@router.get("", response_model=list[BoardResponse])
async def list_boards(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Board).where(Board.user_id == user.id).order_by(Board.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    data: BoardCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Free tier: max 3 boards
    if user.tier == "free":
        count = await db.scalar(
            select(func.count()).select_from(Board).where(Board.user_id == user.id)
        )
        if count >= 3:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free tier allows max 3 boards. Upgrade to Pro for unlimited.",
            )
    board = Board(name=data.name, description=data.description, user_id=user.id)
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Board).where(Board.id == board_id, Board.user_id == user.id)
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    await db.delete(board)
    await db.commit()


@router.post("/{board_id}/ads/{ad_id}", status_code=status.HTTP_201_CREATED)
async def add_ad_to_board(
    board_id: UUID,
    ad_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify board ownership
    result = await db.execute(
        select(Board).where(Board.id == board_id, Board.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")

    # Check ad exists
    result = await db.execute(select(Ad).where(Ad.id == ad_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found")

    # Check duplicate
    result = await db.execute(
        select(BoardAd).where(BoardAd.board_id == board_id, BoardAd.ad_id == ad_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ad already in board")

    # Free tier: max 50 saved ads total
    if user.tier == "free":
        total = await db.scalar(
            select(func.count())
            .select_from(BoardAd)
            .join(Board)
            .where(Board.user_id == user.id)
        )
        if total >= 50:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free tier allows max 50 saved ads. Upgrade to Pro.",
            )

    board_ad = BoardAd(board_id=board_id, ad_id=ad_id)
    db.add(board_ad)
    await db.commit()
    return {"message": "Ad added to board"}


@router.delete("/{board_id}/ads/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_ad_from_board(
    board_id: UUID,
    ad_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BoardAd).where(BoardAd.board_id == board_id, BoardAd.ad_id == ad_id)
    )
    board_ad = result.scalar_one_or_none()
    if not board_ad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await db.delete(board_ad)
    await db.commit()


@router.get("/{board_id}/ads")
async def get_board_ads(
    board_id: UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify ownership
    result = await db.execute(
        select(Board).where(Board.id == board_id, Board.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")

    offset = (page - 1) * limit
    result = await db.execute(
        select(Ad)
        .join(BoardAd)
        .where(BoardAd.board_id == board_id)
        .order_by(BoardAd.added_at.desc())
        .offset(offset)
        .limit(limit)
    )
    ads = result.scalars().all()

    total = await db.scalar(
        select(func.count()).select_from(BoardAd).where(BoardAd.board_id == board_id)
    )

    return {"total": total, "page": page, "limit": limit, "results": ads}
