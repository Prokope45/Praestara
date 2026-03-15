import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.goal_scaffold.resource_profile.models import (
    UserResourceProfile,
    UserResourceProfileUpdate,
)


def get_or_create_profile(
    session: Session,
    user_id: uuid.UUID,
) -> UserResourceProfile:
    stmt = select(UserResourceProfile).where(
        UserResourceProfile.user_id == user_id
    )
    profile = session.exec(stmt).first()
    if profile:
        return profile

    session.exec(
        insert(UserResourceProfile)
        .values(user_id=user_id)
        .on_conflict_do_nothing(index_elements=[UserResourceProfile.user_id])
    )
    session.flush()
    profile = session.exec(stmt).first()
    if profile is None:
        raise ValueError(f"Unable to create resource profile for user {user_id}")
    return profile


def update_profile(
    session: Session,
    user_id: uuid.UUID,
    profile_in: UserResourceProfileUpdate,
) -> UserResourceProfile:
    stmt = select(UserResourceProfile).where(
        UserResourceProfile.user_id == user_id
    )
    profile = session.exec(stmt).first()
    if not profile:
        session.exec(
            insert(UserResourceProfile)
            .values(user_id=user_id)
            .on_conflict_do_nothing(index_elements=[UserResourceProfile.user_id])
        )
        session.flush()
        profile = session.exec(stmt).first()
        if profile is None:
            raise ValueError(f"Unable to create resource profile for user {user_id}")

    update_data = profile_in.model_dump(exclude_unset=True)
    profile.sqlmodel_update(update_data)
    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.flush()
    return profile


def check_feasibility(
    profile: UserResourceProfile,
    required_hours: float,
    required_equipment: list[str],
) -> dict:
    reasons: list[str] = []
    feasible = True

    if required_hours > profile.weekly_available_hours:
        feasible = False
        reasons.append(
            f"Requires {required_hours}h/week but only "
            f"{profile.weekly_available_hours}h available"
        )

    available = set(profile.equipment_access or [])
    missing = [e for e in required_equipment if e not in available]
    if missing:
        feasible = False
        reasons.append(f"Missing equipment: {', '.join(missing)}")

    return {"feasible": feasible, "reasons": reasons}
