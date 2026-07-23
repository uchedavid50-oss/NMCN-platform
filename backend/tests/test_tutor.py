import pytest

from app.core.config import settings
import app.api.tutor as tutor_module


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    last_call_kwargs = None

    @staticmethod
    def generate_content(**kwargs):
        _FakeModels.last_call_kwargs = kwargs
        return _FakeResponse("This is a mocked tutor explanation.")


class _FakeGenaiClient:
    def __init__(self, api_key=None):
        self.models = _FakeModels()


class _FlakyModels:
    """Fails with a transient 503 twice, then succeeds — simulates Gemini's
    real 'high demand' overload behavior to test our retry logic."""

    call_count = 0

    @staticmethod
    def generate_content(**kwargs):
        _FlakyModels.call_count += 1
        if _FlakyModels.call_count < 3:
            from google.genai.errors import APIError

            raise APIError(503, {"error": {"message": "high demand", "status": "UNAVAILABLE"}})
        return _FakeResponse("Recovered after retrying.")


class _FlakyGenaiClient:
    def __init__(self, api_key=None):
        self.models = _FlakyModels()


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


def test_tutor_blocks_if_question_never_attempted(client, auth_headers, monkeypatch, topic_with_question):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    _, question = topic_with_question

    response = client.post(
        "/tutor/ask",
        json={"question_id": question["id"], "message": "Why is the answer left ventricle?"},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_tutor_answers_after_attempt(client, auth_headers, monkeypatch, topic_with_question):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(tutor_module.genai, "Client", _FakeGenaiClient)
    topic, question = topic_with_question

    start = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers).json()
    option_id = question["options"][0]["id"]
    client.post(
        f"/practice/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": option_id},
        headers=auth_headers,
    )

    response = client.post(
        "/tutor/ask",
        json={"question_id": question["id"], "message": "Why is the answer left ventricle?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["reply"] == "This is a mocked tutor explanation."


def test_tutor_requires_api_key_configured(client, auth_headers, monkeypatch, topic_with_question):
    monkeypatch.setattr(settings, "google_api_key", "")
    _, question = topic_with_question

    response = client.post(
        "/tutor/ask",
        json={"question_id": question["id"], "message": "Explain this"},
        headers=auth_headers,
    )
    assert response.status_code == 500


def test_tutor_enforces_daily_rate_limit(client, auth_headers, monkeypatch, topic_with_question):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(tutor_module.genai, "Client", _FakeGenaiClient)
    monkeypatch.setattr(tutor_module, "DAILY_TUTOR_LIMIT", 2)
    topic, question = topic_with_question

    start = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers).json()
    option_id = question["options"][0]["id"]
    client.post(
        f"/practice/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": option_id},
        headers=auth_headers,
    )

    for _ in range(2):
        response = client.post(
            "/tutor/ask",
            json={"question_id": question["id"], "message": "Explain again"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    third = client.post(
        "/tutor/ask",
        json={"question_id": question["id"], "message": "One more please"},
        headers=auth_headers,
    )
    assert third.status_code == 429
    assert "limit" in third.json()["detail"].lower()


def test_study_plan_with_no_data_needs_no_api_key(client, auth_headers):
    """A brand-new student with zero practice history shouldn't need Gemini
    configured at all to get a response — no weak topics means no API call."""
    response = client.post("/tutor/study-plan", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["has_weak_topics"] is False
    assert body["weak_topic_names"] == []


def test_study_plan_identifies_weak_topic_and_generates_plan(
    client, auth_headers, monkeypatch, topic_with_question
):
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(tutor_module.genai, "Client", _FakeGenaiClient)
    topic, question = topic_with_question
    wrong_option_id = next(o["id"] for o in question["options"] if not o["is_correct"])

    # Answer the same question wrong across 3 separate practice attempts to
    # build up enough sample size (min 3) with sub-60% accuracy (0%).
    for _ in range(3):
        start = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers).json()
        client.post(
            f"/practice/{start['attempt_id']}/answer",
            json={"question_id": question["id"], "selected_option_id": wrong_option_id},
            headers=auth_headers,
        )

    response = client.post("/tutor/study-plan", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["has_weak_topics"] is True
    assert "cardiovascular" in body["weak_topic_names"][0].lower()
    assert body["plan"] == "This is a mocked tutor explanation."


def test_gemini_call_sets_thinking_config_to_avoid_truncation(
    client, auth_headers, monkeypatch, topic_with_question
):
    """Regression test for a real production bug: Gemini models 'think'
    before answering by default, and that invisible reasoning is billed
    against the same max_output_tokens budget as the visible response —
    without capping this, real responses came back truncated mid-sentence.
    This confirms every call explicitly sets a thinking config (using
    whichever parameter matches the current model — thinking_budget for
    2.5 series, thinking_level for 3.x), so this can't silently regress."""
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(tutor_module.genai, "Client", _FakeGenaiClient)
    topic, question = topic_with_question

    start = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers).json()
    option_id = question["options"][0]["id"]
    client.post(
        f"/practice/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": option_id},
        headers=auth_headers,
    )
    client.post(
        "/tutor/ask",
        json={"question_id": question["id"], "message": "Explain again"},
        headers=auth_headers,
    )

    config = _FakeModels.last_call_kwargs["config"]
    assert config.thinking_config is not None
    # The SDK stores this as an enum (e.g. ThinkingLevel.LOW) rather than the
    # raw string we passed in — compare by value, not identity, to avoid a
    # brittle test tied to the SDK's internal representation.
    # Since settings.gemini_model defaults to gemini-2.5-flash, this should use
    # thinking_budget (not thinking_level, which is 3.x-only and would error
    # on 2.5 models).
    assert config.thinking_config is not None
    assert config.thinking_config.thinking_level.value.lower() == "low"


def test_gemini_call_retries_transient_503_and_succeeds(
    client, auth_headers, monkeypatch, topic_with_question
):
    """Regression test for a real production issue: Gemini periodically
    returns 503 UNAVAILABLE ('high demand') during load spikes — a
    well-documented, widely-reported behavior, not specific to our API key.
    Confirms our retry-with-backoff actually recovers instead of failing
    the student's request on the first transient blip."""
    monkeypatch.setattr(settings, "google_api_key", "fake-key-for-tests")
    monkeypatch.setattr(tutor_module.genai, "Client", _FlakyGenaiClient)
    monkeypatch.setattr(tutor_module.time, "sleep", lambda seconds: None)  # skip real waiting in tests
    _FlakyModels.call_count = 0
    topic, question = topic_with_question

    start = client.post("/practice/start", json={"topic_id": topic["id"]}, headers=auth_headers).json()
    option_id = question["options"][0]["id"]
    client.post(
        f"/practice/{start['attempt_id']}/answer",
        json={"question_id": question["id"], "selected_option_id": option_id},
        headers=auth_headers,
    )

    response = client.post(
        "/tutor/ask",
        json={"question_id": question["id"], "message": "Explain again"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["reply"] == "Recovered after retrying."
    assert _FlakyModels.call_count == 3  # failed twice, succeeded on the third try
