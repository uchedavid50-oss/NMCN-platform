from datetime import timedelta

import pytest

from app.core.time import utcnow
from app.models.attempt import Attempt
from app.services.mock_cleanup import finalize_expired_mock_attempts


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


def _expire_attempt(db_session, attempt_id):
    attempt = db_session.query(Attempt).filter(Attempt.id == attempt_id).first()
    attempt.expires_at = utcnow() - timedelta(minutes=1)
    db_session.commit()


def test_finalize_expired_mock_attempts_scores_unanswered_as_zero(
    client, auth_headers, topic_with_question, db_session
):
    topic, _ = topic_with_question
    start = client.post(
        "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
    ).json()
    attempt = db_session.query(Attempt).filter(Attempt.id == start["attempt_id"]).first()
    user_id = attempt.user_id
    _expire_attempt(db_session, start["attempt_id"])

    finalized_count = finalize_expired_mock_attempts(db_session, user_id)
    assert finalized_count == 1

    db_session.refresh(attempt)
    assert attempt.finished_at is not None
    assert attempt.score_percentage == 0.0  # never answered anything before abandoning


def test_finalize_is_scoped_to_the_correct_user(client, auth_headers, topic_with_question, db_session):
    topic, _ = topic_with_question
    start = client.post(
        "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
    ).json()
    _expire_attempt(db_session, start["attempt_id"])

    import uuid as uuid_module

    finalized_count = finalize_expired_mock_attempts(db_session, uuid_module.uuid4())
    assert finalized_count == 0  # a different (nonexistent) user's expired attempts shouldn't match


def test_status_check_auto_finalizes_expired_attempt(client, auth_headers, topic_with_question, db_session):
    topic, question = topic_with_question
    start = client.post(
        "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
    ).json()
    correct_id = next(o["id"] for o in question["options"] if o["is_correct"])
    client.post(
        f"/mock/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": correct_id},
        headers=auth_headers,
    )
    _expire_attempt(db_session, start["attempt_id"])

    # Never called /submit — this is exactly the "abandoned attempt" scenario.
    response = client.get(f"/mock/{start['attempt_id']}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["finished_at"] is not None
    assert body["is_expired"] is True

    attempt = client.get("/analytics/history", headers=auth_headers).json()
    matching = next(item for item in attempt["items"] if item["attempt_id"] == start["attempt_id"])
    assert matching["score_percentage"] == 100.0  # answered the one question correctly before abandoning
    assert matching["finished_at"] is not None


def test_analytics_history_finalizes_abandoned_attempts(
    client, auth_headers, topic_with_question, db_session
):
    topic, _ = topic_with_question
    start = client.post(
        "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
    ).json()
    _expire_attempt(db_session, start["attempt_id"])

    # Never touch /mock/* at all — just check analytics directly, simulating a
    # student who abandoned the exam and never came back to that attempt.
    history = client.get("/analytics/history", headers=auth_headers).json()
    matching = next(item for item in history["items"] if item["attempt_id"] == start["attempt_id"])
    assert matching["score_percentage"] == 0.0  # never answered anything
    assert matching["finished_at"] is not None

    overview = client.get("/analytics/overview", headers=auth_headers).json()
    assert overview["completed_attempts"] >= 1
