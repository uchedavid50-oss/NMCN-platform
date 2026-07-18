const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> | undefined),
  };

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // response had no JSON body — fall back to statusText
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export interface User {
  id: string;
  email: string;
  role: string;
  subscription_status: string;
}

export interface Subject {
  id: string;
  name: string;
}

export interface Topic {
  id: string;
  subject_id: string;
  name: string;
}

export interface PracticeOption {
  id: string;
  text: string;
}

export interface PracticeQuestion {
  id: string;
  stem: string;
  difficulty: string;
  options: PracticeOption[];
}

export interface PracticeStartResponse {
  attempt_id: string;
  topic_id: string;
  questions: PracticeQuestion[];
}

export interface AnswerResponse {
  is_correct: boolean;
  correct_option_id: string;
  explanation: string;
}

export interface AttemptSummary {
  attempt_id: string;
  total_questions: number;
  correct_answers: number;
  score_percentage: number;
  started_at: string;
  finished_at: string | null;
}

export interface MockStartResponse {
  attempt_id: string;
  topic_id: string;
  time_limit_minutes: number;
  started_at: string;
  expires_at: string;
  questions: PracticeQuestion[];
}

export interface MockAnswerAck {
  received: boolean;
  message: string;
}

export interface QuestionBreakdown {
  question_id: string;
  stem: string;
  your_answer_id: string | null;
  your_answer_text: string | null;
  correct_option_id: string;
  correct_option_text: string;
  is_correct: boolean;
  explanation: string;
}

export interface MockSubmitResponse {
  attempt_id: string;
  total_questions: number;
  correct_answers: number;
  score_percentage: number;
  started_at: string;
  finished_at: string;
  time_limit_minutes: number;
  breakdown: QuestionBreakdown[];
}

export interface OverviewStats {
  total_attempts: number;
  completed_attempts: number;
  practice_attempts: number;
  mock_attempts: number;
  total_questions_answered: number;
  total_correct: number;
  overall_accuracy_percentage: number;
}

export interface TopicPerformance {
  topic_id: string;
  topic_name: string;
  subject_name: string;
  total_answered: number;
  correct_answered: number;
  accuracy_percentage: number;
  last_attempted_at: string | null;
}

export interface AttemptHistoryItem {
  attempt_id: string;
  mode: string;
  topic_name: string;
  subject_name: string;
  score_percentage: number | null;
  started_at: string;
  finished_at: string | null;
}

export interface AttemptHistory {
  total: number;
  items: AttemptHistoryItem[];
}

export interface TutorReply {
  reply: string;
}

export interface StudyPlan {
  has_weak_topics: boolean;
  weak_topic_names: string[];
  plan: string;
}

export interface Flashcard {
  question_id: string;
  front: string;
  back: string;
}

export const api = {
  signup: (email: string, password: string) =>
    request<User>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    return request<{ access_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
  },

  me: (token: string) => request<User>("/auth/me", {}, token),

  listSubjects: () => request<Subject[]>("/subjects"),

  listTopics: (subjectId: string) => request<Topic[]>(`/topics?subject_id=${subjectId}`),

  startPractice: (topicId: string, token: string) =>
    request<PracticeStartResponse>(
      "/practice/start",
      { method: "POST", body: JSON.stringify({ topic_id: topicId }) },
      token
    ),

  submitPracticeAnswer: (
    attemptId: string,
    questionId: string,
    selectedOptionId: string,
    token: string
  ) =>
    request<AnswerResponse>(
      `/practice/${attemptId}/answer`,
      {
        method: "POST",
        body: JSON.stringify({ question_id: questionId, selected_option_id: selectedOptionId }),
      },
      token
    ),

  finishPractice: (attemptId: string, token: string) =>
    request<AttemptSummary>(`/practice/${attemptId}/finish`, { method: "POST" }, token),

  startMock: (topicId: string, durationMinutes: number, token: string) =>
    request<MockStartResponse>(
      "/mock/start",
      { method: "POST", body: JSON.stringify({ topic_id: topicId, duration_minutes: durationMinutes }) },
      token
    ),

  submitMockAnswer: (attemptId: string, questionId: string, selectedOptionId: string, token: string) =>
    request<MockAnswerAck>(
      `/mock/${attemptId}/answer`,
      {
        method: "POST",
        body: JSON.stringify({ question_id: questionId, selected_option_id: selectedOptionId }),
      },
      token
    ),

  submitMockExam: (attemptId: string, token: string) =>
    request<MockSubmitResponse>(`/mock/${attemptId}/submit`, { method: "POST" }, token),

  getOverview: (token: string) => request<OverviewStats>("/analytics/overview", {}, token),

  getByTopic: (token: string) => request<TopicPerformance[]>("/analytics/by-topic", {}, token),

  getWeakTopics: (token: string) => request<TopicPerformance[]>("/analytics/weak-topics", {}, token),

  getHistory: (token: string, limit = 10) =>
    request<AttemptHistory>(`/analytics/history?limit=${limit}`, {}, token),

  askTutor: (questionId: string, message: string, token: string) =>
    request<TutorReply>(
      "/tutor/ask",
      { method: "POST", body: JSON.stringify({ question_id: questionId, message }) },
      token
    ),

  getStudyPlan: (token: string) =>
    request<StudyPlan>("/tutor/study-plan", { method: "POST" }, token),

  getFlashcards: (topicId: string, token: string) =>
    request<Flashcard[]>(`/flashcards?topic_id=${topicId}`, {}, token),
};
