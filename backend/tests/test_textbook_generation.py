import json
import uuid

import app.api.textbooks as textbooks_module
from app.core.config import settings


VALID_GEMINI_JSON = json.dumps(
    {
        "questions": [
            {
                "stem": "Which chamber pumps oxygenated blood to the body?",
                "difficulty": "easy",
                "explanation": "The left ventricle does this.",
                "options": [
                    {"text": "Left atrium", "is_correct": False},
                    {"text": "Left ventricle", "is_correct": True},
                ],
            }
        ]
    }
)


def _make_folder_and_textbook(client, admin_headers):
    folder = client.post(
        "/textbooks/folders", json={"name": "Past Questions - Anatomy"}, headers=admin_headers
    ).json()
    textbook = client.post(
        f"/textbooks/folders/{folder['id']}/upload",
        data={"title": "2024 Past Questions"},
        files={"file": ("past2024.txt", b"Sample past exam question content.", "text/plain")},
        headers=admin_headers,
    ).json()
    return folder, textbook


def _make_topic(client, admin_headers):
    subject = client.post("/subjects", json={"name": "Anatomy"}, headers=admin_headers).json()
    topic = client.post(
        "/topics", json={"subject_id": subject["id"], "name": "Cardiovascular"}, headers=admin_headers
    ).json()
    return topic


def test_non_admin_cannot_generate_questions_from_textbook(client, auth_headers, admin_headers):
    _, textbook = _make_folder_and_textbook(client, admin_headers)
    topic = _make_topic(client, admin_headers)

    response = client.post(
        f"/textbooks/{textbook['id']}/generate-questions",
        json={"topic_id": topic["id"], "count": 5},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_generate_questions_from_textbook_creates_pending_entries(
    client, admin_headers, monkeypatch
):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(textbooks_module, "_call_gemini", lambda *args, **kwargs: VALID_GEMINI_JSON)

    _, textbook = _make_folder_and_textbook(client, admin_headers)
    topic = _make_topic(client, admin_headers)

    response = client.post(
        f"/textbooks/{textbook['id']}/generate-questions",
        json={"topic_id": topic["id"], "count": 5},
        headers=admin_headers,
    )
    assert response.status_code == 200
    pending = response.json()
    assert len(pending) == 1
    assert pending[0]["status"] == "pending"

    official = client.get(f"/questions?topic_id={topic['id']}", headers=admin_headers).json()
    assert len(official) == 0

    approve = client.post(f"/admin/content/pending/{pending[0]['id']}/approve", headers=admin_headers)
    assert approve.status_code == 200
    official_after = client.get(f"/questions?topic_id={topic['id']}", headers=admin_headers).json()
    assert len(official_after) == 1


def test_generate_questions_404_for_missing_textbook(client, admin_headers, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    topic = _make_topic(client, admin_headers)

    response = client.post(
        f"/textbooks/{uuid.uuid4()}/generate-questions",
        json={"topic_id": topic["id"], "count": 5},
        headers=admin_headers,
    )
    assert response.status_code == 404


def test_generate_questions_404_for_missing_topic(client, admin_headers, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    _, textbook = _make_folder_and_textbook(client, admin_headers)

    response = client.post(
        f"/textbooks/{textbook['id']}/generate-questions",
        json={"topic_id": str(uuid.uuid4()), "count": 5},
        headers=admin_headers,
    )
    assert response.status_code == 404
