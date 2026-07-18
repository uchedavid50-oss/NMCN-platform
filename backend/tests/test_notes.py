import json
import uuid

import pytest

from app.core.config import settings
import app.api.notes as notes_module


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


VALID_GEMINI_JSON = json.dumps(
    {
        "questions": [
            {
                "stem": "What does the SA node do?",
                "difficulty": "medium",
                "explanation": "It's the heart's natural pacemaker.",
                "options": [
                    {"text": "Initiates the heartbeat", "is_correct": True},
                    {"text": "Filters blood", "is_correct": False},
                    {"text": "Produces insulin", "is_correct": False},
                    {"text": "Regulates breathing", "is_correct": False},
                ],
            },
            {
                "stem": "Malformed question with two correct answers",
                "difficulty": "medium",
                "explanation": "This one should be skipped.",
                "options": [
                    {"text": "A", "is_correct": True},
                    {"text": "B", "is_correct": True},
                ],
            },
        ]
    }
)


def test_upload_txt_note(client, auth_headers):
    response = client.post(
        "/notes/upload",
        files={"file": ("notes.txt", b"The SA node is the heart's natural pacemaker.", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "notes.txt"


def test_upload_rejects_unsupported_file_type(client, auth_headers):
    response = client.post(
        "/notes/upload",
        files={"file": ("notes.xyz", b"some content", "application/octet-stream")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_upload_rejects_empty_file(client, auth_headers):
    response = client.post(
        "/notes/upload",
        files={"file": ("notes.txt", b"   ", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_generate_questions_skips_malformed_and_keeps_valid(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(notes_module.genai, "Client", _make_fake_client(VALID_GEMINI_JSON))

    upload = client.post(
        "/notes/upload",
        files={"file": ("notes.txt", b"The SA node is the heart's natural pacemaker.", "text/plain")},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/notes/{upload['id']}/generate-questions",
        json={"count": 5},
        headers=auth_headers,
    )
    assert response.status_code == 200
    questions = response.json()
    # Only the well-formed question (exactly 1 correct option) should survive;
    # the malformed one (2 correct, only 2 options) is silently skipped.
    assert len(questions) == 1
    assert "SA node" in questions[0]["stem"]
    assert sum(1 for o in questions[0]["options"] if o["is_correct"]) == 1


def test_generated_questions_are_private_to_owner(client, auth_headers, make_user, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(notes_module.genai, "Client", _make_fake_client(VALID_GEMINI_JSON))

    upload = client.post(
        "/notes/upload",
        files={"file": ("notes.txt", b"Some notes content here.", "text/plain")},
        headers=auth_headers,
    ).json()

    _, other_token = make_user()
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = client.get(f"/notes/{upload['id']}/questions", headers=other_headers)
    assert response.status_code == 404


def test_generate_questions_requires_api_key_configured(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "")
    upload = client.post(
        "/notes/upload",
        files={"file": ("notes.txt", b"Some notes content.", "text/plain")},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/notes/{upload['id']}/generate-questions",
        json={"count": 5},
        headers=auth_headers,
    )
    assert response.status_code == 500


def test_generate_questions_404_for_nonexistent_note(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    response = client.post(
        f"/notes/{uuid.uuid4()}/generate-questions",
        json={"count": 5},
        headers=auth_headers,
    )
    assert response.status_code == 404
