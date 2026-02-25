import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

from pydantic import EmailStr
import sqlalchemy as sa
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from typing import List


# Enums for questionnaire system
class ScaleType(str, Enum):
    LIKERT_5 = "LIKERT_5"
    LIKERT_7 = "LIKERT_7"
    YES_NO = "YES_NO"
    CUSTOM_NUMERIC = "CUSTOM_NUMERIC"


class AppointmentStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AssignmentStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    profile_image: str | None = Field(default=None, sa_type=sa.Text)
    onboarding_completed_at: datetime | None = Field(
        default=None, sa_type=sa.DateTime(timezone=True)
    )


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    orientations: list["Orientation"] = Relationship(back_populates="owner", cascade_delete=True)
    created_questionnaires: list["QuestionnaireTemplate"] = Relationship(back_populates="created_by", cascade_delete=True)
    appointments: list["Appointment"] = Relationship(back_populates="user", cascade_delete=True)
    questionnaire_assignments: list["QuestionnaireAssignment"] = Relationship(back_populates="user", cascade_delete=True)
    questionnaire_responses: list["QuestionnaireResponse"] = Relationship(back_populates="user", cascade_delete=True)
    legacy_questionnaire_responses: list["LegacyQuestionnaireResponse"] = Relationship(
        back_populates="owner", cascade_delete=True
    )
    engine89_results: list["Engine89Result"] = Relationship(
        back_populates="owner", cascade_delete=True
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


# Orientation Trait models
class OrientationTraitBase(SQLModel):
    name: str = Field(max_length=255)
    value: int = Field(ge=0, le=100)  # 0-100 percentage
    description: str | None = Field(default=None, max_length=500)


class OrientationTraitCreate(OrientationTraitBase):
    pass


class OrientationTraitUpdate(OrientationTraitBase):
    name: str | None = Field(default=None, max_length=255)  # type: ignore
    value: int | None = Field(default=None, ge=0, le=100)  # type: ignore


class OrientationTrait(OrientationTraitBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    orientation_id: uuid.UUID = Field(
        foreign_key="orientation.id", nullable=False, ondelete="CASCADE"
    )
    orientation: Optional["Orientation"] = Relationship(back_populates="traits")


class OrientationTraitPublic(OrientationTraitBase):
    id: uuid.UUID


# Orientation models
class OrientationBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None)


class OrientationCreate(OrientationBase):
    traits: list[OrientationTraitCreate] = []


class OrientationUpdate(OrientationBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    traits: list[OrientationTraitCreate] | None = None


class Orientation(OrientationBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: Optional["User"] = Relationship(back_populates="orientations")
    traits: list["OrientationTrait"] = Relationship(
        back_populates="orientation", cascade_delete=True
    )


class OrientationPublic(OrientationBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    traits: list[OrientationTraitPublic] = []


class OrientationsPublic(SQLModel):
    data: list[OrientationPublic]
    count: int


# Question models (defined before QuestionnaireTemplate to avoid forward reference issues)
class QuestionBase(SQLModel):
    question_text: str = Field(max_length=1000)
    order: int = Field(ge=0)
    is_required: bool = True
    scale_type: ScaleType = Field(default=ScaleType.LIKERT_5)
    # Custom numeric scale fields
    custom_min_value: int | None = Field(default=None)
    custom_max_value: int | None = Field(default=None)
    custom_unit_label: str | None = Field(default=None, max_length=50)


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(QuestionBase):
    question_text: str | None = Field(default=None, max_length=1000)  # type: ignore
    order: int | None = Field(default=None, ge=0)  # type: ignore


class Question(QuestionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    questionnaire_id: uuid.UUID = Field(
        foreign_key="questionnairetemplate.id", nullable=False, ondelete="CASCADE"
    )
    questionnaire: Optional["QuestionnaireTemplate"] = Relationship(back_populates="questions")
    answers: list["Answer"] = Relationship(back_populates="question", cascade_delete=True)


class QuestionPublic(QuestionBase):
    id: uuid.UUID
    questionnaire_id: uuid.UUID


# Questionnaire Template models
class QuestionnaireTemplateBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = True


class QuestionnaireTemplateCreate(QuestionnaireTemplateBase):
    questions: list[QuestionCreate] = []


class QuestionnaireTemplateUpdate(QuestionnaireTemplateBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    questions: list[QuestionCreate] | None = None


class QuestionnaireTemplate(QuestionnaireTemplateBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional["User"] = Relationship(back_populates="created_questionnaires")
    questions: list["Question"] = Relationship(back_populates="questionnaire", cascade_delete=True)
    assignments: list["QuestionnaireAssignment"] = Relationship(back_populates="questionnaire", cascade_delete=True)


class QuestionnaireTemplatePublic(QuestionnaireTemplateBase):
    id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    questions: list[QuestionPublic] = []


class QuestionnaireTemplatesPublic(SQLModel):
    data: list[QuestionnaireTemplatePublic]
    count: int


# Appointment models
class AppointmentBase(SQLModel):
    appointment_datetime: datetime
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    external_calendar_id: str | None = Field(default=None, max_length=255)
    status: AppointmentStatus = Field(default=AppointmentStatus.SCHEDULED)


class AppointmentCreate(AppointmentBase):
    user_id: uuid.UUID


class AppointmentUpdate(AppointmentBase):
    appointment_datetime: datetime | None = None  # type: ignore
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    status: AppointmentStatus | None = None  # type: ignore


class Appointment(AppointmentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user: Optional["User"] = Relationship(back_populates="appointments")
    questionnaire_assignments: list["QuestionnaireAssignment"] = Relationship(back_populates="appointment", cascade_delete=True)


class AppointmentPublic(AppointmentBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class AppointmentsPublic(SQLModel):
    data: list[AppointmentPublic]
    count: int


# Questionnaire Assignment models
class QuestionnaireAssignmentBase(SQLModel):
    due_date: datetime | None = None
    status: AssignmentStatus = Field(default=AssignmentStatus.PENDING)
    reminder_sent: bool = False


class QuestionnaireAssignmentCreate(SQLModel):
    questionnaire_id: uuid.UUID
    user_id: uuid.UUID
    appointment_id: uuid.UUID | None = None
    due_date: datetime | None = None


class QuestionnaireAssignmentBulkCreate(SQLModel):
    questionnaire_id: uuid.UUID
    user_ids: list[uuid.UUID]
    appointment_id: uuid.UUID | None = None
    due_date: datetime | None = None


class QuestionnaireAssignmentUpdate(SQLModel):
    status: AssignmentStatus | None = None
    reminder_sent: bool | None = None


class QuestionnaireAssignment(QuestionnaireAssignmentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    questionnaire_id: uuid.UUID = Field(
        foreign_key="questionnairetemplate.id", nullable=False, ondelete="CASCADE"
    )
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    appointment_id: uuid.UUID | None = Field(
        default=None, foreign_key="appointment.id", ondelete="CASCADE"
    )
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    questionnaire: Optional["QuestionnaireTemplate"] = Relationship(back_populates="assignments")
    user: Optional["User"] = Relationship(back_populates="questionnaire_assignments")
    appointment: Optional["Appointment"] = Relationship(back_populates="questionnaire_assignments")
    response: Optional["QuestionnaireResponse"] = Relationship(back_populates="assignment", cascade_delete=True)


class QuestionnaireAssignmentPublic(QuestionnaireAssignmentBase):
    id: uuid.UUID
    questionnaire_id: uuid.UUID
    user_id: uuid.UUID
    appointment_id: uuid.UUID | None
    assigned_at: datetime
    questionnaire: QuestionnaireTemplatePublic


class QuestionnaireAssignmentsPublic(SQLModel):
    data: list[QuestionnaireAssignmentPublic]
    count: int


# Answer models (depended on by response base)
class AnswerBase(SQLModel):
    likert_value: int | None = Field(default=None, ge=0)
    text_response: str | None = Field(default=None, max_length=1000)


class AnswerCreate(AnswerBase):
    question_id: uuid.UUID


# Questionnaire Response models
class QuestionnaireResponseBase(SQLModel):
    total_score: int | None = None
    manual_score_override: int | None = None


class QuestionnaireResponseCreate(SQLModel):
    assignment_id: uuid.UUID
    answers: list[AnswerCreate]


class QuestionnaireResponseUpdate(SQLModel):
    manual_score_override: int | None = None


class QuestionnaireResponse(QuestionnaireResponseBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    assignment_id: uuid.UUID = Field(
        foreign_key="questionnaireassignment.id", nullable=False, ondelete="CASCADE", unique=True
    )
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    assignment: Optional["QuestionnaireAssignment"] = Relationship(back_populates="response")
    user: Optional["User"] = Relationship(back_populates="questionnaire_responses")
    answers: list["Answer"] = Relationship(back_populates="response", cascade_delete=True)


class QuestionnaireResponsePublic(QuestionnaireResponseBase):
    id: uuid.UUID
    assignment_id: uuid.UUID
    user_id: uuid.UUID
    completed_at: datetime
    answers: list["AnswerPublic"] = []


class QuestionnaireResponsesPublic(SQLModel):
    data: list[QuestionnaireResponsePublic]
    count: int


# Answer models
class Answer(AnswerBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    response_id: uuid.UUID = Field(
        foreign_key="questionnaireresponse.id", nullable=False, ondelete="CASCADE"
    )
    question_id: uuid.UUID = Field(
        foreign_key="question.id", nullable=False, ondelete="CASCADE"
    )
    response: Optional["QuestionnaireResponse"] = Relationship(back_populates="answers")
    question: Optional["Question"] = Relationship(back_populates="answers")


class AnswerPublic(AnswerBase):
    id: uuid.UUID
    question_id: uuid.UUID
    question: QuestionPublic


# Legacy Questionnaire response models (for checkins and engine89)
class LegacyQuestionnaireResponseBase(SQLModel):
    kind: str = Field(max_length=50)
    schema_version: str = Field(default="v1", max_length=20)
    payload: dict[str, Any] = Field(sa_type=sa.JSON)


class LegacyQuestionnaireResponseCreate(LegacyQuestionnaireResponseBase):
    pass


class LegacyQuestionnaireResponse(LegacyQuestionnaireResponseBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: Optional["User"] = Relationship(back_populates="legacy_questionnaire_responses")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=sa.DateTime(timezone=True),
    )


class LegacyQuestionnaireResponsePublic(LegacyQuestionnaireResponseBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime


class LegacyQuestionnaireResponsesPublic(SQLModel):
    data: list[LegacyQuestionnaireResponsePublic]
    count: int


# Engine89 Result models
class Engine89ResultBase(SQLModel):
    kind: str = Field(max_length=50)
    schema_version: str = Field(default="v1", max_length=20)
    payload: dict[str, Any] = Field(sa_type=sa.JSON)


class Engine89ResultCreate(Engine89ResultBase):
    subject_hash: str | None = Field(default=None, max_length=128)


class Engine89Result(Engine89ResultBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: Optional["User"] = Relationship(back_populates="engine89_results")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=sa.DateTime(timezone=True),
    )


class Engine89ResultPublic(Engine89ResultBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime


class Engine89ResultsPublic(SQLModel):
    data: list[Engine89ResultPublic]
    count: int
