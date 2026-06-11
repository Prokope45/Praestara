"""Program management routes.

Programs are named enrollment containers (e.g. "The Lazarus Project").
A program has admins who can observe member metrics and graduate members
to independent use.

Roles:
  admin  — can view all member metrics, manage membership, graduate members
  member — standard user enrolled in the program

Graduation:
  Sets is_graduated=True + graduated_at. Member keeps all their data and
  continues using Praestara independently, just no longer observable by
  the program admin.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Program,
    ProgramCreate,
    ProgramMembership,
    ProgramMembershipCreate,
    ProgramMembershipPublic,
    ProgramMembershipsPublic,
    ProgramMemberRole,
    ProgramPublic,
    ProgramsPublic,
    ProgramUpdate,
    User,
)

router = APIRouter(prefix="/programs", tags=["programs"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_program(session: Session, program_id: uuid.UUID) -> Program:
    program = session.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


def _require_admin(session: Session, program_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Raises 403 if user is not an admin of the program (superusers always pass)."""
    user = session.get(User, user_id)
    if user and user.is_superuser:
        return
    membership = session.exec(
        select(ProgramMembership).where(
            ProgramMembership.program_id == program_id,
            ProgramMembership.user_id == user_id,
            ProgramMembership.role == ProgramMemberRole.ADMIN,
            ProgramMembership.is_graduated == False,  # noqa: E712
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Program admin access required")


# ---------------------------------------------------------------------------
# Program CRUD
# ---------------------------------------------------------------------------

@router.get("/", response_model=ProgramsPublic)
def list_programs(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
) -> ProgramsPublic:
    """List programs the current user belongs to (any role) or all if superuser."""
    if current_user.is_superuser:
        programs = session.exec(select(Program).offset(skip).limit(limit)).all()
        count = session.exec(select(func.count()).select_from(Program)).one()
    else:
        stmt = (
            select(Program)
            .join(ProgramMembership, Program.id == ProgramMembership.program_id)
            .where(ProgramMembership.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        programs = session.exec(stmt).all()
        count = len(programs)

    return ProgramsPublic(data=[ProgramPublic.model_validate(p) for p in programs], count=count)


@router.post("/", response_model=ProgramPublic)
def create_program(
    session: SessionDep,
    current_user: CurrentUser,
    payload: ProgramCreate,
) -> ProgramPublic:
    """Create a new program. Creator is automatically made an admin member."""
    program = Program(
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        created_by_id=current_user.id,
    )
    session.add(program)
    session.flush()

    # auto-enroll creator as admin
    membership = ProgramMembership(
        program_id=program.id,
        user_id=current_user.id,
        role=ProgramMemberRole.ADMIN,
    )
    session.add(membership)
    session.commit()
    session.refresh(program)
    return ProgramPublic.model_validate(program)


@router.get("/{program_id}", response_model=ProgramPublic)
def get_program(
    session: SessionDep,
    current_user: CurrentUser,
    program_id: uuid.UUID,
) -> ProgramPublic:
    return ProgramPublic.model_validate(_require_program(session, program_id))


@router.patch("/{program_id}", response_model=ProgramPublic)
def update_program(
    session: SessionDep,
    current_user: CurrentUser,
    program_id: uuid.UUID,
    payload: ProgramUpdate,
) -> ProgramPublic:
    _require_admin(session, program_id, current_user.id)
    program = _require_program(session, program_id)
    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(program, field, val)
    session.add(program)
    session.commit()
    session.refresh(program)
    return ProgramPublic.model_validate(program)


# ---------------------------------------------------------------------------
# Membership management
# ---------------------------------------------------------------------------

@router.get("/{program_id}/members", response_model=ProgramMembershipsPublic)
def list_members(
    session: SessionDep,
    current_user: CurrentUser,
    program_id: uuid.UUID,
    include_graduated: bool = False,
) -> ProgramMembershipsPublic:
    _require_admin(session, program_id, current_user.id)
    _require_program(session, program_id)

    stmt = select(ProgramMembership).where(ProgramMembership.program_id == program_id)
    if not include_graduated:
        stmt = stmt.where(ProgramMembership.is_graduated == False)  # noqa: E712
    memberships = session.exec(stmt).all()
    return ProgramMembershipsPublic(
        data=[ProgramMembershipPublic.model_validate(m) for m in memberships],
        count=len(memberships),
    )


@router.post("/{program_id}/members", response_model=ProgramMembershipPublic)
def enroll_member(
    session: SessionDep,
    current_user: CurrentUser,
    program_id: uuid.UUID,
    payload: ProgramMembershipCreate,
) -> ProgramMembershipPublic:
    """Enroll a user into a program. Requires program admin."""
    _require_admin(session, program_id, current_user.id)
    _require_program(session, program_id)

    # check target user exists
    target = session.get(User, payload.user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # idempotent — re-enroll if previously graduated
    existing = session.exec(
        select(ProgramMembership).where(
            ProgramMembership.program_id == program_id,
            ProgramMembership.user_id == payload.user_id,
        )
    ).first()
    if existing:
        if not existing.is_graduated:
            raise HTTPException(status_code=409, detail="User already enrolled")
        # re-enroll graduated member
        existing.is_graduated = False
        existing.graduated_at = None
        existing.enrolled_at = datetime.now(timezone.utc)
        existing.role = payload.role
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return ProgramMembershipPublic.model_validate(existing)

    membership = ProgramMembership(
        program_id=program_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return ProgramMembershipPublic.model_validate(membership)


@router.post("/{program_id}/members/{user_id}/graduate", response_model=ProgramMembershipPublic)
def graduate_member(
    session: SessionDep,
    current_user: CurrentUser,
    program_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ProgramMembershipPublic:
    """Graduate a member to independent use. Admin only.
    Member keeps all data; program admin loses observability."""
    _require_admin(session, program_id, current_user.id)
    membership = session.exec(
        select(ProgramMembership).where(
            ProgramMembership.program_id == program_id,
            ProgramMembership.user_id == user_id,
            ProgramMembership.is_graduated == False,  # noqa: E712
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Active membership not found")

    membership.is_graduated = True
    membership.graduated_at = datetime.now(timezone.utc)
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return ProgramMembershipPublic.model_validate(membership)


# ---------------------------------------------------------------------------
# Member metrics (admin observability)
# ---------------------------------------------------------------------------

@router.get("/{program_id}/members/{user_id}/metrics", response_model=dict)
def get_member_metrics(
    session: SessionDep,
    current_user: CurrentUser,
    program_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict[str, Any]:
    """Return current latent state + physiology snapshot for an enrolled member."""
    _require_admin(session, program_id, current_user.id)
    _require_program(session, program_id)

    # confirm active membership
    membership = session.exec(
        select(ProgramMembership).where(
            ProgramMembership.program_id == program_id,
            ProgramMembership.user_id == user_id,
            ProgramMembership.is_graduated == False,  # noqa: E712
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Active member not found")

    from app.goal_scaffold.self_concept import service as sc_service
    from app.goal_scaffold.physiology import service as phys_service

    dims = sc_service.get_current_dimensions(session, user_id)
    snapshot = phys_service.build_snapshot(session, user_id)

    return {
        "user_id": str(user_id),
        "program_id": str(program_id),
        "enrolled_at": membership.enrolled_at.isoformat(),
        "latent_dimensions": dims,
        "physiology": {
            "axis_scores": snapshot.axis_scores,
            "subjective_energy": snapshot.subjective_energy,
            "latent_dimensions": snapshot.latent_dimensions,
        },
    }


@router.get("/{program_id}/members/{user_id}/observations", response_model=list[dict])
def get_member_observations(
    session: SessionDep,
    current_user: CurrentUser,
    program_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return recent qualitative observations for a member (admin only)."""
    _require_admin(session, program_id, current_user.id)

    membership = session.exec(
        select(ProgramMembership).where(
            ProgramMembership.program_id == program_id,
            ProgramMembership.user_id == user_id,
            ProgramMembership.is_graduated == False,  # noqa: E712
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Active member not found")

    from app.goal_scaffold.self_concept.models import QualitativeObservation

    observations = session.exec(
        select(QualitativeObservation)
        .where(QualitativeObservation.user_id == user_id)
        .order_by(QualitativeObservation.observed_at.desc())
        .limit(limit)
    ).all()

    return [
        {
            "id": str(o.id),
            "context": o.context,
            "observed_at": o.observed_at.isoformat(),
            "decoded_by": o.decoded_by,
            "decoded_dimensions": o.decoded_dimensions,
        }
        for o in observations
    ]
