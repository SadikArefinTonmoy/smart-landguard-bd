from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class UserLoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_role: str
    user_name: str


class RiskFlag(BaseModel):
    title: str
    severity: str
    evidence: str
    source: str
    recommendation: str
    requires_human_review: bool = True


class PropertySummary(BaseModel):
    id: str
    title: str
    location: str
    price: str
    status: str
    risk_level: str
    verification_progress: int


class PropertyDetail(BaseModel):
    id: str
    title: str
    location: str
    mouza: str
    khatian: str
    dag: str
    area: str
    asking_price: str
    verification_status: str
    risk_level: str
    evidence_summary: str
    risk_flags: List[RiskFlag]


class DashboardStat(BaseModel):
    label: str
    value: int


class DashboardSummary(BaseModel):
    total_properties_viewed: int
    saved_properties: int
    verification_requests: int
    completed_checks: int
    pending_checks: int
    unresolved_issues: int
    missing_documents: int
    upcoming_actions: int
    recent_alerts: int
    simulated_purchase_requests: int


class ReportSummary(BaseModel):
    property_id: str
    report_title: str
    status: str
    summary: str
    recommendations: List[str]
