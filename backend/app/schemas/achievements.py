from pydantic import BaseModel


class Badge(BaseModel):
    id: str
    name: str
    description: str
    earned: bool


class CertificateEligibility(BaseModel):
    eligible: bool
    reason: str
