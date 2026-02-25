import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

BASE = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "changethis"

DEMO_EMAIL = "demo.user@example.com"
DEMO_PASSWORD = "DemoPass123!"
DEMO_NAME = "Demo User"


def post_json(url, data, token=None):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_form(url, data):
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    token = post_form(f"{BASE}/login/access-token", {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})["access_token"]

    # create demo user (ignore if already exists)
    try:
        post_json(
            f"{BASE}/users/",
            {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD,
                "full_name": DEMO_NAME,
                "is_active": True,
                "is_superuser": False,
            },
            token,
        )
    except Exception:
        pass

    # login as demo user
    demo_token = post_form(f"{BASE}/login/access-token", {"username": DEMO_EMAIL, "password": DEMO_PASSWORD})["access_token"]

    # onboarding payload (simplified but valid)
    onboarding_payload = {
        "schema_version": "onboarding_v1",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "responses": {
            "sectionA": {
                "a1": "Build a stable, meaningful routine and contribute to my community.",
                "a2": "Learning, teaching, and creating structures that help others grow.",
                "a3": "Not showing up for the relationships that matter.",
                "statements": {"a4_1": 5, "a4_2": 4, "a4_3": 4, "a4_4": 5, "a4_5": 2, "a4_6": 2},
            },
            "sectionB": {"domains": []},
            "sectionC": {
                "statements": {"c1": 4, "c2": 4, "c3": 4, "c4": 2, "c5": 2, "c6": 5, "c7": 2, "c8": 4, "c9": 5},
                "futureSelf": "Someone who aligns daily actions with long-term values.",
            },
            "sectionD": {"statements": {"d1": 4, "d2": 4, "d3": 4, "d4": 2, "d5": 2, "d6": 4, "d7": 2, "d8": 4}},
            "sectionE": {"statements": {"e1": 4, "e2": 2, "e3": 4, "e4": 2, "e5": 5, "e6": 2, "e7": 2, "e8": 4}},
            "sectionF": {"statements": {"f1": 4, "f2": 2, "f3": 2, "f4": 4, "f5": 2, "f6": 4, "f7": 2, "f8": 4}, "stressHelp": "Walking, journaling, and checking values."},
            "sectionG": {
                "mood": {"g_mood_1": 1, "g_mood_2": 1, "g_mood_3": 1, "g_mood_4": 1, "g_mood_5": 1, "g_mood_6": 0, "g_mood_7": 1, "g_mood_8": 0},
                "anxiety": {"g_anx_1": 1, "g_anx_2": 1, "g_anx_3": 1, "g_anx_4": 1, "g_anx_5": 1, "g_anx_6": 0, "g_anx_7": 0},
            },
            "sectionH": {
                "statements": {"h1": 4, "h2": 4, "h3": 3, "h4": 5, "h5": 4, "h6": 5},
                "overallThoughts": "Excited to track alignment over time.",
                "supportive": "Gentle prompts that keep me oriented to values.",
            },
        },
    }

    post_json(
        f"{BASE}/questionnaires/",
        {"kind": "onboarding", "schema_version": "onboarding_v1", "payload": onboarding_payload},
        demo_token,
    )

    # seed some notes
    for i in range(5):
        post_json(
            f"{BASE}/items/",
            {"title": f"Reflection {i+1}", "description": "Short note about progress and alignment."},
            demo_token,
        )

    # create check-ins without LLM dependency (store as questionnaire responses)
    for i in range(20):
        day_plan = f"Focus on values-based actions day {i+1}: deep work, movement, and one relationship touchpoint."
        day_done = f"Completed deep work, exercised, and connected with a friend. Alignment felt stronger than last week."
        post_json(
            f"{BASE}/questionnaires/",
            {
                "kind": "morning_checkin",
                "schema_version": "v1",
                "payload": {
                    "type": "morning",
                    "text": day_plan,
                    "reply": "Noted. What value feels most alive in this plan?",
                },
            },
            demo_token,
        )
        post_json(
            f"{BASE}/questionnaires/",
            {
                "kind": "evening_checkin",
                "schema_version": "v1",
                "payload": {
                    "type": "evening",
                    "text": day_done,
                    "reply": "Nice follow-through. Which value felt most supported today?",
                },
            },
            demo_token,
        )

    print("seeded demo user")


if __name__ == "__main__":
    main()
