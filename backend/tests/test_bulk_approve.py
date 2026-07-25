import json

import app.api.admin_content as admin_content_module
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
            },
            {
                "stem": "What is the normal resting heart rate range for an adult?",
                "difficulty": "easy",
                "explanation": "60-100 beats per minute is normal for adults.",
                "options": [
                    {"text": "40-60 bpm", "is_correct": False},
                    {"text": "60-100 bpm", "is_correct": True},
                ],
            },
        ]
    }
)


def _make_topic_and_document(client, admin_headers):
    subject = client.post("/subjects", json={"name": "Anatomy"}, headers=admin_headers).json()
    topic = client.post(
        "/topics", json={"subject_id": subject["id"], "name": "Cardiovascular"}, headers=admin_headers
    ).json()
    doc = client.post(
        "/admin/content/documents/upload",
        files={"file": ("notes.txt", b"Cardiovascular anatomy notes.", "text/plain")},
        data={"document_type": "textbook"},
        headers=admin_headers,
    ).json()
    return topic, doc


def test_non_admin_cannot_bulk_approve(client, auth_headers):
    response = client.post("/admin/content/pending/approve-all", headers=auth_headers)
    assert response.status_code == 403


def test_bulk_approve_publishes_all_pending_to_official_bank(client, admin_headers, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(admin_content_module, "_call_gemini", lambda *args, **kwargs: VALID_GEMINI_JSON)

    topic, doc = _make_topic_and_document(client, admin_headers)
    client.post(
        "/admin/content/generate",
        json={"document_id": doc["id"], "topic_id": topic["id"], "count": 5},
        headers=admin_headers,
    )

    response = client.post("/admin/content/pending/approve-all", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["approved_count"] == 2

    official = client.get(f"/questions?topic_id={topic['id']}", headers=admin_headers).json()
    assert len(official) == 2

    remaining_pending = client.get("/admin/content/pending", headers=admin_headers).json()
    assert len(remaining_pending) == 0


def test_bulk_approve_scoped_to_single_topic(client, admin_headers, monkeypatch):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(admin_content_module, "_call_gemini", lambda *args, **kwargs: VALID_GEMINI_JSON)

    topic1, doc1 = _make_topic_and_document(client, admin_headers)
    subject2 = client.post("/subjects", json={"name": "Pharmacology"}, headers=admin_headers).json()
    topic2 = client.post(
        "/topics", json={"subject_id": subject2["id"], "name": "Analgesics"}, headers=admin_headers
    ).json()

    client.post(
        "/admin/content/generate",
        json={"document_id": doc1["id"], "topic_id": topic1["id"], "count": 5},
        headers=admin_headers,
    )
    client.post(
        "/admin/content/generate",
        json={"document_id": doc1["id"], "topic_id": topic2["id"], "count": 5},
        headers=admin_headers,
    )

    response = client.post(
        f"/admin/content/pending/approve-all?topic_id={topic1['id']}", headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["approved_count"] == 2

    remaining = client.get("/admin/content/pending", headers=admin_headers).json()
    assert len(remaining) == 2
    assert all(q["topic_id"] == topic2["id"] for q in remaining)
