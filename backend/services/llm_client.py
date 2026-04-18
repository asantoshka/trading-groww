import os

from anthropic import Anthropic, AnthropicBedrock


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

MODELS = {
    "anthropic": {
        "sonnet": "claude-sonnet-4-5",
        "opus":   "claude-opus-4-5",
        "haiku":  "claude-haiku-4-5-20251001",
    },
    "bedrock": {
        "sonnet": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "opus":   "global.anthropic.claude-opus-4-5-20251101-v1:0",
        "haiku":  "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    },
}


class LLMClient:
    def __init__(self):
        self.provider = LLM_PROVIDER.lower()

        if self.provider == "bedrock":
            self._client = AnthropicBedrock(aws_region=AWS_REGION)
        elif self.provider == "anthropic":
            self._client = Anthropic(api_key=ANTHROPIC_API_KEY)
        else:
            raise ValueError(
                "LLM_PROVIDER must be 'anthropic' or "
                f"'bedrock', got: {self.provider}"
            )

        print(
            f"[LLMClient] Provider: {self.provider} | "
            f"Model: {self.get_model()}"
        )

    def get_model(self, tier="sonnet") -> str:
        return MODELS[self.provider].get(tier, MODELS[self.provider]["sonnet"])

    def create(self, system, messages, max_tokens=1000, tier="sonnet", **kwargs):
        model = self.get_model(tier)

        if self.provider == "bedrock":
            kwargs.pop("mcp_servers", None)

        return self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            **kwargs,
        )

    def extract_text(self, response) -> str:
        return "\n".join(
            block.text
            for block in response.content
            if hasattr(block, "type") and block.type == "text"
        ).strip()

    def is_bedrock(self) -> bool:
        return self.provider == "bedrock"

    def is_anthropic(self) -> bool:
        return self.provider == "anthropic"


llm_client = LLMClient()
