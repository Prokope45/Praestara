import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.goal_scaffold.enums import DimensionSource, ObservationContext
from app.goal_scaffold.events import emit
from app.goal_scaffold.self_concept.cognition_interface import (
    QualitativeDecodingRequest,
    decode_qualitative_text,
)
from app.goal_scaffold.self_concept.models import (
    ConceptDimension,
    IdentityConsistencyIndex,
    QualitativeObservation,
    SelfConceptSnapshot,
)

_DOMAIN = "self_concept"


def create_dimension(
    session: Session,
    user_id: uuid.UUID,
    name: str,
    value: float,
    source: DimensionSource,
) -> ConceptDimension:
    dim = ConceptDimension(
        user_id=user_id,
        name=name,
        value=value,
        source=source,
    )
    session.add(dim)
    session.flush()
    emit(
        session,
        user_id=user_id,
        event_type="self_concept.dimension_created",
        domain=_DOMAIN,
        payload={"dimension_id": str(dim.id), "name": name, "value": value},
    )
    return dim


def update_dimension(
    session: Session,
    dimension_id: uuid.UUID,
    value: float,
    source: DimensionSource,
) -> ConceptDimension:
    dim = session.get(ConceptDimension, dimension_id)
    if dim is None:
        raise ValueError(f"ConceptDimension {dimension_id} not found")

    old_value = dim.value
    dim.value = value
    dim.source = source
    dim.last_updated = datetime.utcnow()
    session.add(dim)
    session.flush()
    emit(
        session,
        user_id=dim.user_id,
        event_type="self_concept.dimension_updated",
        domain=_DOMAIN,
        payload={
            "dimension_id": str(dim.id),
            "name": dim.name,
            "old_value": old_value,
            "new_value": value,
        },
    )
    return dim


def record_observation(
    session: Session,
    user_id: uuid.UUID,
    text: str,
    context: ObservationContext,
) -> QualitativeObservation:
    current_dims = _get_current_dimension_map(session, user_id)

    decoding = decode_qualitative_text(
        QualitativeDecodingRequest(
            user_id=user_id,
            text=text,
            context=context,
            current_dimensions=current_dims,
        )
    )

    obs = QualitativeObservation(
        user_id=user_id,
        text=text,
        context=context,
        decoded_dimensions=decoding.decoded_dimensions,
        decoded_by="stub",
    )
    session.add(obs)
    session.flush()

    for dim_name, delta in decoding.decoded_dimensions.items():
        stmt = select(ConceptDimension).where(
            ConceptDimension.user_id == user_id,
            ConceptDimension.name == dim_name,
        )
        dim = session.exec(stmt).first()
        if dim:
            new_value = max(0.0, min(1.0, dim.value + delta))
            update_dimension(session, dim.id, new_value, DimensionSource.OBSERVATION)

    emit(
        session,
        user_id=user_id,
        event_type="self_concept.observation_recorded",
        domain=_DOMAIN,
        payload={
            "observation_id": str(obs.id),
            "context": context.value,
            "decoded_dimensions": decoding.decoded_dimensions,
        },
    )
    return obs


def compute_snapshot(
    session: Session,
    user_id: uuid.UUID,
    cycle_id: uuid.UUID | None = None,
    identity_consistency_index: float | None = None,
) -> SelfConceptSnapshot:
    dims = _get_current_dimension_map(session, user_id)

    snapshot = SelfConceptSnapshot(
        user_id=user_id,
        dimensions=dims,
        identity_consistency_index=identity_consistency_index,
        cycle_id=cycle_id,
    )
    session.add(snapshot)
    session.flush()

    emit(
        session,
        user_id=user_id,
        event_type="self_concept.snapshot_computed",
        domain=_DOMAIN,
        payload={
            "snapshot_id": str(snapshot.id),
            "dimension_count": len(dims),
            "cycle_id": str(cycle_id) if cycle_id else None,
        },
    )
    return snapshot


def compute_ici(
    session: Session,
    user_id: uuid.UUID,
    cycle_id: uuid.UUID | None = None,
) -> IdentityConsistencyIndex:
    dims = _get_current_dimension_map(session, user_id)

    goal_alignment = _compute_goal_alignment(dims)
    adherence_alignment = _compute_adherence_alignment(dims)
    tone_alignment = _compute_tone_alignment(dims)

    components = {
        "goal_alignment": goal_alignment,
        "adherence_alignment": adherence_alignment,
        "tone_alignment": tone_alignment,
    }
    value = round(
        (goal_alignment + adherence_alignment + tone_alignment) / 3.0, 4
    )

    ici = IdentityConsistencyIndex(
        user_id=user_id,
        value=value,
        components=components,
        cycle_id=cycle_id,
    )
    session.add(ici)
    session.flush()

    emit(
        session,
        user_id=user_id,
        event_type="self_concept.ici_updated",
        domain=_DOMAIN,
        payload={
            "ici_id": str(ici.id),
            "value": value,
            "components": components,
            "cycle_id": str(cycle_id) if cycle_id else None,
        },
    )
    return ici


def seed_dimensions_from_questionnaire(
    session: Session,
    user_id: uuid.UUID,
    questionnaire_responses: dict[str, int],
) -> list[ConceptDimension]:
    dimensions: list[ConceptDimension] = []
    for name, likert_score in questionnaire_responses.items():
        value = _likert_to_normalized(likert_score)
        dim = create_dimension(
            session, user_id, name, value, DimensionSource.QUESTIONNAIRE
        )
        dimensions.append(dim)
    return dimensions


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def get_current_dimensions(session: Session, user_id: uuid.UUID) -> dict[str, float]:
    return _get_current_dimension_map(session, user_id)


def _get_current_dimension_map(session: Session, user_id: uuid.UUID) -> dict[str, float]:
    stmt = select(ConceptDimension).where(ConceptDimension.user_id == user_id)
    dims = session.exec(stmt).all()
    return {d.name: d.value for d in dims}


def _likert_to_normalized(score: int, scale_max: int = 5) -> float:
    return round(max(0.0, min(1.0, (score - 1) / max(scale_max - 1, 1))), 4)


def _compute_goal_alignment(dims: dict[str, float]) -> float:
    relevant = [dims.get("self_efficacy", 0.5), dims.get("motivation", 0.5)]
    return round(sum(relevant) / len(relevant), 4)


def _compute_adherence_alignment(dims: dict[str, float]) -> float:
    relevant = [dims.get("resilience", 0.5), dims.get("self_efficacy", 0.5)]
    return round(sum(relevant) / len(relevant), 4)


def _compute_tone_alignment(dims: dict[str, float]) -> float:
    relevant = [dims.get("optimism", 0.5), dims.get("well_being", 0.5)]
    return round(sum(relevant) / len(relevant), 4)
