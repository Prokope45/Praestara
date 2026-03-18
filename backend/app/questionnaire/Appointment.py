import uuid

from sqlmodel import Session, func, select

from app.api.deps import CurrentUser
from app.models import (
    Appointment,
    AppointmentCreate,
    AppointmentUpdate,
)


class AppointmentLogic:
    _instance = None

    def __init__(self) -> None:
        """Deny instantiation of class."""
        return None

    def __new__(cls):
        """Instantiates singleton if none exist yet."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create(
        self, *, session: Session, appointment_in: AppointmentCreate
    ) -> Appointment:
        db_appointment = Appointment.model_validate(appointment_in)
        session.add(db_appointment)
        session.commit()
        session.refresh(db_appointment)
        return db_appointment

    def read(
        self, *, session: Session, appointment_id: uuid.UUID
    ) -> Appointment | None:
        return session.get(Appointment, appointment_id)

    def read_all(
        self, *, session: Session, skip: int, limit: int
    ) -> tuple[list[Appointment], int]:
        count_statement = select(func.count()).select_from(Appointment)
        count = session.exec(count_statement).one()

        statement = select(Appointment).offset(skip).limit(limit)
        appointments = session.exec(statement).all()
        return appointments, count

    def read_my_appointments(
        self, *, session: Session, current_user: CurrentUser, skip: int, limit: int
    ) -> tuple[list[Appointment], int]:
        count_statement = (
            select(func.count())
            .select_from(Appointment)
            .where(Appointment.user_id == current_user.id)
        )
        count = session.exec(count_statement).one()

        statement = (
            select(Appointment)
            .where(Appointment.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        appointments = session.exec(statement).all()
        return appointments, count

    def update(
        self, *, session: Session, db_appointment: Appointment, appointment_in: AppointmentUpdate
    ) -> Appointment:
        update_data = appointment_in.model_dump(exclude_unset=True)
        db_appointment.sqlmodel_update(update_data)
        session.add(db_appointment)
        session.commit()
        session.refresh(db_appointment)
        return db_appointment

    def delete(
        self, *, session: Session, db_appointment: Appointment
    ) -> dict[str, bool]:
        is_deleted: bool = False
        try:
            session.delete(db_appointment)
            session.commit()
            is_deleted = True
        except Exception:
            is_deleted = False
        return {"isDeleted": is_deleted}
