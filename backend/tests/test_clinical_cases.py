import json

import pytest

from app.core.config import settings
import app.api.clinical_cases as clinical_cases_module
import app.api.tutor as tutor_module


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, response_text):
        self._response_text = response_text

    def generate_content(self, **kwargs):
        return _FakeResponse(self._response_text)


def _make_fake_client(response_text):
    class _FakeGenaiClient:
        def __init__(self, api_key=None):
            self.models = _FakeModels(response_text)

    return _FakeGenaiClient


VALID_CASE_JSON = json.dumps(
    {
        "scenario": "A 68-year-old man presents with sudden-onset chest pain and shortness of breath.",
        "decision_points": [
            {
                "question": "What should you assess first?",
                "options": [
                    {"text": "Vital signs and pain characteristics", "is_correct": True, "rationale": "Establishes baseline urgency."},
                    {"text": "Ask about diet history", "is_correct": False, "rationale": "Not the priority in acute chest pain."},
                    {"text": "Discharge planning", "is_correct": False, "rationale": "Irrelevant at this acute stage."},
                ],
            },
            {
                "question": "Malformed decision point with two correct answers",
                "options": [
                    {"text": "A", "is_correct": True, "rationale": "x"},
                    {"text": "B", "is_correct": True, "rationale": "y"},
                ],
            },
        ],
    }
)


def test_generate_clinical_case_skips_malformed_decision_points(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(tutor_module.genai, "Client", _make_fake_client(VALID_CASE_JSON))

    response = client.post("/clinical-cases/generate", json={}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    # Only the well-formed decision point (exactly 1 correct option) survives.
    assert len(body["decision_points"]) == 1
    assert "assess first" in body["decision_points"][0]["question"].lower()
    assert sum(1 for o in body["decision_points"][0]["options"] if o["is_correct"]) == 1
    # Rationale is visible on every option — this is a teaching tool, same
    # design reasoning as flashcards (Module 20).
    assert all(o["rationale"] for o in body["decision_points"][0]["options"])


def test_clinical_case_requires_api_key(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "")
    response = client.post("/clinical-cases/generate", json={}, headers=auth_headers)
    assert response.status_code == 500


def test_clinical_case_is_private_to_owner(client, auth_headers, make_user, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(tutor_module.genai, "Client", _make_fake_client(VALID_CASE_JSON))

    case = client.post("/clinical-cases/generate", json={}, headers=auth_headers).json()

    _, other_token = make_user()
    other_headers = {"Authorization": f"Bearer {other_token}"}
    response = client.get(f"/clinical-cases/{case['id']}", headers=other_headers)
    assert response.status_code == 404


def test_complete_clinical_case_computes_score_and_streak(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(tutor_module.genai, "Client", _make_fake_client(VALID_CASE_JSON))

    case = client.post("/clinical-cases/generate", json={}, headers=auth_headers).json()
    response = client.post(
        f"/clinical-cases/{case['id']}/complete",
        json={"total_decisions": 1, "correct_decisions": 1},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["score_percentage"] == 100.0
    assert body["current_streak"] == 1


def test_complete_clinical_case_rejects_impossible_score(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(tutor_module.genai, "Client", _make_fake_client(VALID_CASE_JSON))

    case = client.post("/clinical-cases/generate", json={}, headers=auth_headers).json()
    response = client.post(
        f"/clinical-cases/{case['id']}/complete",
        json={"total_decisions": 1, "correct_decisions": 5},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_list_clinical_cases_scoped_to_owner(client, auth_headers, make_user, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(tutor_module.genai, "Client", _make_fake_client(VALID_CASE_JSON))

    client.post("/clinical-cases/generate", json={}, headers=auth_headers)

    _, other_token = make_user()
    other_headers = {"Authorization": f"Bearer {other_token}"}
    response = client.get("/clinical-cases", headers=other_headers)
    assert response.status_code == 200
    assert response.json() == []
