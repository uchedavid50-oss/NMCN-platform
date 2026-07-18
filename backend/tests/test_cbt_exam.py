from datetime import timedelta

import pytest

from app.core.time import utcnow
from app.models.cbt_exam import CBTExamSession


@pytest.fixture()
def two_subjects_with_questions(client, admin_headers):
    subject1 = client.post("/subjects", json={"name": "Anatomy"}, headers=admin_headers).json()
    topic1 = client.post(
        "/topics", json={"subject_id": subject1["id"], "name": "Cardiovascular"}, headers=admin_headers
    ).json()
    q1 = client.post(
        "/questions",
        json={
            "topic_id": topic1["id"],
            "stem": "Which chamber pumps oxygenated blood to the body?",
            "difficulty": "easy",
            "explanation": "The left ventricle does this.",
            "options": [
                {"text": "Left atrium", "is_correct": False},
                {"text": "Left ventricle", "is_correct": True},
            ],
        },
        headers=admin_headers,
    ).json()

    subject2 = client.post("/subjects", json={"name": "Pharmacology"}, headers=admin_headers).json()
    topic2 = client.post(
        "/topics", json={"subject_id": subject2["id"], "name": "Analgesics"}, headers=admin_headers
    ).json()
    q2 = client.post(
        "/questions",
        json={
            "topic_id": topic2["id"],
            "stem": "Which drug class is paracetamol?",
            "difficulty": "easy",
            "explanation": "Paracetamol is an analgesic/antipyretic.",
            "options": [
                {"text": "Antibiotic", "is_correct": False},
                {"text": "Analgesic/antipyretic", "is_correct": True},
            ],
        },
        headers=admin_headers,
    ).json()

    return [q1, q2]


def test_start_cbt_exam_pulls_across_subjects(client, auth_headers, two_subjects_with_questions):
    response = client.post(
        "/cbt-exam/start", json={"question_count": 250, "duration_minutes": 240}, headers=auth_headers
    )
    assert response.status_code == 201
    body = response.json()
    # Only 2 questions exist total, even though 250 were requested — should
    # gracefully use however many are actually available.
    assert body["question_count"] == 2
    for q in body["questions"]:
        for option in q["options"]:
            assert "is_correct" not in option  # answers hidden, same integrity as mock exams


def test_free_tier_limited_to_one_cbt_exam(client, auth_headers, two_subjects_with_questions):
    first = client.post(
        "/cbt-exam/start", json={"question_count": 10, "duration_minutes": 60}, headers=auth_headers
    )
    assert first.status_code == 201

    second = client.post(
        "/cbt-exam/start", json={"question_count": 10, "duration_minutes": 60}, headers=auth_headers
    )
    assert second.status_code == 403
    assert "free tier" in second.json()["detail"].lower()


def test_active_subscriber_bypasses_cbt_exam_limit(client, make_user, two_subjects_with_questions):
    _, token = make_user(subscription_status="active")
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(3):
        response = client.post(
            "/cbt-exam/start", json={"question_count": 10, "duration_minutes": 60}, headers=headers
        )
        assert response.status_code == 201


def test_cbt_exam_submit_gives_breakdown_with_subject_names(
    client, auth_headers, two_subjects_with_questions
):
    q1, q2 = two_subjects_with_questions
    start = client.post(
        "/cbt-exam/start", json={"question_count": 250, "duration_minutes": 240}, headers=auth_headers
    ).json()
    session_id = start["session_id"]

    correct_q1 = next(o["id"] for o in q1["options"] if o["is_correct"])
    client.post(
        f"/cbt-exam/{session_id}/answer",
        json={"question_id": q1["id"], "selected_option_id": correct_q1},
        headers=auth_headers,
    )

    response = client.post(f"/cbt-exam/{session_id}/submit", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_questions"] == 2
    assert body["correct_answers"] == 1
    assert body["score_percentage"] == 50.0
    subject_names = {item["subject_name"] for item in body["breakdown"]}
    assert subject_names == {"Anatomy", "Pharmacology"}


def test_cbt_exam_answer_rejected_after_time_expires(
    client, auth_headers, two_subjects_with_questions, db_session
):
    q1, _ = two_subjects_with_questions
    start = client.post(
        "/cbt-exam/start", json={"question_count": 250, "duration_minutes": 240}, headers=auth_headers
    ).json()

    session = db_session.query(CBTExamSession).filter(CBTExamSession.id == start["session_id"]).first()
    session.expires_at = utcnow() - timedelta(minutes=1)
    db_session.commit()

    response = client.post(
        f"/cbt-exam/{start['session_id']}/answer",
        json={"question_id": q1["id"], "selected_option_id": q1["options"][0]["id"]},
        headers=auth_headers,
    )
    # Auto-finalized by the time this request is processed (same lazy-cleanup
    # pattern as mock exams, Module 17) — rejected either way.
    assert response.status_code == 400


def test_cbt_exam_ownership_enforced(client, auth_headers, make_user, two_subjects_with_questions):
    start = client.post(
        "/cbt-exam/start", json={"question_count": 250, "duration_minutes": 240}, headers=auth_headers
    ).json()

    _, other_token = make_user()
    other_headers = {"Authorization": f"Bearer {other_token}"}
    response = client.get(f"/cbt-exam/{start['session_id']}", headers=other_headers)
    assert response.status_code == 403
