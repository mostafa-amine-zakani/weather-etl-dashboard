"""Tests Extract : mocks réseau, retries, erreurs."""
from unittest.mock import MagicMock

import pytest
import requests

from src.etl.extract import ExtractionError, fetch_city_weather


def make_session(responses):
    """Session mockée dont .get() rejoue une liste de comportements."""
    session = MagicMock()
    session.get.side_effect = responses
    return session


def ok_response(payload):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    return resp


VALID_PAYLOAD = {"hourly": {"time": ["2026-07-01T00:00"], "temperature_2m": [21.0]}}


def test_fetch_success():
    session = make_session([ok_response(VALID_PAYLOAD)])
    out = fetch_city_weather("Paris", 48.85, 2.35, session=session, retries=1)
    assert out["city"] == "Paris"
    assert "hourly" in out
    session.get.assert_called_once()


def test_fetch_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("src.etl.extract.time.sleep", lambda *_: None)
    session = make_session([
        requests.ConnectionError("boom"),
        ok_response(VALID_PAYLOAD),
    ])
    out = fetch_city_weather("Paris", 48.85, 2.35, session=session, retries=3)
    assert out["city"] == "Paris"
    assert session.get.call_count == 2


def test_fetch_fails_after_all_retries(monkeypatch):
    monkeypatch.setattr("src.etl.extract.time.sleep", lambda *_: None)
    session = make_session([requests.Timeout("t")] * 3)
    with pytest.raises(ExtractionError):
        fetch_city_weather("Paris", 48.85, 2.35, session=session, retries=3)
    assert session.get.call_count == 3


def test_fetch_rejects_payload_without_hourly(monkeypatch):
    monkeypatch.setattr("src.etl.extract.time.sleep", lambda *_: None)
    session = make_session([ok_response({"error": True})] * 2)
    with pytest.raises(ExtractionError):
        fetch_city_weather("Paris", 48.85, 2.35, session=session, retries=2)
