from pydantic import BaseModel, Field


class ConfidenceWeights(BaseModel):
    reason_clarity_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    historical_pattern_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    context_completeness_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    action_history_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    model_assessment_weight: float = Field(default=0.10, ge=0.0, le=1.0)

    def validate_weights(self) -> bool:
        total = (
            self.reason_clarity_weight
            + self.historical_pattern_weight
            + self.context_completeness_weight
            + self.action_history_weight
            + self.model_assessment_weight
        )
        return abs(total - 1.0) < 1e-4


class ConfidenceThresholds(BaseModel):
    high_threshold: float = Field(default=0.85, ge=0.0, le=1.0, description="Autonomous candidate cutoff")
    medium_threshold: float = Field(default=0.60, ge=0.0, le=1.0, description="Assisted candidate cutoff")
