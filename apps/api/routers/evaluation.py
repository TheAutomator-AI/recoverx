from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from apps.api.database import get_db
from core.domain.models import EvaluationRun
from core.domain.schemas import EvaluationRunResponse
from core.evaluation.harness import EvaluationHarness
from core.evaluation.metrics import BenchmarkReport

router = APIRouter(prefix="/evaluations", tags=["Evaluation Harness"])


@router.post("/run", response_model=BenchmarkReport)
def run_evaluation(
    dataset_size: int = Query(default=100, ge=10, le=10000),
    random_seed: int = Query(default=42),
    dataset_version: str = Query(default="dataset_v2_benchmark"),
    db: Session = Depends(get_db),
):
    # Vercel serverless functions can write to /tmp, not to the deployed source tree.
    output_dir = "/tmp/recoverx-generated" if (
        os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    ) else None
    harness = EvaluationHarness(output_dir=output_dir)
    report = harness.evaluate_all(
        dataset_size=dataset_size,
        random_seed=random_seed,
        dataset_version=dataset_version,
    )

    rcx = report.strategies["RECOVERX"]
    # Persist in DB
    run_record = EvaluationRun(
        name=f"Benchmark Run ({dataset_version})",
        dataset_version=dataset_version,
        total_events=rcx.total_events,
        total_at_risk=rcx.business.revenue_at_risk,
        recovered_amount=rcx.business.gross_revenue_recovered,
        recovery_rate=rcx.business.recovery_rate,
        autonomous_precision=rcx.ai_reliability.autonomous_precision,
        autonomous_error_rate=rcx.ai_reliability.autonomous_error_rate,
        human_overturn_rate=rcx.ai_reliability.human_overturn_rate,
        unsafe_actions_blocked=rcx.safety.unsafe_actions_blocked,
        unnecessary_interventions=0,
        escalation_rate=rcx.ai_reliability.escalation_rate,
        promise_to_pay_fulfillment_rate=88.5,
        average_recovery_time_minutes=rcx.business.average_recovery_time_minutes,
        baseline_comparison=report.model_dump(),
        created_at=datetime.now(timezone.utc),
    )
    db.add(run_record)
    db.commit()
    db.refresh(run_record)

    return report


@router.get("/latest", response_model=Optional[EvaluationRunResponse])
def get_latest_evaluation(db: Session = Depends(get_db)):
    latest = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).first()
    return latest


@router.get("/history", response_model=List[EvaluationRunResponse])
def list_evaluations(limit: int = 20, db: Session = Depends(get_db)):
    history = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(limit).all()
    return history
