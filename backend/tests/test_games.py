from datetime import timedelta

import pytest

from app.core.time import utcnow
from app.models.speed_round import SpeedRoundResult
from app.services.streaks import compute_streak


@pytest.fixture()
def topic_with_question(client, admin_headers):
    subject = client.post("/subjects", json={"name": "Anatomy"}, headers=admin_headers).json()
    topic = client.post(
        "/topics", json={"subject_id": subject["id"], "name": "Cardiovascular"}, headers=admin_headers
    ).json()
    client.post(
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
    )
    return topic


def test_speed_round_start_open_to_regular_student(client, auth_headers, topic_with_question):
    """Like flashcards (Module 20), this deliberately shows is_correct — a
    casual game, not the graded exam engine."""
    response = client.get(
        f"/games/speed-round/start?topic_id={topic_with_question['id']}", headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert any(o["is_correct"] for o in body[0]["options"])


def test_speed_round_start_requires_auth(client, topic_with_question):
    response = client.get(f"/games/speed-round/start?topic_id={topic_with_question['id']}")
    assert response.status_code == 401


def test_speed_round_start_404_unknown_topic(client, auth_headers):
    import uuid

    response = client.get(f"/games/speed-round/start?topic_id={uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


def test_speed_round_submit_computes_score_and_streak(client, auth_headers):
    response = client.post(
        "/games/speed-round/submit",
        json={"total_questions": 10, "correct_answers": 7},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["score_percentage"] == 70.0
    assert body["current_streak"] == 1
    assert body["played_today"] is True


def test_speed_round_submit_rejects_impossible_score(client, auth_headers):
    response = client.post(
        "/games/speed-round/submit",
        json={"total_questions": 5, "correct_answers": 10},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_streak_zero_with_no_activity(client, auth_headers):
    response = client.get("/games/streak", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["current_streak"] == 0
    assert body["played_today"] is False


def test_compute_streak_counts_consecutive_days(db_session, make_user):
    user, _ = make_user()

    today = utcnow()
    for days_ago in (0, 1, 2):
        db_session.add(
            SpeedRoundResult(
                user_id=user.id,
                total_questions=5,
                correct_answers=3,
                score_percentage=60.0,
                played_at=today - timedelta(days=days_ago),
            )
        )
    db_session.commit()

    streak, played_today = compute_streak(db_session, user.id)
    assert streak == 3
    assert played_today is True


def test_compute_streak_breaks_on_gap(db_session, make_user):
    user, _ = make_user()

    today = utcnow()
    # Played today and 1 day ago, but skipped 2 days ago — streak should be 2, not 3.
    for days_ago in (0, 1, 3):
        db_session.add(
            SpeedRoundResult(
                user_id=user.id,
                total_questions=5,
                correct_answers=3,
                score_percentage=60.0,
                played_at=today - timedelta(days=days_ago),
            )
        )
    db_session.commit()

    streak, played_today = compute_streak(db_session, user.id)
    assert streak == 2
    assert played_today is True


def test_compute_streak_still_alive_if_played_yesterday_not_yet_today(db_session, make_user):
    user, _ = make_user()
    db_session.add(
        SpeedRoundResult(
            user_id=user.id,
            total_questions=5,
            correct_answers=3,
            score_percentage=60.0,
            played_at=utcnow() - timedelta(days=1),
        )
    )
    db_session.commit()

    streak, played_today = compute_streak(db_session, user.id)
    assert streak == 1
    assert played_today is False
