import uuid
from typing import Any

from sqlmodel import Session, func, select

from app.api.deps import CurrentUser
from app.models import (
    Answer,
    AssignmentStatus,
    QuestionnaireAssignment,
    QuestionnaireResponse,
    QuestionnaireResponseCreate,
)
from app.questionnaire.Appointment import AppointmentLogic
from app.questionnaire.Assignment import Assignment
from app.questionnaire.Template import Template


class Questionnaire:

    _instance = None
    template = Template()
    assignment = Assignment()
    appointment = AppointmentLogic()

    def __init__(self) -> None:

        """Deny instantiation of class."""
        return None

    def __new__(cls):
        """Instantiates singleton if none exist yet.

        Returns:
            cls: Class to check if instance exists.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # Questionnaire Response CRUD
    def create_questionnaire_response(
        self, *, session: Session, response_in: QuestionnaireResponseCreate, user_id: uuid.UUID
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

    def read_response(self, *, session: Session, response_id: uuid.UUID):
        return session.get(QuestionnaireResponse, response_id)

    def read_my_responses(
        self, session: Session, current_user: CurrentUser,
        skip: int, limit: int
    ) -> tuple:
        count_statement = (
            select(func.count())
            .select_from(QuestionnaireResponse)
            .where(QuestionnaireResponse.user_id == current_user.id)
        )
        count = session.exec(count_statement).one()

        statement = (
            select(QuestionnaireResponse)
            .where(QuestionnaireResponse.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        responses = session.exec(statement).all()

        return responses, count

    def update_response_score(
        self, *, session: Session, response: Any, score_override: Any
    ):
        response.manual_score_override = score_override
        session.add(response)
        session.commit()
        session.refresh(response)
