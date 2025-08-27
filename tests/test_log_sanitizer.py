# tests/test_log_sanitizer.py
from utils.log_sanitizer import sanitize_headers, safe_log_api_call


def test_sanitize_headers_masks_authorization():
    headers = {
        "Authorization": "Bearer SECRET.TOKEN.VALUE",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    sanitized = sanitize_headers(headers)
    assert "Authorization" in sanitized
    # le token brut ne doit pas apparaître
    assert "SECRET.TOKEN.VALUE" not in str(sanitized["Authorization"])
    # la mention 'Bearer' peut rester, mais masquée (ex: 'Bearer ***' ou tronquée)
    assert "Bearer" in sanitized["Authorization"]


def test_safe_log_api_call_masks_token(capsys):
    # logger de test
    logs = []
    def fake_log(msg, enabled=True):
        if enabled:
            logs.append(str(msg))

    method = "POST"
    url = "https://api.topstepx.com/api/Order/place"
    headers = {"Authorization": "Bearer VERY.VERY.LONG.TOKEN", "Content-Type": "application/json"}
    payload = {"foo": "bar"}

    safe_log_api_call(method, url, headers, payload, fake_log, True, prefix="[TEST]")

    captured = "\n".join(logs)
    # le token brut ne doit pas apparaître dans les logs
    assert "VERY.VERY.LONG.TOKEN" not in captured
    assert "Authorization" in captured
