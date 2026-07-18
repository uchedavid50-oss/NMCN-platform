import pytest


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


def test_badges_all_unearned_for_fresh_user(client, auth_headers):
    response = client.get("/achievements/badges", headers=auth_headers)
    assert response.status_code == 200
    badges = response.json()
    assert all(b["earned"] is False for b in badges)


def test_first_steps_badge_earned_after_answering(client, auth_headers, topic_with_question):
    topic, question = topic_with_question
    start = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers).json()
    client.post(
        f"/practice/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": question["options"][0]["id"]},
        headers=auth_headers,
    )

    badges = client.get("/achievements/badges", headers=auth_headers).json()
    first_steps = next(b for b in badges if b["id"] == "first_steps")
    assert first_steps["earned"] is True


def test_certificate_not_eligible_with_no_mocks(client, auth_headers):
    response = client.get("/achievements/certificate/eligibility", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["eligible"] is False
    assert "3 mock exams" in body["reason"]


def test_certificate_download_rejected_when_not_eligible(client, auth_headers):
    response = client.get("/achievements/certificate/download", headers=auth_headers)
    assert response.status_code == 403


def test_certificate_eligible_and_downloadable_after_three_good_mocks(
    client, auth_headers, topic_with_question
):
    topic, question = topic_with_question
    correct_id = question["options"][1]["id"]

    for _ in range(3):
        start = client.post(
            "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
        ).json()
        client.post(
            f"/mock/{start['attempt_id']}/answer",
            json={"question_id": question["id"], "selected_option_id": correct_id},
            headers=auth_headers,
        )
        client.post(f"/mock/{start['attempt_id']}/submit", headers=auth_headers)

    eligibility = client.get("/achievements/certificate/eligibility", headers=auth_headers).json()
    assert eligibility["eligible"] is True

    response = client.get("/achievements/certificate/download", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_certificate_not_eligible_with_low_average_score(client, auth_headers, topic_with_question):
    topic, question = topic_with_question
    wrong_id = question["options"][0]["id"]

    for _ in range(3):
        start = client.post(
            "/mock/start", json={"topic_id": topic["id"], "duration_minutes": 30}, headers=auth_headers
        ).json()
        client.post(
            f"/mock/{start['attempt_id']}/answer",
            json={"question_id": question["id"], "selected_option_id": wrong_id},
            headers=auth_headers,
        )
        client.post(f"/mock/{start['attempt_id']}/submit", headers=auth_headers)

    eligibility = client.get("/achievements/certificate/eligibility", headers=auth_headers).json()
    assert eligibility["eligible"] is False
    assert "70%" in eligibility["reason"]
