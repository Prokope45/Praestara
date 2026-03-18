import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.models import (
    Message,
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.user import user_logic

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """
    users, count = user_logic.read_all(session=session, skip=skip, limit=limit)
    return UsersPublic(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = user_logic.register_new_user(session=session, user_in=user_in)
    user_logic.send_new_account_email(email_to=user_in.email, username=user_in.email, password=user_in.password)
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """
    return user_logic.update_me(session=session, user_in=user_in, current_user=current_user)


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    user_logic.update_password_me(session=session, body=body, current_user=current_user)
    return Message(message="Password updated successfully")


@router.post("/me/profile-image", response_model=UserPublic)
async def upload_profile_image(
    *, session: SessionDep, current_user: CurrentUser, file: UploadFile = File(...)
) -> Any:
    """
    Upload profile image for current user.
    """
    contents = await file.read()
    return user_logic.upload_profile_image(
        session=session, current_user=current_user, content_type=file.content_type, contents=contents
    )


@router.delete("/me/profile-image", response_model=UserPublic)
def delete_profile_image(
    *, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Delete profile image for current user.
    """
    return user_logic.delete_profile_image(session=session, current_user=current_user)


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    user_logic.delete_me(session=session, current_user=current_user)
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user_create = UserCreate.model_validate(user_in)
    return user_logic.register_new_user(session=session, user_in=user_create)


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = user_logic.read_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    return user_logic.admin_update_user(session=session, user_id=user_id, user_in=user_in)


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user_logic.admin_delete_user(session=session, current_user=current_user, user_id=user_id)
    return Message(message="User deleted successfully")
