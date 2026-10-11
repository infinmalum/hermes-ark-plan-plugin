"""Volcengine ARK subscription providers with isolated credentials and catalogs."""
from providers import register_provider
from providers.base import ProviderProfile

_AGENT_MODELS = ("glm-5.3", "glm-5.3-flash", "doubao-seed-2.0-lite", "doubao-seed-2.0-mini")
_CODING_MODELS = _AGENT_MODELS + ("deepseek-v4-pro", "deepseek-v4.1-flash")


class ArkPlanProfile(ProviderProfile):
    """Expose a curated local catalog, without probing subscription /models."""

    def fetch_models(self, **kwargs) -> list[str]:
        return list(self.fallback_models)


def _register(name, aliases, display, mode, endpoint, key, models):
    register_provider(ArkPlanProfile(
        name=name, aliases=aliases, display_name=display,
        description=display + " — " + mode,
        signup_url="https://console.volcengine.com/ark",
        api_mode=mode, env_vars=(key,),
        base_url="https://ark.cn-beijing.volces.com" + endpoint,
        auth_type="api_key", supports_model_listing=False,
        supports_health_check=False, fallback_models=models,
    ))


_register("ark-agentplan", ("ark-plan", "volcengine-ark-plan", "ark-agent-plan"),
          "Volcengine ARK Agent Plan (OpenAI Responses)", "codex_responses",
          "/api/plan/v3", "ARK_PLAN_API_KEY", _AGENT_MODELS)
_register("ark-agentplan-anthropic", ("ark-agent-plan-anthropic", "ark-plan-anthropic"),
          "Volcengine ARK Agent Plan (Anthropic)", "anthropic",
          "/api/plan", "ARK_PLAN_API_KEY", _AGENT_MODELS)
_register("ark-coding-plan", ("ark-coding", "volcengine-ark-coding-plan"),
          "Volcengine ARK Coding Plan (OpenAI)", "chat_completions",
          "/api/coding/v3", "ARK_CODING_API_KEY", _CODING_MODELS)
_register("ark-coding-plan-anthropic", ("ark-coding-anthropic",),
          "Volcengine ARK Coding Plan (Anthropic)", "anthropic",
          "/api/coding", "ARK_CODING_API_KEY", _CODING_MODELS)
