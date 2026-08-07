import json

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
    return textbook


def _make_topic(client, admin_headers):
    subject = client.post("/subjects", json={"name": "Anatomy"}, headers=admin_headers).json()
    return client.post(
        "/topics", json={"subject_id": subject["id"], "name": "Cardiovascular"}, headers=admin_headers
    ).json()


def test_past_questions_count_starts_at_zero(client):
    response = client.get("/past-questions/count")
    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_past_questions_practice_empty_before_any_are_approved(client, auth_headers):
    response = client.get("/past-questions/practice", headers=auth_headers)
    assert response.status_code == 400


def test_approved_past_question_shows_up_in_dedicated_practice(
    client, admin_headers, auth_headers, monkeypatch
):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(textbooks_module, "_call_gemini", lambda *args, **kwargs: VALID_GEMINI_JSON)

    textbook = _make_folder_and_textbook(client, admin_headers)
    topic = _make_topic(client, admin_headers)

    generated = client.post(
        f"/textbooks/{textbook['id']}/generate-questions",
        json={"topic_id": topic["id"], "count": 5},
        headers=admin_headers,
    ).json()
    client.post(f"/admin/content/pending/{generated[0]['id']}/approve", headers=admin_headers)

    count_response = client.get("/past-questions/count")
    assert count_response.json()["count"] == 1

    practice_response = client.get("/past-questions/practice", headers=auth_headers)
    assert practice_response.status_code == 200
    questions = practice_response.json()
    assert len(questions) == 1
    assert any(o["is_correct"] for o in questions[0]["options"])


def test_regular_admin_content_is_included_in_past_questions(
    client, admin_headers, monkeypatch
):
    """The past-questions pool intentionally draws from the entire question
    bank, not just source == "past_questions" -- regular admin-generated
    content (e.g. the NCLEX/NMCN bulk generation pipeline) should show up
    here too, not just real historical exam questions."""
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")

    subject = client.post("/subjects", json={"name": "Pharmacology"}, headers=admin_headers).json()
    topic = client.post(
        "/topics", json={"subject_id": subject["id"], "name": "Analgesics"}, headers=admin_headers
    ).json()
    doc = client.post(
        "/admin/content/documents/upload",
        files={"file": ("notes.txt", b"Some textbook content.", "text/plain")},
        data={"document_type": "textbook"},
        headers=admin_headers,
    ).json()

    import app.api.admin_content as admin_content_module

    monkeypatch.setattr(admin_content_module, "_call_gemini", lambda *args, **kwargs: VALID_GEMINI_JSON)
    generated = client.post(
        "/admin/content/generate",
        json={"document_id": doc["id"], "topic_id": topic["id"], "count": 5},
        headers=admin_headers,
    ).json()
    client.post(f"/admin/content/pending/{generated[0]['id']}/approve", headers=admin_headers)

    count_response = client.get("/past-questions/count")
    assert count_response.json()["count"] == 1


def test_complete_past_questions_practice_updates_streak(client, auth_headers):
    response = client.post(
        "/past-questions/complete",
        json={"total_questions": 10, "correct_answers": 8},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["score_percentage"] == 80.0
    assert body["current_streak"] == 1
