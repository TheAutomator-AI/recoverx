from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from core.domain.enums import AutonomyLevel, FailureStep, RecoveryAction
from core.domain.schemas import PaymentContext


class PolicyConfig(BaseModel):
    max_autonomous_retries: int = 2
    max_total_attempts: int = 4
    min_cooldown_seconds: int = 1800  # 30 minutes default
    high_value_threshold: float = 50000.0  # ₹50,000 requires human review
    block_terminal_retry: bool = True
    require_verified_idempotency: bool = True


class PolicyEvaluationContext(BaseModel):
    payment_context: PaymentContext
    candidate_action: RecoveryAction
    candidate_autonomy: AutonomyLevel
    composite_confidence: float
    existing_retry_count: int = 0
    last_attempt_at: Optional[datetime] = None
    has_active_pending_attempt: bool = False
    is_previously_recovered: bool = False
    has_contradictory_records: bool = False
    proposed_message: Optional[str] = None
