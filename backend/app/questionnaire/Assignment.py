import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
import random

from sqlmodel import Session, func, select

from app.api.deps import CurrentUser
from app.models import (
    QuestionnaireAssignment,
    QuestionnaireAssignmentBulkCreate,
    QuestionnaireAssignmentCreate,
    QuestionnaireTemplate,
)


class Assignment:

    _instance = None

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

    def __randomize_answers(self, session: Session, assignment_in: QuestionnaireAssignmentCreate):
        questionnaire = session.get(QuestionnaireTemplate, assignment_in.questionnaire_id)

        if not assignment_in.prefill or not questionnaire:
            return None

        answers = {}
        for question in questionnaire.questions:
            if question.scale_type == "LIKERT_5":
                answers[str(question.id)] = random.randint(1, 5)
            elif question.scale_type == "LIKERT_7":
                answers[str(question.id)] = random.randint(1, 7)
            elif question.scale_type == "YES_NO":
                answers[str(question.id)] = random.randint(0, 1)
            elif question.scale_type == "CUSTOM_NUMERIC":
                min_val = question.custom_min_value or 0
                max_val = question.custom_max_value or 100
                answers[str(question.id)] = random.randint(min_val, max_val)
            elif question.scale_type == "TEXT":
                answers[str(question.id)] = "Random generated text answer for demo."
            elif question.scale_type == "FREQUENCY":
                answers[str(question.id)] = random.randint(0, 3)
            elif question.scale_type == "DOMAIN_RATING":
                answers[str(question.id)] = {"importance": random.randint(0, 10), "consistency": random.randint(0, 10), "note": "Random generated note"}
        return answers

    # Questionnaire Assignment CRUD
    def create(
        self, *, session: Session, assignment_in: QuestionnaireAssignmentCreate
    ) -> QuestionnaireAssignment:
        db_assignment = QuestionnaireAssignment.model_validate(assignment_in)
        session.add(db_assignment)
        session.commit()
        session.refresh(db_assignment)
        return db_assignment

    def create_bulk(
        self, *, session: Session, assignment_in: QuestionnaireAssignmentBulkCreate
    ) -> list[QuestionnaireAssignment]:
        """Create multiple questionnaire assignments at once"""
        assignments = []

        # questionnaire = session.get(QuestionnaireTemplate, assignment_in.questionnaire_id)
        saved_progress = None

        if answers := self.__randomize_answers(session=session, assignment_in=assignment_in):
            saved_progress = {"answers": answers, "lastPage": 0}

        for user_id in assignment_in.user_ids:
            db_assignment = QuestionnaireAssignment(
                questionnaire_id=assignment_in.questionnaire_id,
                user_id=user_id,
                appointment_id=assignment_in.appointment_id,
                due_date=assignment_in.due_date,
                saved_progress=saved_progress,
            )
            session.add(db_assignment)
            assignments.append(db_assignment)

        session.commit()

        # Refresh all assignments
        for assignment in assignments:
            session.refresh(assignment)

        return assignments

    def assign_onboarding_questionnaire(self, *, session: Session, user_id: uuid.UUID) -> QuestionnaireAssignment | None:
        """
        Auto-assign the "Praestara Onboarding" questionnaire to a user if it exists.
        Returns the created assignment or None if the questionnaire doesn't exist.
        """
        # Find the active "Praestara Onboarding" questionnaire
        onboarding_questionnaire = session.exec(
            select(QuestionnaireTemplate).where(
                QuestionnaireTemplate.title == "Praestara Onboarding",
                QuestionnaireTemplate.is_active
            )
        ).first()

        if not onboarding_questionnaire:
            return None

        # Create the assignment with a 7-day due date
        assignment_data = QuestionnaireAssignmentCreate(
            questionnaire_id=onboarding_questionnaire.id,
            user_id=user_id,
            due_date=datetime.now(timezone.utc) + timedelta(days=7)
        )

        return self.create(session=session, assignment_in=assignment_data)

    def read(
        self, session: Session, assignment_id: uuid.UUID
    ):
        return session.get(QuestionnaireAssignment, assignment_id)

    def read_all(
        self, session: Session,
        skip: int, limit: int, questionnaire_id: uuid.UUID
    ):
        if questionnaire_id:
            count_statement = (
                select(func.count())
                .select_from(QuestionnaireAssignment)
                .where(QuestionnaireAssignment.questionnaire_id == questionnaire_id)
            )
            count = session.exec(count_statement).one()

            statement = (
                select(QuestionnaireAssignment)
                .where(QuestionnaireAssignment.questionnaire_id == questionnaire_id)
                .offset(skip)
                .limit(limit)
            )
        else:
            count_statement = select(func.count()).select_from(QuestionnaireAssignment)
            count = session.exec(count_statement).one()

            statement = select(QuestionnaireAssignment).offset(skip).limit(limit)

        assignments = session.exec(statement).all()
        return assignments, count

    def read_my_assignments(
        self, session: Session, current_user: CurrentUser,
        skip: int, limit: int
    ) -> tuple:
        count_statement = (
            select(func.count())
            .select_from(QuestionnaireAssignment)
            .where(QuestionnaireAssignment.user_id == current_user.id)
        )
        count = session.exec(count_statement).one()

        statement = (
            select(QuestionnaireAssignment)
            .where(QuestionnaireAssignment.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        assignments = session.exec(statement).all()

        return assignments, count

    def update_progress(
        self, session: Session, assignment: Any, progress: dict
    ):
        assignment.saved_progress = progress
        session.add(assignment)
        session.commit()
        session.refresh(assignment)

    def delete(
        self, session: Session, assignment_id: uuid.UUID
    ) -> dict[str, bool]:
        is_deleted: bool = False
        assignment = self.read(
            session=session,
            assignment_id=assignment_id
        )
        if not assignment:
            raise ValueError("Failed to retrieve assignment")

        try:
            session.delete(assignment)
            session.commit()
            is_deleted = True
        except Exception:
            is_deleted = False
        return {"isDeleted": is_deleted}
