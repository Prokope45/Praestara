import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.crud import create_orientation, update_orientation
from app.models import (
    Orientation,
    OrientationCreate,
    OrientationPublic,
    OrientationsPublic,
    OrientationUpdate,
    Message,
)

router = APIRouter(prefix="/orientations", tags=["orientations"])


@router.get("/", response_model=OrientationsPublic)
def read_orientations(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve orientations.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Orientation)
        count = session.exec(count_statement).one()
        statement = select(Orientation).offset(skip).limit(limit)
        orientations = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Orientation)
            .where(Orientation.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Orientation)
            .where(Orientation.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        orientations = session.exec(statement).all()

    return OrientationsPublic(data=orientations, count=count)


@router.get("/{id}", response_model=OrientationPublic)
def read_orientation(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get orientation by ID.
    """
    orientation = session.get(Orientation, id)
    if not orientation:
        raise HTTPException(status_code=404, detail="Orientation not found")
    if not current_user.is_superuser and (orientation.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return orientation


@router.post("/", response_model=OrientationPublic)
def create_orientation_endpoint(
    *, session: SessionDep, current_user: CurrentUser, orientation_in: OrientationCreate
) -> Any:
    """
    Create new orientation.
    """
    orientation = create_orientation(
        session=session, orientation_in=orientation_in, owner_id=current_user.id
    )
    return orientation


@router.put("/{id}", response_model=OrientationPublic)
def update_orientation_endpoint(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    orientation_in: OrientationUpdate,
) -> Any:
    """
    Update an orientation.
    """
    orientation = session.get(Orientation, id)
    if not orientation:
        raise HTTPException(status_code=404, detail="Orientation not found")
    if not current_user.is_superuser and (orientation.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    orientation = update_orientation(
        session=session, db_orientation=orientation, orientation_in=orientation_in
    )
    return orientation


@router.delete("/{id}")
def delete_orientation(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an orientation.
    """
    orientation = session.get(Orientation, id)
    if not orientation:
        raise HTTPException(status_code=404, detail="Orientation not found")
    if not current_user.is_superuser and (orientation.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(orientation)
    session.commit()
    return Message(message="Orientation deleted successfully")
