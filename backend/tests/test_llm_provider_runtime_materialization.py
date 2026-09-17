from types import SimpleNamespace

from app.services import llm_provider_config
from app.services.llm_provider_config import LLMProviderConfigService


class FakeFernet:
    def decrypt(self, value: bytes) -> bytes:
        return value


def test_configured_provider_materializes_persisted_runtime_parameters(monkeypatch):
    captured = {}

    class FakeQwenProvider:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    service = LLMProviderConfigService(repository=SimpleNamespace())
    row = {
        "provider": "openai_compatible",
        "base_url": "https://provider.example/v1",
        "model": "custom-model",
        "timeout_seconds": 42.5,
        "api_key_encrypted": "encrypted-key",
    }

    monkeypatch.setattr(service.repository, "get", lambda conn, user_id: row)
    monkeypatch.setattr(service, "_fernet", lambda: FakeFernet())
    monkeypatch.setattr(llm_provider_config, "QwenProvider", FakeQwenProvider)

    provider = service.build_provider(object(), "user-a")

    assert isinstance(provider, FakeQwenProvider)
    assert captured == {
        "api_key": "encrypted-key",
        "base_url": "https://provider.example/v1",
        "model": "custom-model",
        "timeout_seconds": 42.5,
    }
