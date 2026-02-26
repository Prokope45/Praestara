import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.health import service
from app.goal_scaffold.health.models import (
    HealthPillar,
    HealthPillarPublic,
    HealthProfile,
    HealthProfilePublic,
    PillarAssessment,
    PillarAssessmentCreate,
    PillarAssessmentPublic,
)
from app.goal_scaffold.enums import PillarType

router = APIRouter()


@router.get("/profile", response_model=HealthProfilePublic)
def get_health_profile(
    session: SessionDep,
    current_user: CurrentUser,
) -> HealthProfile:
    stmt = select(HealthProfile).where(
        HealthProfile.user_id == current_user.id
    )
    profile = session.exec(stmt).first()
    if profile is None:
        profile = service.initialize_health_profile(session, current_user.id)
        session.commit()
        session.refresh(profile)
    return profile


@router.post("/assessment", response_model=PillarAssessmentPublic)
def record_assessment(
    body: PillarAssessmentCreate,
    pillar_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> PillarAssessment:
    pillar = session.get(HealthPillar, pillar_id)
    if pillar is None:
        raise HTTPException(status_code=404, detail="Pillar not found")

    profile = session.get(HealthProfile, pillar.health_profile_id)
    if profile is None or profile.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pillar not found")

    assessment = service.record_assessment(session, pillar_id, body)
    service.update_profile(session, pillar.health_profile_id)
    session.commit()
    session.refresh(assessment)
    return assessment


@router.get("/pillars", response_model=list[HealthPillarPublic])
def get_pillars(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[HealthPillar]:
    stmt = select(HealthProfile).where(
        HealthProfile.user_id == current_user.id
    )
    profile = session.exec(stmt).first()
    if profile is None:
        profile = service.initialize_health_profile(session, current_user.id)
        session.commit()
        session.refresh(profile)

    stmt = select(HealthPillar).where(
        HealthPillar.health_profile_id == profile.id
    )
    return list(session.exec(stmt).all())


@router.get("/priority", response_model=PillarType)
def get_priority(
    session: SessionDep,
    current_user: CurrentUser,
) -> PillarType:
    stmt = select(HealthProfile).where(
        HealthProfile.user_id == current_user.id
    )
    profile = session.exec(stmt).first()
    if profile is None:
        return PillarType.ENDURANCE
    return profile.primary_focus


@router.get(
    "/pillar-history/{pillar_id}",
    response_model=list[PillarAssessmentPublic],
)
def get_pillar_history(
    pillar_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = 50,
    offset: int = 0,
) -> list[PillarAssessment]:
    pillar = session.get(HealthPillar, pillar_id)
    if pillar is None:
        raise HTTPException(status_code=404, detail="Pillar not found")

    profile = session.get(HealthProfile, pillar.health_profile_id)
    if profile is None or profile.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pillar not found")

    stmt = (
        select(PillarAssessment)
        .where(PillarAssessment.pillar_id == pillar_id)
        .order_by(PillarAssessment.assessed_at.desc())  # type: ignore[union-attr]
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(stmt).all())
