from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from core.domain.enums import (
    AutonomyLevel,
    PolicyDecisionType,
    PaymentStatus,
    FailureSource,
    FailureStep,
    PaymentMethod,
    RecoveryAction,
    CustomerSegment,
    Language,
    Script,
    Tone,
    Formality,
    AttemptStatus,
    ReviewerAction,
    PromiseStatus,
    AuditActor,
)


# --- Customer Schemas ---
class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    segment: CustomerSegment = CustomerSegment.DIRECT_TO_CONSUMER
    lifetime_value: float = 0.0
    historical_success_rate: float = 0.9
    historical_failure_rate: float = 0.1
    preferred_language: Language = Language.ENGLISH
    preferred_script: Script = Script.LATIN
    preferred_tone: Tone = Tone.EMPATHETIC


class CustomerCreate(CustomerBase):
    id: Optional[str] = None


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


# --- Payment Schemas ---
class PaymentEventIn(BaseModel):
    payment_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = "Priya Sharma"
    customer_email: Optional[str] = "priya.sharma@example.com"
    customer_phone: Optional[str] = "+919876543210"
    customer_segment: CustomerSegment = CustomerSegment.DIRECT_TO_CONSUMER
    order_id: str
    amount: float
    currency: str = "INR"
    failure_source: FailureSource = FailureSource.BANK
    failure_step: FailureStep = FailureStep.AUTHORIZATION
    failure_reason: str
    failure_code: Optional[str] = None
    payment_method: PaymentMethod = PaymentMethod.UPI
    attempt_number: int = 1
    preferred_language: Optional[Language] = Language.ENGLISH
    preferred_script: Optional[Script] = Script.LATIN
    preferred_tone: Optional[Tone] = Tone.EMPATHETIC
    metadata: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    customer_id: str
    customer: Optional[CustomerResponse] = None
    order_id: str
    amount: float
    currency: str
    status: PaymentStatus
    failure_source: FailureSource
    failure_step: FailureStep
    failure_reason: str
    failure_code: Optional[str] = None
    payment_method: PaymentMethod
    attempt_number: int
    is_simulated: bool
    raw_event_payload: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# --- Context Layer Schemas ---
class CustomerContext(BaseModel):
    customer_id: str
    name: str
    segment: CustomerSegment
    lifetime_value: float
    historical_success_rate: float
    historical_failure_rate: float
    preferred_language: Language
    preferred_script: Script
    preferred_tone: Tone
    prior_promises_count: int = 0
    prior_broken_promises_count: int = 0


class PaymentContext(BaseModel):
    payment_id: str
    order_id: str
    amount: float
    currency: str
    failure_source: FailureSource
    failure_step: FailureStep
    failure_reason: str
    failure_code: Optional[str] = None
    payment_method: PaymentMethod
    attempt_number: int
    is_simulated: bool = True
    customer: CustomerContext
    previous_attempts: List[Dict[str, Any]] = []
    active_recovery_attempts_count: int = 0
    last_attempt_time: Optional[datetime] = None
    is_previously_recovered: bool = False
    has_contradictory_records: bool = False
    raw_event_payload: Dict[str, Any] = {}


# --- AI Reasoning Schemas ---
class ConfidenceFactors(BaseModel):
    reason_clarity: float = Field(..., ge=0.0, le=1.0, description="Telemetry specificity and contradiction check (0.0 to 1.0)")
    historical_pattern: float = Field(..., ge=0.0, le=1.0, description="Customer cohort historical success pattern (0.0 to 1.0)")
    context_completeness: float = Field(..., ge=0.0, le=1.0, description="Completeness of transaction and customer metadata (0.0 to 1.0)")
    recovery_history: float = Field(..., ge=0.0, le=1.0, description="Attempt progression penalty (0.0 to 1.0)")
    model_assessment: float = Field(..., ge=0.0, le=1.0, description="Model self-assessed confidence (0.0 to 1.0)")


class AIDiagnosisOutput(BaseModel):
    likely_failure_cause: str = Field(..., description="Root cause diagnosis of the payment failure")
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured key evidence supporting diagnosis"
    )
    raw_model_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Self-assessed confidence by the model"
    )
    recommended_recovery_action: RecoveryAction = Field(..., description="Recommended recovery strategy")
    recommended_delay_hours: float = Field(default=0.0, ge=0.0, description="Recommended retry delay in hours")
    confidence_factors: Optional[ConfidenceFactors] = None
    recommended_language: Language = Language.ENGLISH
    recommended_script: Script = Script.LATIN
    recommended_tone: Tone = Tone.EMPATHETIC
    rationale: str = Field(..., description="Explainable rationale for recommendation")
    model_name: str = "RecoverX-Diagnostic-v1"


# --- Confidence Calibration Schemas ---
class ConfidenceBreakdown(BaseModel):
    reason_clarity_score: float  # Weight: 35%
    historical_pattern_score: float  # Weight: 25%
    context_completeness_score: float  # Weight: 20%
    action_history_score: float  # Weight: 10%
    model_assessment_score: float  # Weight: 10%
    composite_confidence: float
    autonomy_candidate: AutonomyLevel


