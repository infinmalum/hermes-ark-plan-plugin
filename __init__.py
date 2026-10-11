"""Volcengine ARK subscription providers.

No model id is hardcoded anywhere in this plugin:

* Both plans attempt to read their own live /models catalog at selection time.
* If a catalog request fails, users can still enter model ids manually.

Manual entry stays available for both providers, which is also the escape hatch
when the live catalog hides something an account can actually call.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request

from providers import register_provider
from providers.base import ProviderProfile

_BASE_URL = "https://ark.cn-beijing.volces.com"
# Catalog rows that are not callable, or are not chat models, are filtered out.
_UNUSABLE_STATUS = frozenset({"shutdown", "retiring"})
_EXCLUDED_DOMAINS = frozenset({"router"})
_CATALOG_TTL_SECONDS = 300.0
_catalog_cache: dict[str, tuple[float, list[dict]]] = {}


def _is_selectable(row: object) -> bool:
    """True for catalog rows a chat/agent client can be pointed at."""
    if not isinstance(row, dict) or not row.get("id"):
        return False
    if str(row.get("status") or "").lower() in _UNUSABLE_STATUS:
        return False
    if str(row.get("domain") or "").lower() in _EXCLUDED_DOMAINS:
        return False
    modalities = row.get("modalities") or {}
    outputs = modalities.get("output_modalities") or []
    return "text" in outputs


class ArkPlanProfile(ProviderProfile):
    """Both subscriptions: live catalog, filtered, nothing hardcoded."""

    def fetch_models(
        self, *, api_key: str | None = None, base_url: str | None = None, timeout: float = 8.0
    ) -> list[str] | None:
        catalog = self.fetch_catalog(api_key=api_key, base_url=base_url, timeout=timeout)
        if catalog is None:
            return None
        return sorted({row["id"] for row in catalog if _is_selectable(row)}) or None

    def fetch_catalog(
        self, *, api_key: str | None = None, base_url: str | None = None, timeout: float = 8.0
    ) -> list[dict] | None:
        """Live catalog rows, or None when the endpoint cannot be read."""
        url = self._catalog_url(base_url)
        if not url:
            return None
        now = time.monotonic()
        cached = _catalog_cache.get(url)
        if cached and now - cached[0] < _CATALOG_TTL_SECONDS:
            return cached[1]
        rows = self._read_catalog(url, api_key=api_key, timeout=timeout)
        if rows is not None:
            _catalog_cache[url] = (now, rows)
        return rows

    def _catalog_url(self, base_url: str | None) -> str:
        caller = (base_url or "").strip().rstrip("/")
        if caller and caller != (self.base_url or "").rstrip("/"):
            return caller + "/models"
        return (self.models_url or "").strip() or (self.base_url or "").rstrip("/") + "/models"

    def _read_catalog(self, url: str, *, api_key: str | None, timeout: float) -> list[dict] | None:
        key = api_key or os.environ.get((self.env_vars or ("",))[0], "")
        if not key:
            return None
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {key}")
        request.add_header("Accept", "application/json")
        try:
            opener = None
            try:
                from hermes_cli.urllib_security import open_credentialed_url

                opener = open_credentialed_url
            except Exception:
                opener = None
            if opener is not None:
                with opener(request, timeout=timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            else:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None
        rows = payload.get("data") if isinstance(payload, dict) else None
        return rows if isinstance(rows, list) else None


register_provider(ArkPlanProfile(
    name="ark-coding-plan",
    aliases=("ark-coding", "volcengine-ark-coding-plan"),
    display_name="Volcengine ARK Coding Plan",
    description="火山方舟 Coding Plan — OpenAI Chat Completions, live model catalog",
    signup_url="https://console.volcengine.com/ark",
    api_mode="chat_completions",
    env_vars=("ARK_CODING_API_KEY",),
    base_url=_BASE_URL + "/api/coding/v3",
    auth_type="api_key",
    supports_model_listing=True,
    supports_health_check=True,
    fallback_models=(),
))

register_provider(ArkPlanProfile(
    name="ark-agentplan",
    aliases=("ark-plan", "volcengine-ark-plan", "ark-agent-plan"),
    display_name="Volcengine ARK Agent Plan",
    description="火山方舟 Agent Plan — OpenAI Responses API, live model catalog",
    signup_url="https://console.volcengine.com/ark",
    api_mode="codex_responses",
    env_vars=("ARK_PLAN_API_KEY",),
    base_url=_BASE_URL + "/api/plan/v3",
    auth_type="api_key",
    supports_model_listing=True,
    supports_health_check=True,
    fallback_models=(),
))
