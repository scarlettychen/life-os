"""Optional LLM client — never used for decisions, only narration."""

from __future__ import annotations

from lifeos.config import Settings, get_settings


def llm_available(settings: Settings | None = None) -> bool:
    cfg = settings or get_settings()
    return bool(cfg.llm_api_key and cfg.llm_provider)


def synthesize_review_narrative(context: str, settings: Settings | None = None) -> str | None:
    """Return an LLM-drafted review paragraph, or None if LLM is not configured."""
    cfg = settings or get_settings()
    if not llm_available(cfg):
        return None
    # Provider wiring deferred — deterministic review is the default.
    return None
