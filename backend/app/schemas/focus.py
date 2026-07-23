from pydantic import BaseModel, Field


class FocusSessionCompleteRequest(BaseModel):
    duration_minutes: int = Field(ge=1, le=180)


class FocusSessionCompleteResponse(BaseModel):
    total_sessions: int
    total_minutes: int
    current_streak: int
