"""Capability-based Bedrock model registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ada.config import AdaConfig


class ModelTier(StrEnum):
    HIGH = "high"
    BALANCED = "balanced"
    ECONOMY = "economy"


class Capability(StrEnum):
    FAST_ROUTING = "FAST_ROUTING"
    STRUCTURED_EXTRACTION = "STRUCTURED_EXTRACTION"
    COMPLEX_REASONING = "COMPLEX_REASONING"
    MULTIMODAL = "MULTIMODAL"
    HIGH_STAKES_REVIEW = "HIGH_STAKES_REVIEW"


class TaskClass(StrEnum):
    ROUTING = "routing"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    MAPPING = "mapping"
    REASONING = "reasoning"
    MULTIMODAL = "multimodal"
    HIGH_STAKES = "high_stakes"


@dataclass(frozen=True)
class TierProfile:
    tier: ModelTier
    primary: str
    fallbacks: tuple[str, ...]
    max_tokens: int
    max_agent_loops: int
    request_timeout_seconds: int
    allow_optional_passes: bool
    evaluator_enabled: bool
    debate_enabled: bool
    retrieval_top_k: int


TASK_CAPABILITIES: dict[TaskClass, Capability] = {
    TaskClass.ROUTING: Capability.FAST_ROUTING,
    TaskClass.CLASSIFICATION: Capability.FAST_ROUTING,
    TaskClass.EXTRACTION: Capability.STRUCTURED_EXTRACTION,
    TaskClass.MAPPING: Capability.STRUCTURED_EXTRACTION,
    TaskClass.REASONING: Capability.COMPLEX_REASONING,
    TaskClass.MULTIMODAL: Capability.MULTIMODAL,
    TaskClass.HIGH_STAKES: Capability.HIGH_STAKES_REVIEW,
}


class ModelRegistry:
    """Resolve budget tiers and capabilities without agent/model coupling."""

    def __init__(self, config: AdaConfig) -> None:
        self.config = config

    @staticmethod
    def _tier(tier: ModelTier | str) -> ModelTier:
        return tier if isinstance(tier, ModelTier) else ModelTier(tier.lower())

    @staticmethod
    def _capability(capability: Capability | str) -> Capability:
        if isinstance(capability, Capability):
            return capability
        try:
            return Capability(capability)
        except ValueError:
            return Capability[capability.upper()]

    def profile(self, tier: ModelTier | str) -> TierProfile:
        resolved = self._tier(tier)
        models = self.config.models_for_tier(resolved.value)
        if resolved is ModelTier.HIGH:
            return TierProfile(
                tier=resolved,
                primary=models[0],
                fallbacks=models[1:],
                max_tokens=self.config.high_max_tokens,
                max_agent_loops=self.config.high_max_agent_loops,
                request_timeout_seconds=self.config.request_timeout_seconds,
                allow_optional_passes=True,
                evaluator_enabled=True,
                debate_enabled=True,
                retrieval_top_k=12,
            )
        if resolved is ModelTier.BALANCED:
            return TierProfile(
                tier=resolved,
                primary=models[0],
                fallbacks=models[1:],
                max_tokens=self.config.balanced_max_tokens,
                max_agent_loops=self.config.balanced_max_agent_loops,
                request_timeout_seconds=self.config.request_timeout_seconds,
                allow_optional_passes=True,
                evaluator_enabled=True,
                debate_enabled=False,
                retrieval_top_k=8,
            )
        return TierProfile(
            tier=resolved,
            primary=models[0],
            fallbacks=models[1:],
            max_tokens=self.config.economy_max_tokens,
            max_agent_loops=self.config.economy_max_agent_loops,
            request_timeout_seconds=self.config.request_timeout_seconds,
            allow_optional_passes=False,
            evaluator_enabled=False,
            debate_enabled=False,
            retrieval_top_k=5,
        )

    @staticmethod
    def capability_for(task_class: TaskClass | str) -> Capability:
        resolved = (
            task_class if isinstance(task_class, TaskClass) else TaskClass(task_class.lower())
        )
        return TASK_CAPABILITIES[resolved]

    def model_for(self, tier: ModelTier | str, capability: Capability | str) -> str:
        """Resolve a model; only this registry knows model IDs."""

        profile = self.profile(tier)
        resolved = self._capability(capability)
        models = (profile.primary, *profile.fallbacks)
        if resolved is Capability.FAST_ROUTING:
            if profile.tier is ModelTier.HIGH:
                return models[-1]
            if profile.tier is ModelTier.BALANCED and len(models) > 1:
                return models[1]
            return models[-1]
        return profile.primary

    def active_profile(self) -> TierProfile:
        return self.profile(self.config.active_tier)
