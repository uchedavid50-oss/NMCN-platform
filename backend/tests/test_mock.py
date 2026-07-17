from datetime import timedelta

import pytest

from app.core.time import utcnow
from app.models.attempt import Attempt


@pytest.fixture()
def topic_with_question(client, admin_headers):
    subject = client.post("/subjects", json={"name": "Anatomy"}, headers=admin_headers).json()
    topic = client.post(
        "/topics", json={"subject_id": subject["id"], "name": "Cardiovascular"}, headers=admin_headers
    ).json()
    question = client.post(
        "/questions",
        json={
            "topic_id": topic["id"],
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
    return topic, question


def test_mock_answer_reveals_nothing(client, auth_headers, topic_with_question):
    topic, question = topic_with_question
    start = client.post(
        "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
    ).json()
    option_id = question["options"][0]["id"]

    response = client.post(
        f"/mock/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": option_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"received", "message"}


def test_mock_answer_can_be_changed_before_submit(client, auth_headers, topic_with_question):
    topic, question = topic_with_question
    start = client.post(
        "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
    ).json()
    wrong_id = next(o["id"] for o in question["options"] if not o["is_correct"])
    correct_id = next(o["id"] for o in question["options"] if o["is_correct"])

    client.post(
        f"/mock/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": wrong_id},
        headers=auth_headers,
    )
    client.post(
        f"/mock/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": correct_id},
        headers=auth_headers,
    )
    result = client.post(f"/mock/{start['attempt_id']}/submit", headers=auth_headers).json()
    assert result["correct_answers"] == 1
    assert result["score_percentage"] == 100.0


def test_mock_submit_reveals_full_breakdown(client, auth_headers, topic_with_question):
    topic, question = topic_with_question
    start = client.post(
        "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
    ).json()
    response = client.post(f"/mock/{start['attempt_id']}/submit", headers=auth_headers)
    assert response.status_code == 200
    breakdown = response.json()["breakdown"][0]
    assert breakdown["your_answer_id"] is None
    assert breakdown["is_correct"] is False
    assert "left ventricle" in breakdown["explanation"].lower()


def test_mock_answer_rejected_after_submit(client, auth_headers, topic_with_question):
    topic, question = topic_with_question
    start = client.post(
        "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
    ).json()
    client.post(f"/mock/{start['attempt_id']}/submit", headers=auth_headers)

    response = client.post(
        f"/mock/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": question["options"][0]["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_mock_answer_rejected_after_time_expires(client, auth_headers, topic_with_question, db_session):
    """As of Module 17, an expired attempt gets auto-finalized (via
    finalize_expired_mock_attempts) the moment it's next touched — so this now
    surfaces as "already submitted" rather than "time limit exceeded". Both are
    a 400 rejection; the message changed because the underlying behavior
    genuinely improved (the attempt now gets a real score instead of sitting
    open forever)."""
    topic, question = topic_with_question
    start = client.post(
        "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
    ).json()

    # Simulate time having already run out, without needing to actually wait 30 minutes.
    attempt = db_session.query(Attempt).filter(Attempt.id == start["attempt_id"]).first()
    attempt.expires_at = utcnow() - timedelta(minutes=1)
    db_session.commit()

    response = client.post(
        f"/mock/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": question["options"][0]["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "already been submitted" in response.json()["detail"].lower()


def test_free_tier_mock_limit_enforced(client, auth_headers, topic_with_question):
    topic, _ = topic_with_question
    for _ in range(3):
        response = client.post(
            "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
        )
        assert response.status_code == 201

    fourth = client.post(
        "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
    )
    assert fourth.status_code == 403
    assert "free tier" in fourth.json()["detail"].lower()


def test_active_subscription_bypasses_free_tier_limit(client, make_user, topic_with_question):
    topic, _ = topic_with_question
    _, token = make_user(subscription_status="active")
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(5):
        response = client.post(
            "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=headers
        )
        assert response.status_code == 201
