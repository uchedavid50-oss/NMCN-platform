# Module 1: Environment & Scaffolding — Run It

This spins up Postgres + FastAPI together in Docker. Run these on your own machine (Docker doesn't run inside this chat).

## Steps

1. Unzip this project, `cd` into `nmcn-platform/`.
2. Run:
   ```
   docker compose up --build
   ```
3. Wait for logs to show the backend has started (`Application startup complete`).
4. In a browser or with curl, check:
   - `http://localhost:8000/health` → should return `{"status":"ok"}`
   - `http://localhost:8000/health/db` → should return `{"status":"ok","db_result":1}`

If `/health/db` works, FastAPI successfully reached Postgres through Docker's internal network. That's Module 1 done.

## If something breaks

- `docker compose up --build` fails immediately → send me the exact error text, don't paraphrase it.
- Port 5432 or 8000 already in use → something else on your machine is using it (another Postgres install, another API). Stop that first, or tell me and we'll remap the port.
- `/health/db` times out or errors → almost always means `backend` started before `db` was ready. The `depends_on: condition: service_healthy` in docker-compose.yml is meant to prevent this — if it still happens, paste the backend container logs.

## Module 2: Auth — Run It

1. Since `requirements.txt` changed, rebuild: `docker compose up --build`
2. On startup, the `users` table is auto-created in Postgres (via SQLAlchemy `create_all` — fine for now, we'll switch to real Alembic migrations once the schema grows).
3. Test signup:
   ```
   curl -X POST http://localhost:8000/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password123"}'
   ```
   Should return the created user (id, email, role, subscription_status) — no password hash exposed.
4. Test login (note: this endpoint expects form data, not JSON, because of the OAuth2 password flow standard):
   ```
   curl -X POST http://localhost:8000/auth/login \
     -d "username=test@example.com&password=password123"
   ```
   Should return `{"access_token": "...", "token_type": "bearer"}`.
5. Test the protected route with the token from step 4:
   ```
   curl http://localhost:8000/auth/me -H "Authorization: Bearer <paste token here>"
   ```
   Should return the same user info.

If all three work, Module 2 is done.

## Module 3: Question Bank Foundation — Run It

Module 3 adds Subjects, Topics, Questions, and Options, with full CRUD APIs. It also introduces **Alembic** for real migrations — schema is no longer auto-created by SQLAlchemy on startup.

### ⚠️ One-time reset needed

Because we're switching from `create_all` to Alembic-managed migrations, and your existing `users` table was created the old way, reset your local database volume before continuing (this is throwaway dev data — your test signup/login accounts):

```
docker compose down -v
docker compose up --build
```

### Apply the migration

Once containers are up:

```
docker compose exec backend alembic upgrade head
```

This creates all five tables (`users`, `subjects`, `topics`, `questions`, `options`) in one migration. Confirm with:

```
docker compose exec db psql -U nmcn_user -d nmcn_db -c "\dt"
```

You should see all five tables listed.

### Test via Swagger UI

FastAPI auto-generates interactive docs. Open:

```
http://localhost:8000/docs
```

Test in this order (each depends on the previous existing):

1. **POST /subjects** — create a subject, e.g. `{"name": "Anatomy & Physiology"}`. Copy the returned `id`.
2. **POST /topics** — create a topic using that `subject_id`, e.g. `{"subject_id": "<paste>", "name": "Cardiovascular System"}`. Copy the returned `id`.
3. **POST /questions** — create a question using that `topic_id`, with at least 2 options and exactly one `is_correct: true`:
   ```json
   {
     "topic_id": "<paste>",
     "stem": "Which chamber of the heart pumps oxygenated blood to the body?",
     "difficulty": "easy",
     "explanation": "The left ventricle pumps oxygenated blood into the aorta and out to the body.",
     "options": [
       {"text": "Left atrium", "is_correct": false},
       {"text": "Left ventricle", "is_correct": true},
       {"text": "Right atrium", "is_correct": false},
       {"text": "Right ventricle", "is_correct": false}
     ]
   }
   ```
4. **GET /questions?topic_id=\<paste\>** — confirm the question and its options come back.
5. Try a bad payload — 2 correct answers, or only 1 option — and confirm you get a `422` validation error, not a silently broken question.
6. Try **PUT /questions/{id}** to replace it, and **DELETE /subjects/{id}** to confirm cascading delete removes its topics/questions/options too.

If all of that behaves, Module 3 is done.

### Known gap, flagged on purpose

These CRUD endpoints are currently **unauthenticated** — anyone with API access can create/edit/delete content. That's fine for solo local development, but must be closed off (admin-only) before this goes anywhere near production. Worth deciding whether that's part of Module 8 (Admin) or pulled forward sooner.

## Module 4: Quiz Engine — Practice Mode — Run It

Adds `attempts` and `attempt_answers` tables, and three new endpoints under `/practice`. Unlike Module 3, **these endpoints require authentication** — practice sessions belong to a specific logged-in user.

### Apply the new migration

```
docker compose up --build
docker compose exec backend alembic upgrade head
```

### Test via Swagger UI (`http://localhost:8000/docs`)

You'll need a logged-in user and at least one topic with questions in it (reuse what Module 3 testing created, or make fresh ones).

1. **POST /auth/login** with your test user, copy the `access_token`.
2. Click the green **Authorize** button at the top of the Swagger page, paste the token (just the token, Swagger adds "Bearer" itself), click Authorize. The lock icons next to protected routes should now look "closed."
3. **POST /practice/start** with `{"topic_id": "<your topic id>"}`. Response should list all questions for that topic — notice the options do **not** include `is_correct`, and there's no `explanation` field. Copy the `attempt_id`.
4. **POST /practice/{attempt_id}/answer** with a `question_id` and a `selected_option_id` from that question's options. Response should return `is_correct`, the `correct_option_id`, and the `explanation` — instantly.
5. Try submitting the same `question_id` again in the same attempt — should get a `400` ("already answered").
6. **POST /practice/{attempt_id}/finish** — should return a score summary (`total_questions`, `correct_answers`, `score_percentage`).
7. Try calling `/answer` again after finishing — should get a `400` ("already finished").
8. **GET /practice/{attempt_id}** — should return the same summary even after finishing.

If all of that behaves, Module 4 is done.

## Module 5: Quiz Engine — Mock Exam Mode — Run It

Adds timed mock exams under `/mock`. Key differences from practice mode: answers give **no instant feedback** (you can change your answer before submitting, but you never learn if it's right until the whole exam is submitted), the exam has a real time limit, and the full answer breakdown only appears after **POST /mock/{attempt_id}/submit**.

### Apply the new migration

```
docker compose up --build
docker compose exec backend alembic upgrade head
```

### Test via Swagger UI

Make sure you're still logged in and Authorized (or re-login if your token expired). Use the same topic/questions from Module 4, or create fresh ones.

1. **POST /mock/start** with `{"topic_id": "<your topic id>", "duration_minutes": 30}`. Response should include `expires_at`, and questions with **no `is_correct`** — same hiding behavior as practice mode. Copy `attempt_id`.
2. **POST /mock/{attempt_id}/answer** with a `question_id`/`selected_option_id`. Response should say `"received": true` — notice it does **not** tell you if you were right.
3. Submit the same question again with a **different** `selected_option_id` — should succeed and say `"Answer updated"` (you're allowed to change your mind before submitting, unlike practice mode).
4. **GET /mock/{attempt_id}** — check `time_remaining_seconds` is counting down and `is_expired` is `false`.
5. **POST /mock/{attempt_id}/submit** — now you should get the full breakdown: each question, what you picked, the correct answer, and the explanation, plus your overall score.
6. Try calling `/answer` again on the same attempt — should get a `400` ("already submitted").

### Known gap, flagged on purpose

There's no background job auto-submitting an exam the moment time runs out — the time limit is only enforced when the student tries to submit an answer *after* `expires_at` (they'll get rejected), but a client that never calls `/answer` again after time runs out could theoretically leave an attempt open indefinitely. Fine for MVP; would need a scheduled task or a "submit on expiry" check in Module 7 (Analytics) or during frontend integration.

If all the above behaves, Module 5 is done.

## Module 6: Payments/Subscriptions — Run It

Adds a `subscriptions` table, three endpoints under `/payments` (`initialize`, `webhook`, `subscription`), and a free-tier gate on mock exams (max 3 mock exams unless `subscription_status` is `active`).

### Get a free Paystack test key (no real money involved)

1. Sign up at paystack.com if you haven't already — it's free.
2. In the dashboard, make sure you're in **Test Mode** (toggle, usually top-left).
3. Go to Settings → API Keys & Webhooks, copy the **Test Secret Key** (starts with `sk_test_`).
4. Create a new file `backend/.env` (copy from `.env.example`) and paste your key in:
   ```
   PAYSTACK_SECRET_KEY=sk_test_your_actual_key_here
   ```
5. Rebuild so the container picks up the new env var:
   ```
   docker compose down
   docker compose up --build
   docker compose exec backend alembic upgrade head
   ```

### Test initialization (real call to Paystack)

1. Still logged in/Authorized in Swagger, expand **POST /payments/initialize**, "Try it out", body:
   ```json
   {"plan": "premium_monthly"}
   ```
2. Execute — should return an `authorization_url` and a `reference`. This is a real Paystack API call, so if your key is wrong or missing you'll get a clear error here.
3. Open that `authorization_url` in a browser — it's Paystack's real test checkout page. Pay using a Paystack test card: card number `4084084084084081`, any future expiry date, CVV `408`, PIN `0000`, OTP `123456`. This does not charge real money — it's sandbox mode.

### Simulate the webhook locally

Paystack's servers can't reach `localhost` on your machine directly, so completing the test checkout above won't automatically hit your `/payments/webhook` unless you've set up a public tunnel (e.g. ngrok) and registered it in the Paystack dashboard — optional, and worth doing later before real deployment, but not required to prove the logic works now.

For now, simulate the webhook call yourself using the `reference` from step 2 above. In a Python shell (or a quick script), compute a valid signature and send it:

```python
import hashlib, hmac, json, httpx

secret = "sk_test_your_actual_key_here"  # same key as in backend/.env
reference = "nmcn_xxxxxxxx"  # paste the reference from /payments/initialize

payload = {"event": "charge.success", "data": {"reference": reference}}
body = json.dumps(payload).encode()
signature = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()

r = httpx.post(
    "http://localhost:8000/payments/webhook",
    content=body,
    headers={"x-paystack-signature": signature, "Content-Type": "application/json"},
)
print(r.status_code, r.text)
```

Should print `200 {"received":true}`.

### Confirm the subscription activated

**GET /payments/subscription** in Swagger — should now show `"status": "active"` and an `expires_at` about 30 days out.

### Confirm the free-tier gate

1. Before subscribing (or with a second, non-subscribed test user), call **POST /mock/start** repeatedly against a topic with questions — after 3 total mock exams, the 4th should return a `403` pointing you to subscribe.
2. After a user's `subscription_status` becomes `active` (per the webhook above), confirm they can start a 4th, 5th, etc. mock exam without being blocked.

If all of that behaves, Module 6 is done.

## Module 7: Analytics — Run It

Adds four read-only endpoints under `/analytics`, built entirely on data you've already generated in Modules 4-6 — no new database tables, no new migration needed.

### Test via Swagger UI

Still logged in/Authorized from before. All four require auth.

1. **GET /analytics/overview** — should show your total attempts, completed attempts, practice vs mock counts, and overall accuracy across everything you've answered so far.
2. **GET /analytics/by-topic** — should show a row for the "Cardiovascular System" topic (or whatever you've been testing with), with `total_answered`, `correct_answered`, and `accuracy_percentage`, sorted weakest-first.
3. **GET /analytics/weak-topics** — by default, only flags a topic as weak if you've answered at least 3 questions in it AND your accuracy is below 60%. With only 1-2 questions answered so far, this will likely return an **empty list** — that's correct behavior, not a bug (not enough data yet to call it "weak" rather than a fluke).
4. **GET /analytics/history** — should list your past attempts (practice + mock) with scores and timestamps, newest first. Try the `mode=mock` query parameter to filter to just mock exams.

### To properly test weak-topic detection

Since it needs real signal, you'll want at least 3 answered questions in one topic with a sub-60% accuracy. Easiest way: add 2 more questions to your existing topic (**POST /questions**, same topic_id), start a fresh practice attempt, and deliberately answer at least one wrong. Then re-check `/analytics/weak-topics` — it should now show that topic.

If all of the above behaves as expected, Module 7 is done.

## Module 8: Admin (minimal) — Run It

This closes the "unauthenticated CRUD" gap flagged all the way back in Module 3 — and fixes something we hadn't caught until now: `GET /questions` was returning `is_correct` and `explanation` to **anyone**, meaning a student could just call the raw API and see every answer key, completely bypassing practice/mock mode. That's now locked down too.

**What changed:**
- `Subjects`/`Topics`: only **writes** (POST/PUT/DELETE) now require an admin role. Reads stay public — subject/topic names aren't sensitive.
- `Questions`: **everything**, including reads, now requires an admin role, since the response includes the answer key.
- No database changes, no new migration — this reuses the `role` column that's existed on `users` since Module 2.

### Promote your test user to admin

There's no self-service "become an admin" endpoint on purpose — that would be a security hole. For now, promote directly in the database:

```
docker compose exec db psql -U nmcn_user -d nmcn_db -c "UPDATE users SET role='admin' WHERE email='test@example.com';"
```

You do **not** need to log in again — your existing token still works, since the role is checked fresh from the database on every request, not stored in the token itself.

### Test the lockdown

1. **Before promoting** (or using a second, non-admin test user): try **POST /questions** or **GET /questions** — should now return `403` ("Admin access required") instead of succeeding.
2. Run the `psql` command above to promote your user.
3. Retry the same calls — should now succeed normally, exactly like before.
4. Confirm **GET /subjects** and **GET /topics** still work **without** being admin (create a second non-admin user to check, or just note that a 403 here would mean something's wrong — these should stay public).

If all of that behaves, Module 8 is done — and with it, the full MVP scope from the original charter (Section 6) is built.

## Module 9: Frontend Foundation — Run It

Adds a Next.js frontend under `frontend/` — a landing page, signup, login, and a protected dashboard, wired to your real backend. This is the first module you'll actually see in a normal browser, not just Swagger.

### Design direction (for context, not something to test)

The look is a "clinical chart" aesthetic — a pulse-line motif representing exam readiness, Fraunces for headings, IBM Plex Sans/Mono for body and data. Deliberately not another cream-and-terracotta or dark-mode-neon SaaS template.

### First-time setup

Since I can't run `npm install` from my side (no network access in my environment), you'll do it once yourself:

```
cd frontend
npm install
cd ..
```

This will take a minute or two — it's downloading React, Next.js, and Tailwind.

### Running it

The `frontend` service is now in `docker-compose.yml` alongside `backend` and `db`. Bring everything up together:

```
docker compose up --build
```

Then open **`http://localhost:3000`** in your browser (not 8000 — that's still the backend/Swagger).

### Test the flow

1. You should see the landing page with the pulse-line animation drawing itself in once, headline, and two buttons.
2. Click **"Create your account"**. Sign up with a **new** email (not `test@example.com` — that one's already registered from backend testing). Use a real-looking email and an 8+ character password.
3. On success, you should land on `/dashboard`, showing your email, role (`student`), and subscription status (`free`).
4. Click **"Log out"** — should return you to the login page.
5. Log back in with the same credentials — should land on `/dashboard` again.
6. Try visiting `http://localhost:3000/dashboard` directly in a new incognito/private browser tab (no login) — should redirect you to `/login` instead of showing the dashboard. This confirms the protected-route check works.

If all of that behaves, Module 9 is done.

### Known gap, flagged on purpose

Auth state lives in `localStorage` and is checked client-side only — there's no server-side route protection yet (a technically savvy user could briefly see a flash of the dashboard shell before the redirect kicks in, though they can't actually fetch real data without a valid token). Fine for MVP; worth hardening with proper middleware-based auth before this goes to production.

## Module 10: Frontend — Subjects, Topics, and Practice Mode UI — Run It

Adds `/subjects`, `/subjects/[subjectId]`, and `/practice/[topicId]` pages, plus a "Start practicing" link on the dashboard. This is the actual product experience — no code changes needed to the backend, just new frontend pages calling endpoints that already exist.

### Run it

No rebuild needed if containers are already running — Next.js hot-reloads. If they're not running:
```
docker compose up
```

### Test the flow

1. Log in, land on `/dashboard`, click **"Start practicing"**.
2. You should see your subject(s) listed (e.g. "Anatomy & Physiology" from earlier testing). Click one.
3. You should see the topic(s) under it (e.g. "Cardiovascular System"). Click one.
4. This starts a practice attempt — you should see "Question 1 of N" and the question stem with clickable options.
5. Click an option — it should lock in, show either a teal highlight (correct answer) or coral highlight (if you picked wrong), plus the explanation text and a "Next question"/"Finish" button.
6. Click through to the end — the last question's button should say "Finish" instead of "Next question".
7. On finishing, you should see a summary screen with your score percentage and a link back to subjects.

### Known gap, flagged on purpose

If you only have 1 question in your topic (likely, from earlier testing), you won't get to see the "Next question" button in action — only "Finish" immediately. Worth adding 2-3 more questions to the same topic via Swagger (as admin) if you want to see the full multi-question flow before moving on.

If all of the above behaves, Module 10 is done.

## What's next (Module 11: Frontend — Mock Exam UI)

Same idea as this module, but for the timed mock exam flow — a visible countdown timer, no instant feedback per question, and the full breakdown only shown after submitting.

## Module 11: Mock Exam UI — Run It

Adds a full timed exam experience at `/mock/[topicId]`: a live countdown, a question navigator strip (dots showing answered/unanswered/current), free navigation between questions with no correctness feedback, and a complete breakdown only after submitting. Also auto-submits if the timer runs out.

### No rebuild needed

Same as Module 10 — just new pages and API calls, no new packages. Restart the frontend if hot reload doesn't pick it up:
```
docker compose restart frontend
```

### Test the flow

1. From a topic's page (`/subjects/{id}`), you should now see **two** buttons per topic: "Practice" and "Mock exam". Click **"Mock exam"**.
2. Should start a 30-minute timed exam, showing "Question 1 of N" and a countdown timer in the top right (turns coral under 60 seconds remaining).
3. Click an answer — it should highlight teal, but **no explanation or correctness appears** (this is the key difference from practice mode).
4. Use the dot navigator strip below the timer — click a different dot to jump directly to that question. Answered questions should show as filled teal dots.
5. Use **Previous**/**Next** to move between questions without answering every one — mock mode allows skipping.
6. On the last question, the right-hand button changes to **"Submit exam"**. There's also a smaller "Submit exam now" link below if you want to submit early from any question.
7. After submitting, you should see the score, then a full per-question breakdown: your answer, the correct answer (only shown if you got it wrong), and the explanation.

### Testing the free-tier limit (optional, since you may already be subscribed)

If your test account still has `subscription_status: free`, and you've already used 3+ mock exams across earlier testing, starting a new one should show a clear message about the free-tier limit instead of a raw error. If you're already `active` from Module 6 testing, you won't see this — that's expected, not a bug.

### Known gap, flagged on purpose

The countdown timer runs entirely in the browser. If a student closes the tab and comes back after the real deadline (tracked server-side via `expires_at`), the frontend timer resets to whatever's left according to the server, but there's no server-side auto-submission — this mirrors the backend gap flagged back in Module 5.

If all of the above behaves, Module 11 is done — and with it, every core student-facing flow (auth, browsing, practice, mock exams) is usable end to end, not just through Swagger.

## What's next

At this point every MVP feature from the original charter has both a backend and a frontend. Worth a deliberate conversation about priorities from here: hardening known gaps (abandoned attempts, timer edge cases, automated tests), P1/P2 features (analytics dashboard UI, flashcards, dark mode), the AI Tutor, or getting this in front of real nursing students for feedback before building further.

## Module 12: Automated Backend Tests — Run It

Adds a `pytest` suite covering auth, question-bank admin-gating (including the exact answer-key leak found in Module 8), practice mode, mock exam mode (including simulating time expiry without waiting 30 real minutes), and payment webhook signature verification (using a fake key — no real Paystack calls happen in tests).

Tests run against a **separate database** (`nmcn_test_db`, auto-created on first run) so they never touch your real dev data, and each test runs inside its own transaction that's rolled back afterward — tests can't leave leftover data behind or interfere with each other.

### Install the new dependency and run

```
docker compose up --build
docker compose exec backend pytest -v
```

The `-v` shows each test name as it runs. You should see roughly 25-30 tests, almost all passing.

### What to look at

- **Green (`PASSED`)**: the behavior it's checking works as expected.
- **Red (`FAILED`)**: something regressed, or the test itself has a bug. Either way, worth reading the assertion error — that's pytest telling you exactly what it expected vs. what it got.

Pay particular attention to `test_question_read_blocked_for_regular_student` in `test_questions_admin_gating.py` — this is a direct, permanent regression test for the answer-key leak we found and fixed in Module 8. If this test ever goes red in the future, it means that protection broke again.

### Why this matters going forward

From here on, before believing any change "works," you can run `docker compose exec backend pytest` instead of manually re-clicking through Swagger every time. It won't replace testing the frontend by hand, but it means backend regressions get caught in seconds instead of requiring a full manual walkthrough — exactly the kind of safety net that would have caught the CORS-missing issue or the CSV/JSON casing bugs faster than we found them by hand.

### Known gap, flagged on purpose

This suite only covers the backend. There's no frontend testing yet (e.g. Playwright/Cypress for the browser flows) — worth adding once the product is more stable and changing less rapidly.

If the suite runs and mostly passes, Module 12 is done.

## What's next

With tests in place as a safety net, worth revisiting: P1/P2 features (analytics dashboard UI, flashcards, dark mode), the AI Tutor, hardening remaining known gaps (server-side mock exam expiry, abandoned attempt cleanup), or pausing to get real nursing students using this for feedback.

## Module 13: Analytics Dashboard UI — Run It

Adds a real `/analytics` page in the browser, pulling from the four endpoints built back in Module 7 (`overview`, `by-topic`, `weak-topics`, `history`) — no new backend work needed, this module is entirely frontend.

### No rebuild needed

Just new pages and API calls again. `docker compose restart frontend` should be enough; full rebuild only if hot reload doesn't pick it up.

### Test the flow

1. From your dashboard, click **"View my progress"** (new button next to "Start practicing").
2. You should see four stat cards: overall accuracy, questions answered, practice sessions, mock exams.
3. If you have at least one topic with 3+ answered questions below 60% accuracy, you'll see a **"Needs work"** section highlighted in coral. If not, this section just won't render — that's correct, not a bug (matches the backend's minimum-sample-size guard from Module 7).
4. A **"By topic"** section should show a horizontal bar per topic — teal if accuracy is 60%+, coral if below.
5. A **"Recent activity"** list should show your last 10 attempts, tagged practice/mock, with score and date.
6. If you have zero practice/mock data on whichever account you're testing with, you should instead see a friendly empty state pointing you to start practicing — not a blank page or an error.

If all of that behaves, Module 13 is done.

## What's next

Analytics dashboard is live. From here: flashcards/dark mode (P2 charter features), the AI Tutor, remaining known gaps (server-side mock expiry, stale attempt cleanup, the `datetime.utcnow()` deprecation cleanup), or — genuinely worth considering now that the full loop exists end to end — getting real nursing students to actually use this and tell you what's missing before building further.

## Module 14: AI Tutor (Foundation) — Run It

Adds a scoped "explain this further" tutor, using Google's Gemini API, attached to practice mode. Deliberately **not** open-ended chat — the tutor only discusses a question after the student has actually submitted an answer for it (practice or mock). This closes off the same class of backdoor we found and fixed in Module 8 (answer-key access without practicing), just via a new route.

**Note:** this originally used Anthropic's Claude API. Switched to Google Gemini instead since it has a genuine free tier (no credit card, no billing setup) — the right call for an MVP with no revenue yet. Two honest trade-offs that came with the switch: free-tier rate limits are real (roughly 10-1,000 requests/day depending on model — fine for testing and early beta, not for scale), and Google may use free-tier prompts to improve their models (low-risk here since the content is just nursing exam Q&A, not sensitive personal data, but worth knowing).

### Get a free Gemini API key (genuinely free — no credit card, no billing)

1. Go to Google AI Studio (aistudio.google.com), sign in with a Google account.
2. Click "Get API key" → "Create API key." No credit card or billing setup required for the free tier.
3. Add it to `backend/.env` (same file as your Paystack key):
   ```
   GOOGLE_API_KEY=your-real-gemini-api-key-here
   ```
4. Rebuild:
   ```
   docker compose up --build
   ```

### Run the automated tests first (no API cost — these mock the Gemini call entirely)

```
docker compose exec backend pytest -v tests/test_tutor.py
```

Should show 3 passing tests, confirming the gating logic works without spending a single real API call.

### Test the real thing in the browser

1. Go to a topic, start **Practice**, answer a question (right or wrong — either works).
2. In the feedback panel, below the explanation, you should see **"Still unsure? Ask the tutor"** with a text input.
3. Type a genuine follow-up question (e.g., "why not the right atrium?") and press Enter or click Ask.
4. After a few seconds, a real Gemini-generated explanation should appear, grounded in that specific question's topic and correct answer — not a generic response.
5. Try asking something unrelated to nursing (e.g., "what's the capital of France?") — the tutor should gently redirect back to exam content rather than just answering it, per the system prompt.

### Confirm the gate works (optional but worth it once)

Using a fresh question the student hasn't answered yet, try calling `POST /tutor/ask` directly via Swagger with that question's ID — should get a `403` telling you to attempt it first, exactly like the automated test confirms.

If the real API call in step 4 returns a sensible, grounded explanation, Module 14's foundation is done.

### Known gaps, flagged on purpose

- No per-user rate limiting on tutor calls yet — a student could exhaust the free-tier daily quota by spamming follow-up questions, at which point the API starts returning 429 errors (which would currently surface as a generic "Tutor request failed" message). Worth adding before real users at scale.
- Each tutor question is stateless (no memory of earlier follow-ups within the same conversation) — fine for a first version, but a real "conversation" would need to pass prior messages back to the API.
- This only covers "explain this question further" — the charter's other AI Tutor goals (recommend study plans, proactively identify weak topics) aren't built yet; those could lean on the analytics data from Module 7 in a future session.

## What's next

The AI Tutor foundation is live. From here: expanding the tutor (rate limiting, conversation memory, weak-topic-aware study plan recommendations), P2 features (flashcards, dark mode), remaining tech debt, or pausing for real student feedback.

## Module 15: Tutor Rate Limiting — Run It

Closes the "no rate limiting" gap flagged in Module 14. Adds a `tutor_requests` table logging each successful tutor call, and caps students at **20 tutor questions per rolling 24 hours**. Only successful calls count against the limit — a failed Gemini call (timeout, API error) doesn't cost the student one of their questions.

### Apply the new migration

```
docker compose up --build
docker compose exec backend alembic upgrade head
```

### Run the automated tests

```
docker compose exec backend pytest -v tests/test_tutor.py
```

Should show 4 passing tests now (one new: `test_tutor_enforces_daily_rate_limit`, which temporarily lowers the limit to 2 for the test itself rather than actually sending 21 requests).

### Test it for real (optional — costs a few real API calls)

Ask the tutor a genuine question in the browser 20+ times in a row on the same account. The 21st should return a clear message about the daily limit instead of a real answer. Not required to consider this module done, since the automated test already proves the logic — only do this if you want to see the real UI behavior when the limit hits (currently it'll show whatever generic error text the frontend displays for a failed request; polishing that message is a nice-to-have, not required).

If the tests pass, Module 15 is done.

## What's next

Tutor is now both grounded and rate-limited. From here: conversation memory for the tutor, weak-topic-aware study plans, P2 features (flashcards, dark mode), remaining tech debt (server-side mock expiry, stale attempt cleanup, `datetime.utcnow()` deprecation), or — still genuinely worth doing — getting real nursing students using this end to end.

## Module 16: `datetime.utcnow()` Cleanup — Run It

Pure refactor, no new features, no migration, no new dependency. Replaces every call to the deprecated `datetime.utcnow()` in our own code with a single shared helper (`app/core/time.py`), across `security.py`, all four models with timestamp columns, and `practice.py`/`mock.py`/`payments.py`/`tutor.py`.

**Design decision worth understanding:** the helper still returns a **naive** datetime (no timezone attached) — exactly matching what `datetime.utcnow()` used to return. It would have been tempting to switch everything to timezone-aware datetimes while we were in here, but every DateTime column in this app is naive, and mixing aware/naive datetimes is a real source of silent bugs (it's the same category of mistake that broke the mock-exam countdown timer in Module 11, just Python-side instead of JS-side this time). The helper exists so there's exactly one place to change if this app ever does move to full timezone-awareness later.

### No rebuild strictly needed

No new dependencies or migrations — this is pure code. `docker compose restart backend` should be enough, though a full rebuild won't hurt.

### Run the full test suite

```
docker compose exec backend pytest -v
```

Should still show all tests passing (32 backend tests plus the 4 tutor tests = 36 total at this point). The **absence** of `datetime.utcnow() is deprecated` warnings from our own files is the actual thing to check for — you'll likely still see one from `python-jose` itself (a third-party dependency's internal code, not something we can fix from our side without switching JWT libraries, which isn't worth doing over a warning).

If all tests still pass and the deprecation warnings from our own code are gone, Module 16 is done.

## What's next

Tech debt cleanup complete for this item. Remaining known gaps: server-side mock exam expiry (currently only enforced reactively), stale/abandoned attempt handling, and the still-open question of whether to keep building or get real student feedback first.

## Module 17: Stale Mock Attempt Cleanup — Run It

Closes the "abandoned attempt" gap that's been flagged since Module 5, and that you actually saw in your own analytics dashboard in Module 13 (13 mock attempts, only 1 finished). No new dependency, no scheduler — a shared helper (`app/services/mock_cleanup.py`) lazily auto-finalizes any mock attempt that's past its `expires_at` but was never submitted, scored based on whatever was answered before it was abandoned.

**Where it runs:** whenever a student's own mock status/answer/submit endpoints are touched, and whenever they view their own analytics (overview/history) — no cron job needed, and it only ever touches the current user's own data.

### No rebuild needed

Pure code, no new dependencies or migrations. `docker compose restart backend` is enough.

### Run the automated tests

```
docker compose exec backend pytest -v tests/test_mock_cleanup.py
```

Should show 3 new passing tests: one confirming an expired, unanswered attempt gets auto-scored at 0%, one confirming the cleanup is correctly scoped to the right user only, and one confirming a status check on an abandoned attempt finalizes it with the correct score based on what was actually answered.

### See it for real (optional)

If you still have old abandoned mock attempts from earlier testing sessions sitting in your dev database, refresh `/analytics` in the browser — any that are now past their (long-expired) time limit should show a real score instead of "incomplete" the next time you view your history.

### Full suite check

```
docker compose exec backend pytest -v
```

Should now show 39 total tests passing (36 from before + 3 new).

If all tests pass, Module 17 is done.

## What's next

The known-gaps list from the original charter and everything discovered along the way is now essentially closed: security gaps fixed (Module 8), automated testing in place (Module 12), tutor cost-protected (Module 15), deprecation warnings cleared (Module 16), and abandoned attempts now self-heal (Module 17). What's left is genuinely a product/business decision, not an engineering one: P2 polish (flashcards, dark mode), expanding the AI Tutor (conversation memory, study plans), or — the thing worth doing before any of that — finding out from real nursing students what actually matters to them next.

## Module 18: Production Deployment (Railway) — Run It

This is the first module that needs **Git and GitHub**, since Railway deploys from a repository, not a zip file. New territory — take it slow.

### What changed in this module

- Backend now reads CORS origins and environment from config instead of hardcoding `localhost` — production must set real values or the app **refuses to start** (a deliberate fail-fast safety check if `JWT_SECRET_KEY` is still the dev default in production).
- Backend Dockerfile now auto-runs `alembic upgrade head` before starting — only affects Railway; your local `docker-compose.yml` still overrides this with its own dev command, unaffected.
- Frontend Dockerfile now does a real production build (`next build` + `next start`) instead of the dev server — again, only affects Railway; local dev is unaffected since `docker-compose.yml` overrides it with `npm run dev`.
- A worthwhile side effect: real Paystack webhooks will finally work automatically once deployed — no more manually running `simulate_webhook.py`, since Paystack's servers can reach a real public URL.

### Step 1: Get your code onto GitHub

If you've never used Git before, this is genuinely new — go slow and ask if anything errors.

```
cd C:\Users\Uche\OneDrive\Documents\nmcn-platform
git init
git add .
git commit -m "Initial commit: full NMCN platform MVP"
```

Then create a new **empty** repository on github.com (no README, no .gitignore — you already have one), and follow GitHub's instructions to push an existing local repo, which will look like:

```
git remote add origin https://github.com/<your-username>/nmcn-platform.git
git branch -M main
git push -u origin main
```

Confirm on github.com that your files (not `node_modules`, not `.env`) actually show up.

### Step 2: Create a Railway project

1. Sign up at railway.app (free to start; usage-based billing kicks in beyond the free trial credit).
2. New Project → "Deploy from GitHub repo" → select your `nmcn-platform` repo.
3. Railway will try to auto-detect a service — delete whatever it creates automatically; we'll add each service manually since this is a monorepo with `backend/` and `frontend/` subfolders.

### Step 3: Add Postgres

1. In your Railway project, click "Create" → "Database" → "Add PostgreSQL".
2. That's it — Railway manages this for you, no Dockerfile needed.

### Step 4: Add the backend service

1. "Create" → "GitHub Repo" → select your repo again.
2. In the new service's Settings, set **Root Directory** to `backend`. Railway will detect `backend/Dockerfile` automatically.
3. Go to the **Variables** tab and add:
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ENVIRONMENT=production
   JWT_SECRET_KEY=<paste a real random value — see below>
   CORS_ALLOWED_ORIGINS=http://localhost:3000
   PAYSTACK_SECRET_KEY=<your real Paystack test key>
   FRONTEND_CALLBACK_URL=http://localhost:3000/payment/callback
   GOOGLE_API_KEY=<your real Gemini key>
   ```
   (The `${{Postgres.DATABASE_URL}}` syntax references the Postgres service you just created — Railway will offer this as an autocomplete suggestion as you type.)

   Generate a real random JWT secret locally first:
   ```
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
   Paste that output as `JWT_SECRET_KEY` — never reuse the dev default.

4. Under Settings → Networking, click **"Generate Domain"** — this gives you a real public URL like `https://nmcn-backend-production.up.railway.app`. Copy it.
5. Deploy should start automatically. Watch the build logs — this is where `alembic upgrade head` runs automatically for the first time in production.

### Step 5: Add the frontend service

1. "Create" → "GitHub Repo" → select your repo again.
2. Set **Root Directory** to `frontend`.
3. Add one variable, using the backend URL from Step 4:
   ```
   NEXT_PUBLIC_API_URL=https://nmcn-backend-production.up.railway.app
   ```
   This **must** be set before the first build — remember, it's baked into the JS bundle at build time, not read at runtime.
4. Generate a public domain for this service too (Settings → Networking).
5. Deploy.

### Step 6: Close the loop — update the backend's CORS setting

Now that you have the frontend's real URL, go back to the **backend** service's Variables and update:
```
CORS_ALLOWED_ORIGINS=https://<your-frontend-domain>.up.railway.app
FRONTEND_CALLBACK_URL=https://<your-frontend-domain>.up.railway.app/payment/callback
```
Redeploy the backend service for this to take effect.

### Step 7: Point Paystack at your real webhook (optional but worth doing now)

In your Paystack dashboard → Settings → API Keys & Webhooks, set the webhook URL to:
```
https://<your-backend-domain>.up.railway.app/payments/webhook
```
Now real Paystack test payments will trigger your webhook automatically — no more manually running `simulate_webhook.py`.

### Test it for real

Open your frontend's real public URL in a browser (on your phone too, if you want — it's a real URL now, not localhost). Walk through signup → practice → mock exam → tutor, same as every local test so far, just on the real internet.

If signup/login/practice all work on the live URL, Module 18 is done — and you have a real, shareable product.

## What's next

You now have something you can actually send a link to a nursing student and say "try this." That's the natural point to pause and gather real feedback, or continue with P2 features / AI Tutor expansion armed with a live URL to test changes against immediately.
