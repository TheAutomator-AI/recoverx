from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    segment = Column(String(64), default="DIRECT_TO_CONSUMER", nullable=False)
    lifetime_value = Column(Float, default=0.0, nullable=False)
    historical_success_rate = Column(Float, default=0.9, nullable=False)
    historical_failure_rate = Column(Float, default=0.1, nullable=False)
    preferred_language = Column(String(64), default="English", nullable=False)
    preferred_script = Column(String(64), default="Latin", nullable=False)
    preferred_tone = Column(String(64), default="EMPATHETIC", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    promises = relationship("PromiseToPay", back_populates="customer", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False)
    order_id = Column(String(64), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(64), default="FAILED", nullable=False, index=True)
    failure_source = Column(String(64), default="BANK", nullable=False)
    failure_step = Column(String(64), default="AUTHORIZATION", nullable=False)
    failure_reason = Column(Text, nullable=False)
    failure_code = Column(String(64), nullable=True)
    payment_method = Column(String(64), default="UPI", nullable=False)
    attempt_number = Column(Integer, default=1, nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)
    raw_event_payload = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    customer = relationship("Customer", back_populates="payments")
    decisions = relationship("RecoveryDecision", back_populates="payment", cascade="all, delete-orphan")
    policy_decisions = relationship("PolicyDecision", back_populates="payment", cascade="all, delete-orphan")
    attempts = relationship("RecoveryAttempt", back_populates="payment", cascade="all, delete-orphan")
    human_reviews = relationship("HumanReview", back_populates="payment", cascade="all, delete-orphan")
    promises = relationship("PromiseToPay", back_populates="payment", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="payment", cascade="all, delete-orphan")


class RecoveryDecision(Base):
    __tablename__ = "recovery_decisions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    payment_id = Column(String(64), ForeignKey("payments.id"), nullable=False, index=True)
    diagnosis = Column(Text, nullable=False)
    evidence = Column(JSON, default=dict, nullable=False)
    confidence = Column(Float, nullable=False)
    recommended_action = Column(String(64), nullable=False)
    recommended_delay_hours = Column(Float, default=0.0, nullable=False)
    communication_language = Column(String(64), default="English", nullable=False)
    communication_script = Column(String(64), default="Latin", nullable=False)
    communication_tone = Column(String(64), default="EMPATHETIC", nullable=False)
    rationale = Column(Text, nullable=False)
    autonomy_level = Column(String(64), nullable=False, index=True)  # AUTONOMOUS, ASSISTED, ESCALATED
    model_name = Column(String(128), default="RecoverX-Diagnostic-v1", nullable=False)
    factor_scores = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    payment = relationship("Payment", back_populates="decisions")
    human_reviews = relationship("HumanReview", back_populates="decision")


class PolicyDecision(Base):
    __tablename__ = "policy_decisions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    payment_id = Column(String(64), ForeignKey("payments.id"), nullable=False, index=True)
    decision = Column(String(64), nullable=False, index=True)  # APPROVE, BLOCK, ESCALATE
    reasons = Column(JSON, default=list, nullable=False)
    rules_evaluated = Column(JSON, default=list, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    cooldown_status = Column(JSON, default=dict, nullable=False)
    risk_flags = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    payment = relationship("Payment", back_populates="policy_decisions")


class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    payment_id = Column(String(64), ForeignKey("payments.id"), nullable=False, index=True)
    strategy = Column(String(64), nullable=False)
    status = Column(String(64), default="SCHEDULED", nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    result = Column(JSON, default=dict, nullable=False)
    amount_recovered = Column(Float, default=0.0, nullable=False)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    payment = relationship("Payment", back_populates="attempts")


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    payment_id = Column(String(64), ForeignKey("payments.id"), nullable=False, index=True)
    decision_id = Column(String(64), ForeignKey("recovery_decisions.id"), nullable=True)
    reviewer_action = Column(String(64), nullable=False)  # APPROVE, MODIFY, REJECT
    original_ai_action = Column(String(64), nullable=False)
    modified_action = Column(String(64), nullable=True)
    reason = Column(Text, nullable=False)
    review_duration_seconds = Column(Float, default=0.0, nullable=False)
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    payment = relationship("Payment", back_populates="human_reviews")
    decision = relationship("RecoveryDecision", back_populates="human_reviews")


class PromiseToPay(Base):
    __tablename__ = "promises_to_pay"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    payment_id = Column(String(64), ForeignKey("payments.id"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    promised_date = Column(DateTime, nullable=False)
    language = Column(String(64), default="English", nullable=False)
    script = Column(String(64), default="Latin", nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(64), default="PROMISE_TO_PAY", nullable=False, index=True)
    follow_up_at = Column(DateTime, nullable=True)
    fulfilled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    payment = relationship("Payment", back_populates="promises")
    customer = relationship("Customer", back_populates="promises")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    payment_id = Column(String(64), ForeignKey("payments.id"), nullable=True, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    actor = Column(String(64), nullable=False)
    payload = Column(JSON, default=dict, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    payment = relationship("Payment", back_populates="audit_events")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    dataset_version = Column(String(64), default="v1_standard", nullable=False)
    total_events = Column(Integer, default=0, nullable=False)
    total_at_risk = Column(Float, default=0.0, nullable=False)
    recovered_amount = Column(Float, default=0.0, nullable=False)
    recovery_rate = Column(Float, default=0.0, nullable=False)
    autonomous_precision = Column(Float, default=0.0, nullable=False)
    autonomous_error_rate = Column(Float, default=0.0, nullable=False)
    human_overturn_rate = Column(Float, default=0.0, nullable=False)
    unsafe_actions_blocked = Column(Integer, default=0, nullable=False)
    unnecessary_interventions = Column(Integer, default=0, nullable=False)
    escalation_rate = Column(Float, default=0.0, nullable=False)
    promise_to_pay_fulfillment_rate = Column(Float, default=0.0, nullable=False)
    average_recovery_time_minutes = Column(Float, default=0.0, nullable=False)
    baseline_comparison = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
