import json
import sys
import urllib.parse
import urllib.request

BASE = "http://localhost:8000/api/v1"
EMAIL = "admin@example.com"
PASSWORD = "changethis"
PRESET = "balanced_baseline"


def post_form(url: str, data: dict[str, str]) -> dict:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(url: str, data: dict, token: str) -> dict:
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    email = sys.argv[1] if len(sys.argv) > 1 else EMAIL
    password = sys.argv[2] if len(sys.argv) > 2 else PASSWORD
    preset = sys.argv[3] if len(sys.argv) > 3 else PRESET

    token = post_form(
        f"{BASE}/login/access-token",
        {"username": email, "password": password},
    )["access_token"]
    result = post_json(
        f"{BASE}/private/dev/apply-onboarding-preset",
        {"preset": preset, "confirm_week_setup": True},
        token,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
