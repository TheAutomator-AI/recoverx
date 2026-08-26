from abc import ABC, abstractmethod
from typing import Any, Dict
from core.domain.schemas import (
    PaymentContext,
    AIDiagnosisOutput,
    CommunicationMessage,
)
from core.domain.enums import Language, Script, Tone


class AIProvider(ABC):
    """
    Abstract AI Provider interface for RecoverX.
    The AI produces structured reasoning, evidence, and recommendations.
    THE AI NEVER DIRECTLY AUTHORIZES OR EXECUTES FINANCIAL ACTIONS.
    """

    @abstractmethod
    def diagnose_failure(self, context: PaymentContext) -> AIDiagnosisOutput:
        """
        Diagnose the root cause of a payment failure from the context and return structured reasoning.
        """
        pass

    @abstractmethod
    def generate_recovery_plan(self, context: PaymentContext) -> Dict[str, Any]:
        """
        Generate a structured recovery plan with recommended steps and timing.
        """
        pass

    @abstractmethod
    def generate_recovery_message(
        self,
        context: PaymentContext,
        language: Language,
        script: Script,
        tone: Tone,
    ) -> CommunicationMessage:
        """
        Generate a localized, tone-calibrated communication message.
        """
        pass
