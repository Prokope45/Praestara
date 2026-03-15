from app.goal_scaffold.physiology import (
    CrossAxisInfluence,
    GenericPhysiologyConfig,
    GenericPhysiologyExecution,
    GenericPhysiologyState,
    apply_generic_progression,
    compute_cross_axis_support,
)


def test_cross_axis_support_handles_inverse_relationships() -> None:
    support = compute_cross_axis_support(
        target_axis="sleep",
        source_states={"stress": 0.9, "nutrition": 0.7},
        influences=[
            CrossAxisInfluence(source_axis="stress", target_axis="sleep", coefficient=0.3, inverse=True),
            CrossAxisInfluence(source_axis="nutrition", target_axis="sleep", coefficient=0.2),
        ],
    )

    assert support < 0


def test_generic_progression_improves_scores_with_positive_support() -> None:
    updated = apply_generic_progression(
        state=GenericPhysiologyState(
            primary_score=0.4,
            secondary_score=0.4,
            tertiary_score=0.4,
            training_age_weeks=4,
        ),
        execution=GenericPhysiologyExecution(
            adherence_ratio=0.9,
            recovery_adequacy=0.8,
            stress_budget=0.7,
            modulator=0.8,
            cross_axis_support=0.2,
        ),
        config=GenericPhysiologyConfig(base_gain=0.05, age_decay=0.01),
    )

    assert updated.primary_score > 0.4
    assert updated.secondary_score > 0.4
    assert updated.tertiary_score > 0.4
