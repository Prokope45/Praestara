import uuid
from datetime import datetime

from sqlmodel import Session, func, select

from app.models import (
    Question,
    QuestionSection,
    QuestionnaireTemplate,
    QuestionnaireTemplateCreate,
    QuestionnaireTemplatesPublic,
    QuestionnaireTemplateUpdate,
)


class Template:

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

    def read_template(
        self, *, session: Session, template_id: uuid.UUID
    ):
        return session.get(QuestionnaireTemplate, template_id)

    def read_templates(
        self, *, session: Session, skip: int = 0, limit: int = 100
    ) -> QuestionnaireTemplatesPublic:
        count_statement = select(func.count()).select_from(QuestionnaireTemplate)
        count = session.exec(count_statement).one()

        statement = select(QuestionnaireTemplate).offset(skip).limit(limit)
        templates = session.exec(statement).all()

        return QuestionnaireTemplatesPublic(
            data=templates,
            count=count
        )

    def create_template(
        self, *, session: Session, questionnaire_in: QuestionnaireTemplateCreate, created_by_id: uuid.UUID
    ) -> QuestionnaireTemplate:
        # Create the questionnaire template without questions first
        questionnaire_data = questionnaire_in.model_dump(exclude={"questions", "sections"})
        db_questionnaire = QuestionnaireTemplate.model_validate(
            questionnaire_data, update={"created_by_id": created_by_id}
        )
        session.add(db_questionnaire)
        session.flush()  # Flush to get the questionnaire ID

        # Create the sections
        for section_data in questionnaire_in.sections:
            db_section = QuestionSection.model_validate(
                section_data, update={"questionnaire_id": db_questionnaire.id}
            )
            session.add(db_section)

        # Create the questions
        for question_data in questionnaire_in.questions:
            db_question = Question.model_validate(
                question_data, update={"questionnaire_id": db_questionnaire.id}
            )
            session.add(db_question)

        session.commit()
        session.refresh(db_questionnaire)
        return db_questionnaire

    def update_template(
        self, *, session: Session, db_questionnaire: QuestionnaireTemplate, questionnaire_in: QuestionnaireTemplateUpdate
    ) -> QuestionnaireTemplate:
        questionnaire_data = questionnaire_in.model_dump(exclude_unset=True, exclude={"questions", "sections"})
        questionnaire_data["updated_at"] = datetime.utcnow()
        db_questionnaire.sqlmodel_update(questionnaire_data)

        # Update sections
        if questionnaire_in.sections is not None:
            for section in list(db_questionnaire.sections):
                session.delete(section)
            db_questionnaire.sections = []
            session.flush()
            for section_data in questionnaire_in.sections:
                db_section = QuestionSection.model_validate(
                    section_data, update={"questionnaire_id": db_questionnaire.id}
                )
                session.add(db_section)
            session.flush()

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

    def delete_template(
        self, session: Session, template_id: uuid.UUID
    ) -> dict[str, bool]:
        is_deleted: bool = False
        template = self.read_template(
            session=session,
            template_id=template_id
        )
        if not template:
            raise ValueError("Failed to retrieve template.")

        try:
            session.delete(template)
            session.commit()
            is_deleted = True
        except Exception:
            is_deleted = False

        return {"isDeleted": is_deleted}
