import uuid
from datetime import datetime
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
    QuestionnaireTemplate,
    QuestionnaireTemplateCreate,
    QuestionnaireTemplateUpdate,
    Question,
    Appointment,
    AppointmentCreate,
    QuestionnaireAssignment,
    QuestionnaireAssignmentCreate,
    QuestionnaireAssignmentBulkCreate,
    QuestionnaireResponse,
    QuestionnaireResponseCreate,
    Answer,
    AssignmentStatus,
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


# Questionnaire Template CRUD
def create_questionnaire_template(
    *, session: Session, questionnaire_in: QuestionnaireTemplateCreate, created_by_id: uuid.UUID
) -> QuestionnaireTemplate:
    # Create the questionnaire template without questions first
    questionnaire_data = questionnaire_in.model_dump(exclude={"questions"})
    db_questionnaire = QuestionnaireTemplate.model_validate(
        questionnaire_data, update={"created_by_id": created_by_id}
    )
    session.add(db_questionnaire)
    session.flush()  # Flush to get the questionnaire ID

    # Create the questions
    for question_data in questionnaire_in.questions:
        db_question = Question.model_validate(
            question_data, update={"questionnaire_id": db_questionnaire.id}
        )
        session.add(db_question)

    session.commit()
    session.refresh(db_questionnaire)
    return db_questionnaire


def update_questionnaire_template(
    *, session: Session, db_questionnaire: QuestionnaireTemplate, questionnaire_in: QuestionnaireTemplateUpdate
) -> QuestionnaireTemplate:
    questionnaire_data = questionnaire_in.model_dump(exclude_unset=True, exclude={"questions"})
    questionnaire_data["updated_at"] = datetime.utcnow()
    db_questionnaire.sqlmodel_update(questionnaire_data)

    # If questions are provided, replace all existing questions
    if questionnaire_in.questions is not None:
        # Delete existing questions
        existing_questions = list(db_questionnaire.questions)
        for question in existing_questions:
            session.delete(question)
        
        db_questionnaire.questions = []
        session.flush()

        # Create new questions
        new_questions = []
        for question_data in questionnaire_in.questions:
            db_question = Question.model_validate(
                question_data, update={"questionnaire_id": db_questionnaire.id}
            )
            new_questions.append(db_question)
            session.add(db_question)
        
        db_questionnaire.questions = new_questions

    session.add(db_questionnaire)
    session.commit()
    session.refresh(db_questionnaire)
    return db_questionnaire


# Appointment CRUD
def create_appointment(
    *, session: Session, appointment_in: AppointmentCreate
) -> Appointment:
    db_appointment = Appointment.model_validate(appointment_in)
    session.add(db_appointment)
    session.commit()
    session.refresh(db_appointment)
    return db_appointment


# Questionnaire Assignment CRUD
def create_questionnaire_assignment(
    *, session: Session, assignment_in: QuestionnaireAssignmentCreate
) -> QuestionnaireAssignment:
    db_assignment = QuestionnaireAssignment.model_validate(assignment_in)
    session.add(db_assignment)
    session.commit()
    session.refresh(db_assignment)
    return db_assignment


def create_bulk_questionnaire_assignments(
    *, session: Session, assignment_in: QuestionnaireAssignmentBulkCreate
) -> list[QuestionnaireAssignment]:
    """Create multiple questionnaire assignments at once"""
    assignments = []
    
    for user_id in assignment_in.user_ids:
        db_assignment = QuestionnaireAssignment(
            questionnaire_id=assignment_in.questionnaire_id,
            user_id=user_id,
            appointment_id=assignment_in.appointment_id,
            due_date=assignment_in.due_date,
        )
        session.add(db_assignment)
        assignments.append(db_assignment)
    
    session.commit()
    
    # Refresh all assignments
    for assignment in assignments:
        session.refresh(assignment)
    
    return assignments


# Questionnaire Response CRUD
def create_questionnaire_response(
    *, session: Session, response_in: QuestionnaireResponseCreate, user_id: uuid.UUID
) -> QuestionnaireResponse:
    # Calculate total score from answers
    total_score = sum(
        answer.likert_value for answer in response_in.answers if answer.likert_value is not None
    )
    
    # Create the response
    db_response = QuestionnaireResponse(
        assignment_id=response_in.assignment_id,
        user_id=user_id,
        total_score=total_score
    )
    session.add(db_response)
    session.flush()  # Flush to get the response ID

    # Create the answers
    for answer_data in response_in.answers:
        db_answer = Answer.model_validate(
            answer_data, update={"response_id": db_response.id}
        )
        session.add(db_answer)

    # Update the assignment status to COMPLETED
    assignment = session.get(QuestionnaireAssignment, response_in.assignment_id)
    if assignment:
        assignment.status = AssignmentStatus.COMPLETED
        session.add(assignment)

    session.commit()
    session.refresh(db_response)
    return db_response
