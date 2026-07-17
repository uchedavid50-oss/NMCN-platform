import pytest


@pytest.fixture()
def sample_topic(client, admin_headers):
    subject = client.post("/subjects", json={"name": "Anatomy"}, headers=admin_headers).json()
    topic = client.post(
        "/topics", json={"subject_id": subject["id"], "name": "Cardiovascular"}, headers=admin_headers
    ).json()
    return topic


@pytest.fixture()
def sample_question(client, admin_headers, sample_topic):
    payload = {
        "topic_id": sample_topic["id"],
        "stem": "Which chamber pumps oxygenated blood to the body?",
        "difficulty": "easy",
        "explanation": "The left ventricle does this.",
        "options": [
            {"text": "Left atrium", "is_correct": False},
            {"text": "Left ventricle", "is_correct": True},
        ],
    }
    return client.post("/questions", json=payload, headers=admin_headers).json()


def test_subjects_list_is_public(client, sample_topic):
    response = client.get("/subjects")
    assert response.status_code == 200


def test_subject_create_requires_admin(client, auth_headers):
    response = client.post("/subjects", json={"name": "Should fail"}, headers=auth_headers)
    assert response.status_code == 403


def test_subject_create_works_for_admin(client, admin_headers):
    response = client.post("/subjects", json={"name": "Pharmacology"}, headers=admin_headers)
    assert response.status_code == 201


def test_question_create_rejects_single_option(client, admin_headers, sample_topic):
    payload = {
        "topic_id": sample_topic["id"],
        "stem": "Bad question",
        "difficulty": "easy",
        "explanation": "n/a",
        "options": [{"text": "Only one", "is_correct": True}],
    }
    response = client.post("/questions", json=payload, headers=admin_headers)
    assert response.status_code == 422


def test_question_create_rejects_two_correct_answers(client, admin_headers, sample_topic):
    payload = {
        "topic_id": sample_topic["id"],
        "stem": "Bad question",
        "difficulty": "easy",
        "explanation": "n/a",
        "options": [
            {"text": "A", "is_correct": True},
            {"text": "B", "is_correct": True},
        ],
    }
    response = client.post("/questions", json=payload, headers=admin_headers)
    assert response.status_code == 422


def test_question_read_blocked_for_regular_student(client, auth_headers, sample_question):
    """This is the exact gap discovered in Module 8: a student hitting the raw
    questions endpoint should never see the answer key."""
    response = client.get("/questions", headers=auth_headers)
    assert response.status_code == 403


def test_question_read_blocked_with_no_auth_at_all(client, sample_question):
    response = client.get("/questions")
    assert response.status_code == 401


def test_question_read_works_for_admin(client, admin_headers, sample_question):
    response = client.get("/questions", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert any("is_correct" in opt for q in body for opt in q["options"])


def test_subject_delete_cascades_to_topics_and_questions(client, admin_headers, sample_topic, sample_question):
    subject_id = None
    subjects = client.get("/subjects").json()
    for s in subjects:
        topics = client.get(f"/topics?subject_id={s['id']}").json()
        if any(t["id"] == sample_topic["id"] for t in topics):
            subject_id = s["id"]
            break
    assert subject_id is not None

    delete_response = client.delete(f"/subjects/{subject_id}", headers=admin_headers)
    assert delete_response.status_code == 204

    remaining_topics = client.get(f"/topics?subject_id={subject_id}").json()
    assert remaining_topics == []