# --- Recovery Decision Schemas ---
class RecoveryDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    payment_id: str
    diagnosis: str
    evidence: Dict[str, Any]
    confidence: float
    recommended_action: RecoveryAction
    recommended_delay_hours: float
    communication_language: str
    communication_script: str
    communication_tone: str
    rationale: str
    autonomy_level: AutonomyLevel
    model_name: str
    factor_scores: Dict[str, float]
    created_at: datetime


# --- Deterministic Policy Schemas ---
class PolicyRuleResult(BaseModel):
    rule_name: str
    passed: bool
    decision: PolicyDecisionType
    detail: str


class PolicyEvaluationResult(BaseModel):
    decision: PolicyDecisionType  # APPROVE, BLOCK, ESCALATE
    reasons: List[str]
    rules_evaluated: List[PolicyRuleResult]
    retry_count: int
    cooldown_satisfied: bool
    cooldown_remaining_seconds: int = 0
    risk_flags: List[str]


class PolicyDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    payment_id: str
    decision: PolicyDecisionType
    reasons: List[str]
    rules_evaluated: List[Dict[str, Any]]
    retry_count: int
    cooldown_status: Dict[str, Any]
    risk_flags: List[str]
    created_at: datetime


# --- Recovery Attempt Schemas ---
class RecoveryAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    payment_id: str
    strategy: str
    status: AttemptStatus
    scheduled_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    result: Dict[str, Any]
    amount_recovered: float
    idempotency_key: str
    created_at: datetime


# --- Human Review Schemas ---
class HumanReviewRequest(BaseModel):
    action: ReviewerAction  # APPROVE, MODIFY, REJECT
    modified_action: Optional[RecoveryAction] = None
    modified_delay_hours: Optional[float] = None
    reason: str
    reviewer_notes: Optional[str] = None
    review_duration_seconds: float = 0.0


class HumanReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    payment_id: str
    decision_id: Optional[str] = None
    reviewer_action: ReviewerAction
    original_ai_action: str
    modified_action: Optional[str] = None
    reason: str
    review_duration_seconds: float
    reviewer_notes: Optional[str] = None
    created_at: datetime


# --- Promise to Pay Schemas ---
class PromiseToPayCreate(BaseModel):
    payment_id: str
    amount: Optional[float] = None
    promised_date: datetime
    language: Language = Language.ENGLISH
    script: Script = Script.LATIN
    message: Optional[str] = None


class PromiseToPayUpdate(BaseModel):
    status: PromiseStatus
    fulfilled_at: Optional[datetime] = None
    follow_up_at: Optional[datetime] = None
    notes: Optional[str] = None


class PromiseToPayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    payment_id: str
    customer_id: str
    amount: float
    promised_date: datetime
    language: str
    script: str
    message: str
    status: PromiseStatus
    follow_up_at: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None
    created_at: datetime


# --- Multilingual Communication Schemas ---
class CommunicationMessage(BaseModel):
    language: Language
    script: Script
    tone: Tone
    headline: str
    body: str
    cta_text: str
    is_synthetic: bool = True
    disclaimer: str = "Simulated communication preview. RecoverX does not initiate unverified real financial transactions."
    validation_flags: List[str] = []


class MultilingualBundle(BaseModel):
    payment_id: str
    selected_language: Language
    selected_script: Script
    selected_tone: Tone
    messages: Dict[str, CommunicationMessage]


# --- Audit Schemas ---
class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    payment_id: Optional[str] = None
    event_type: str
    actor: str
    payload: Dict[str, Any]
    timestamp: datetime


# --- Pipeline & Journey Schemas ---
class JourneyStep(BaseModel):
    step_name: str
    title: str
    status: str  # COMPLETED, ACTIVE, BLOCKED, ESCALATED, PENDING
    timestamp: datetime
    actor: str
    details: Dict[str, Any]


class PaymentJourneyResponse(BaseModel):
    payment: PaymentResponse
    steps: List[JourneyStep]
    active_autonomy_level: Optional[AutonomyLevel] = None
    latest_confidence: Optional[float] = None
    latest_policy_decision: Optional[PolicyDecisionType] = None
    audit_trail: List[AuditEventResponse] = []


# --- Evaluation Run Schemas ---
class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    dataset_version: str
    total_events: int
    total_at_risk: float
    recovered_amount: float
    recovery_rate: float
    autonomous_precision: float
    autonomous_error_rate: float
    human_overturn_rate: float
    unsafe_actions_blocked: int
    unnecessary_interventions: int
    escalation_rate: float
    promise_to_pay_fulfillment_rate: float
    average_recovery_time_minutes: float
    baseline_comparison: Dict[str, Any]
    created_at: datetime


# --- Dashboard Stats Schema ---
class DashboardStats(BaseModel):
    revenue_at_risk: float
    revenue_recovered: float
    recovery_rate: float
    total_failed_payments: int
    autonomous_count: int
    assisted_count: int
    escalated_count: int
    autonomous_precision: float
    human_overturn_rate: float
    unsafe_actions_blocked: int
    active_promises_count: int
    promise_fulfillment_rate: float
    average_recovery_time_minutes: float
    autonomy_distribution: Dict[str, int]
    failure_reasons_breakdown: Dict[str, int]
    recent_activity: List[AuditEventResponse]
