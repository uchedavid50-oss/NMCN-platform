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


def test_flashcards_require_authentication(client, topic_with_question):
    topic, _ = topic_with_question
    response = client.get(f"/flashcards?topic_id={topic['id']}")
    assert response.status_code == 401


def test_flashcards_open_to_regular_student_unlike_raw_questions(
    client, auth_headers, topic_with_question
):
    """The key design point of this module: /questions blocks students
    (Module 8), but /flashcards deliberately does not — showing the answer
    is the entire point of a flashcard, not a leak."""
    topic, _ = topic_with_question
    response = client.get(f"/flashcards?topic_id={topic['id']}", headers=auth_headers)
    assert response.status_code == 200


def test_flashcard_contains_front_and_answer_in_back(client, auth_headers, topic_with_question):
    topic, question = topic_with_question
    response = client.get(f"/flashcards?topic_id={topic['id']}", headers=auth_headers)
    cards = response.json()
    assert len(cards) == 1
    assert cards[0]["front"] == question["stem"]
    assert "left ventricle" in cards[0]["back"].lower()


def test_flashcards_404_for_unknown_topic(client, auth_headers):
    import uuid

    response = client.get(f"/flashcards?topic_id={uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404
