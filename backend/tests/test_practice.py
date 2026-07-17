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


def test_practice_start_hides_answer_key(client, auth_headers, topic_with_question):
    topic, _ = topic_with_question
    response = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    for question in body["questions"]:
        assert "explanation" not in question
        for option in question["options"]:
            assert "is_correct" not in option


def test_practice_answer_reveals_correctness_and_explanation(client, auth_headers, topic_with_question):
    topic, question = topic_with_question
    start = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers).json()
    correct_option_id = next(o["id"] for o in question["options"] if o["is_correct"])

    response = client.post(
        f"/practice/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": correct_option_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is True
    assert body["correct_option_id"] == correct_option_id
    assert "left ventricle" in body["explanation"].lower()


def test_practice_answer_twice_is_rejected(client, auth_headers, topic_with_question):
    topic, question = topic_with_question
    start = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers).json()
    option_id = question["options"][0]["id"]

    first = client.post(
        f"/practice/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": option_id},
        headers=auth_headers,
    )
    assert first.status_code == 200

    second = client.post(
        f"/practice/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": option_id},
        headers=auth_headers,
    )
    assert second.status_code == 400


def test_practice_finish_computes_score(client, auth_headers, topic_with_question):
    topic, question = topic_with_question
    start = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers).json()
    correct_option_id = next(o["id"] for o in question["options"] if o["is_correct"])

    client.post(
        f"/practice/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": correct_option_id},
        headers=auth_headers,
    )
    response = client.post(f"/practice/{start['attempt_id']}/finish", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_questions"] == 1
    assert body["correct_answers"] == 1
    assert body["score_percentage"] == 100.0


def test_practice_answer_after_finish_is_rejected(client, auth_headers, topic_with_question):
    topic, question = topic_with_question
    start = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers).json()
    client.post(f"/practice/{start['attempt_id']}/finish", headers=auth_headers)

    response = client.post(
        f"/practice/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": question["options"][0]["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_practice_attempt_belongs_to_owner_only(client, auth_headers, make_user, topic_with_question):
    topic, _ = topic_with_question
    start = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers).json()

    _, other_token = make_user()
    other_headers = {"Authorization": f"Bearer {other_token}"}
    response = client.post(f"/practice/{start['attempt_id']}/finish", headers=other_headers)
    assert response.status_code == 403
