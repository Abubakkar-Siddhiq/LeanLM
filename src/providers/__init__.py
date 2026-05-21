class ProviderFactory:
    _instances = {}

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
