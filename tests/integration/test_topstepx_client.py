from types import SimpleNamespace
from urdu_exec_bot.services.topstepx_client import TopstepXClient


class FakeResp:
    def __init__(self, url):
        self.status_code = 200
        self._url = url
        self.content = b"{}"

    def json(self):
        return {"url": self._url}


def test_place_order_uses_endpoint(monkeypatch, settings_tmp):
    called = {}

    def fake_post(self, url, json=None, headers=None, timeout=None):
        called["url"] = url
        called["json"] = json
        return FakeResp(url)

    import requests
    monkeypatch.setattr(requests.Session, "post", fake_post, raising=True)

    c = TopstepXClient(settings_path=str(settings_tmp["settings_path"]))
    ok, data = c.place_order("GC", "BUY", 1, "MARKET", client_tag="t1")
    assert ok is True
    assert "/api/Order/place" in called["url"]
    assert data.get("url") == called["url"]
    assert called["json"]["instrument"] == "GC"
    assert called["json"]["side"] == "BUY"
    assert called["json"]["qty"] == 1
