import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    ItemCreate,
    User,
    UserCreate,
    UserUpdate,
    Orientation,
    OrientationCreate,
    OrientationUpdate,
    OrientationTrait,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def create_orientation(
    *, session: Session, orientation_in: OrientationCreate, owner_id: uuid.UUID
) -> Orientation:
    # Create the orientation without traits first
    orientation_data = orientation_in.model_dump(exclude={"traits"})
    db_orientation = Orientation.model_validate(
        orientation_data, update={"owner_id": owner_id}
    )
    session.add(db_orientation)
    session.flush()  # Flush to get the orientation ID

    # Create the traits
    for trait_data in orientation_in.traits:
        db_trait = OrientationTrait.model_validate(
            trait_data, update={"orientation_id": db_orientation.id}
        )
        session.add(db_trait)

    session.commit()
    session.refresh(db_orientation)
    return db_orientation


def update_orientation(
    *, session: Session, db_orientation: Orientation, orientation_in: OrientationUpdate
) -> Orientation:
    orientation_data = orientation_in.model_dump(exclude_unset=True, exclude={"traits"})
    db_orientation.sqlmodel_update(orientation_data)

    # If traits are provided, replace all existing traits
    if orientation_in.traits is not None:
        # Delete existing traits - collect them first to avoid iteration issues
        existing_traits = list(db_orientation.traits)
        for trait in existing_traits:
            session.delete(trait)
        
        # Clear the relationship to avoid stale references
        db_orientation.traits = []
        session.flush()

        # Create new traits
        new_traits = []
        for trait_data in orientation_in.traits:
            db_trait = OrientationTrait.model_validate(
                trait_data, update={"orientation_id": db_orientation.id}
            )
            new_traits.append(db_trait)
            session.add(db_trait)
        
        db_orientation.traits = new_traits

    session.add(db_orientation)
    session.commit()
    session.refresh(db_orientation)
    return db_orientation
