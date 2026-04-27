from unittest.mock import PropertyMock, patch

from fastapi.testclient import TestClient

from app.core.config import settings


def test_besci_analyze_endpoint(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    payload = {
        "samples": [
            {"text": "I feel stuck, alone, and overwhelmed."},
            {"text": "Today I made a plan, stayed focused, and felt a little better."},
        ]
    }

    response = client.post(
        f"{settings.API_V1_STR}/besci/analyze",
        headers=normal_user_token_headers,
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()["analysis"]
    assert data["sample_count"] == 2
    assert "trajectory_score" in data
    assert "current_state" in data
    assert "higher_order_factors" in data
    assert "process_signals" in data
    assert "domain_analyses" in data
    assert "alignment_signals" in data
    assert "summary" in data


def test_chat_route_injects_besci_context(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    captured: dict[str, str] = {}

    def fake_process_query(*, user_id: str, query: str, temperature: float) -> str:
        captured["user_id"] = user_id
        captured["query"] = query
        captured["temperature"] = str(temperature)
        return "ok"

    with (
        patch(
            "app.koios_client.KoiosClient.KoiosClient.is_configured",
            new_callable=PropertyMock,
            return_value=True,
        ),
        patch(
            "app.koios_client.routes.ai_client.get_history",
            return_value=[
                {"role": "user", "content": "I have been overwhelmed and isolated lately."},
                {"role": "assistant", "content": "Thanks for sharing that."},
                {"role": "user", "content": "I still feel stuck and unsure what to do next."},
            ],
        ),
        patch(
            "app.koios_client.routes.ai_client.process_query",
            side_effect=fake_process_query,
        ),
    ):
        response = client.post(
            f"{settings.API_V1_STR}/ai/chat",
            headers=normal_user_token_headers,
            json={"message": "Today I feel a little more grounded and made a plan."},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "ok"
    assert "Passive longitudinal BeSci context." in captured["query"]
    assert "User message:" in captured["query"]
