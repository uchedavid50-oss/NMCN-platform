import json

import pytest

from app.core.config import settings
import app.api.admin_content as admin_content_module


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

CSV_CONTENT = (
    "subject,topic,stem,difficulty,explanation,option_a,option_b,option_c,option_d,correct_answer\n"
    "Anatomy,Cardiovascular,Which chamber pumps blood to the lungs?,easy,"
    "The right ventricle pumps deoxygenated blood to the lungs.,"
    "Right ventricle,Left ventricle,Right atrium,Left atrium,a\n"
)

BAD_CSV_ROW = (
    "subject,topic,stem,difficulty,explanation,option_a,option_b,option_c,option_d,correct_answer\n"
    "Anatomy,Cardiovascular,Incomplete row,easy,No options here,,,,,\n"
)


def test_non_admin_blocked_from_bulk_import(client, auth_headers):
    files = {"file": ("questions.csv", CSV_CONTENT.encode(), "text/csv")}
    response = client.post("/admin/content/bulk-import", files=files, headers=auth_headers)
    assert response.status_code == 403


def test_bulk_import_creates_subject_topic_and_question(client, admin_headers):
    files = {"file": ("questions.csv", CSV_CONTENT.encode(), "text/csv")}
    response = client.post("/admin/content/bulk-import", files=files, headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["created_count"] == 1
    assert body["skipped_rows"] == []

    subjects = client.get("/subjects").json()
    assert any(s["name"] == "Anatomy" for s in subjects)


def test_bulk_import_skips_malformed_rows_without_failing_whole_file(client, admin_headers):
    files = {"file": ("questions.csv", BAD_CSV_ROW.encode(), "text/csv")}
    response = client.post("/admin/content/bulk-import", files=files, headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["created_count"] == 0
    assert len(body["skipped_rows"]) == 1


@pytest.fixture()
def topic_id(client, admin_headers):
    subject = client.post("/subjects", json={"name": "Anatomy"}, headers=admin_headers).json()
    topic = client.post(
        "/topics", json={"subject_id": subject["id"], "name": "Cardiovascular"}, headers=admin_headers
    ).json()
    return topic["id"]


def test_generate_pending_questions_creates_review_queue_entries(
    client, admin_headers, monkeypatch, topic_id
):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(admin_content_module, "_call_gemini", lambda *args, **kwargs: VALID_GEMINI_JSON)

    doc = client.post(
        "/admin/content/documents/upload",
        files={"file": ("notes.txt", b"Cardiovascular anatomy notes.", "text/plain")},
        data={"document_type": "textbook"},
        headers=admin_headers,
    ).json()

    response = client.post(
        "/admin/content/generate",
        json={"document_id": doc["id"], "topic_id": topic_id, "count": 5},
        headers=admin_headers,
    )
    assert response.status_code == 200
    pending = response.json()
    assert len(pending) == 1
    assert pending[0]["status"] == "pending"

    # Not yet in the official bank — only visible in the pending queue.
    review_queue = client.get("/admin/content/pending", headers=admin_headers).json()
    assert len(review_queue) == 1


def test_approve_pending_question_publishes_to_official_bank(
    client, admin_headers, monkeypatch, topic_id
):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(admin_content_module, "_call_gemini", lambda *args, **kwargs: VALID_GEMINI_JSON)

    doc = client.post(
        "/admin/content/documents/upload",
        files={"file": ("notes.txt", b"Cardiovascular anatomy notes.", "text/plain")},
        data={"document_type": "textbook"},
        headers=admin_headers,
    ).json()
    pending = client.post(
        "/admin/content/generate",
        json={"document_id": doc["id"], "topic_id": topic_id, "count": 5},
        headers=admin_headers,
    ).json()

    approve = client.post(
        f"/admin/content/pending/{pending[0]['id']}/approve", headers=admin_headers
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"

    official_questions = client.get(f"/questions?topic_id={topic_id}", headers=admin_headers).json()
    assert len(official_questions) == 1


def test_reject_pending_question_never_reaches_official_bank(
    client, admin_headers, monkeypatch, topic_id
):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(admin_content_module, "_call_gemini", lambda *args, **kwargs: VALID_GEMINI_JSON)

    doc = client.post(
        "/admin/content/documents/upload",
        files={"file": ("notes.txt", b"Cardiovascular anatomy notes.", "text/plain")},
        data={"document_type": "textbook"},
        headers=admin_headers,
    ).json()
    pending = client.post(
        "/admin/content/generate",
        json={"document_id": doc["id"], "topic_id": topic_id, "count": 5},
        headers=admin_headers,
    ).json()

    reject = client.post(f"/admin/content/pending/{pending[0]['id']}/reject", headers=admin_headers)
    assert reject.status_code == 200
    assert reject.json()["status"] == "rejected"

    official_questions = client.get(f"/questions?topic_id={topic_id}", headers=admin_headers).json()
    assert len(official_questions) == 0
