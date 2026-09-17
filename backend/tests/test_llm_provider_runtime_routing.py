from types import SimpleNamespace

from app.api.routes import (
    analysis_action_plan,
    analysis_recommendation,
    analysis_strategic_reply,
    analysis_strategy,
    analysis_structured,
)


class FakeProvider:
    pass


MODULES = [
    analysis_structured,
    analysis_strategy,
    analysis_recommendation,
    analysis_strategic_reply,
    analysis_action_plan,
]


def test_configured_provider_is_used_by_all_llm_analysis_routes(monkeypatch):
    fake_provider = FakeProvider()
    config = SimpleNamespace(provider="openai_compatible")

    for module in MODULES:
        monkeypatch.setattr(module.provider_config_service, "get", lambda conn, user_id: config)
        monkeypatch.setattr(
            module.provider_config_service,
            "build_provider",
            lambda conn, user_id: fake_provider,
        )

        with object() as conn:
            provider = module._build_provider(conn, "user-a")

        assert provider is fake_provider


def test_unconfigured_provider_keeps_qwen_default_on_all_llm_analysis_routes(monkeypatch):
    for module in MODULES:
        fake_qwen = FakeProvider()
        monkeypatch.setattr(module.provider_config_service, "get", lambda conn, user_id: None)
        monkeypatch.setattr(module, "QwenProvider", lambda: fake_qwen)

        provider = module._build_provider(object(), "user-a")

        assert provider is fake_qwen
