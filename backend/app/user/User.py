import base64
import uuid

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    UpdatePassword,
    User,
    UserCreate,
    UserUpdate,
    UserUpdateMe,
)
from app.questionnaire import questionnaire
from app.utils import generate_new_account_email, send_email


class UserLogic:
    _instance = None

    def __init__(self) -> None:
        """Deny instantiation of class."""
        return None

    def __new__(cls):
        """Instantiates singleton if none exist yet."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create(self, *, session: Session, user_create: UserCreate) -> User:
        db_obj = User.model_validate(
            user_create, update={"hashed_password": get_password_hash(user_create.password)}
        )
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def update(self, *, session: Session, db_user: User, user_in: UserUpdate) -> User:
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

    def get_by_email(self, *, session: Session, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        session_user = session.exec(statement).first()
        return session_user

    def authenticate(self, *, session: Session, email: str, password: str) -> User | None:
        db_user = self.get_by_email(session=session, email=email)
        if not db_user:
            return None
        if not verify_password(password, db_user.hashed_password):
            return None
        return db_user

    def read_all(self, *, session: Session, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
        count_statement = select(func.count()).select_from(User)
        count = session.exec(count_statement).one()

        statement = select(User).offset(skip).limit(limit)
        users = session.exec(statement).all()
        return list(users), count

    def read_by_id(self, *, session: Session, user_id: uuid.UUID) -> User | None:
        return session.get(User, user_id)

    def register_new_user(self, *, session: Session, user_in: UserCreate) -> User:
        user = self.get_by_email(session=session, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )

        user = self.create(session=session, user_create=user_in)

        if not user.is_superuser:
            questionnaire.assignment.assign_onboarding_questionnaire(session=session, user_id=user.id)

        return user

    def update_me(self, *, session: Session, user_in: UserUpdateMe, current_user: User) -> User:
        if user_in.email:
            existing_user = self.get_by_email(session=session, email=user_in.email)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(
                    status_code=409, detail="User with this email already exists"
                )
        user_data = user_in.model_dump(exclude_unset=True)
        current_user.sqlmodel_update(user_data)
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
        return current_user

    def update_password_me(self, *, session: Session, body: UpdatePassword, current_user: User) -> None:
        if not verify_password(body.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect password")
        if body.current_password == body.new_password:
            raise HTTPException(
                status_code=400, detail="New password cannot be the same as the current one"
            )
        hashed_password = get_password_hash(body.new_password)
        current_user.hashed_password = hashed_password
        session.add(current_user)
        session.commit()

    def upload_profile_image(self, *, session: Session, current_user: User, content_type: str, contents: bytes) -> User:
        if not content_type or not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 5MB")

        base64_image = base64.b64encode(contents).decode('utf-8')
        data_url = f"data:{content_type};base64,{base64_image}"

        current_user.profile_image = data_url
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
        return current_user

    def delete_profile_image(self, *, session: Session, current_user: User) -> User:
        current_user.profile_image = None
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
        return current_user

    def delete_me(self, *, session: Session, current_user: User) -> None:
        if current_user.is_superuser:
            raise HTTPException(
                status_code=403, detail="Super users are not allowed to delete themselves"
            )
        if not current_user.can_delete_account:
            raise HTTPException(
                status_code=403, detail=(
                    "You do not have permission to delete your account."
                    "Please contact an administrator."
                )
            )
        session.delete(current_user)
        session.commit()

    def admin_update_user(self, *, session: Session, user_id: uuid.UUID, user_in: UserUpdate) -> User:
        db_user = session.get(User, user_id)
        if not db_user:
            raise HTTPException(
                status_code=404,
                detail="The user with this id does not exist in the system",
            )
        if user_in.email:
            existing_user = self.get_by_email(session=session, email=user_in.email)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=409, detail="User with this email already exists"
                )

        db_user = self.update(session=session, db_user=db_user, user_in=user_in)
        return db_user

    def admin_delete_user(self, *, session: Session, current_user: User, user_id: uuid.UUID) -> None:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user == current_user:
            raise HTTPException(
                status_code=403, detail="Super users are not allowed to delete themselves"
            )
        session.delete(user)
        session.commit()

    def send_new_account_email(self, *, email_to: str, username: str, password: str) -> None:
        if settings.emails_enabled and email_to:
            email_data = generate_new_account_email(
                email_to=email_to, username=username, password=password
            )
            send_email(
                email_to=email_to,
                subject=email_data.subject,
                html_content=email_data.html_content,
            )
