from app.goal_scaffold.physiology import decode_subjective_state


def test_subjective_decoder_maps_text_to_bounded_constructs() -> None:
    decoded = decode_subjective_state(
        text="I feel tired, stressed, and unmotivated after missing my plan.",
        current_dimensions={"vitality": 0.5, "stress_load": 0.3, "motivation": 0.6},
    )

    assert decoded.dimension_deltas["vitality"] < 0
    assert decoded.dimension_deltas["stress_load"] > 0
    assert decoded.dimension_deltas["motivation"] < 0
    assert decoded.suggested_probes


def test_subjective_decoder_respects_saturation() -> None:
    decoded = decode_subjective_state(
        text="I feel confident and focused.",
        current_dimensions={"self_efficacy": 0.95, "goal_clarity": 0.95},
    )

    assert decoded.dimension_deltas["self_efficacy"] < 0.06
