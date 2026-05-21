class ProviderFactory:
    _instances = {}

    _PROVIDER_KEY_MAP = {
        "groq": "GROQ_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GEMINI_API_KEY",
    }

    @classmethod
    def available_providers(cls) -> list[str]:
        from config.settings import settings
        return [
            name
            for name, key_attr in cls._PROVIDER_KEY_MAP.items()
            if getattr(settings, key_attr, "").strip()
        ]

    @classmethod
    def get(cls, name: str):
        if name not in cls._instances:
            if name == "groq":
                from providers.groq import GroqProvider
                cls._instances[name] = GroqProvider()
            elif name == "openai":
                from providers.openai import OpenAIProvider
                cls._instances[name] = OpenAIProvider()
            elif name == "anthropic":
                from providers.anthropic import AnthropicProvider
                cls._instances[name] = AnthropicProvider()
            elif name == "google":
                from providers.google import GoogleProvider
                cls._instances[name] = GoogleProvider()
        return cls._instances.get(name)
