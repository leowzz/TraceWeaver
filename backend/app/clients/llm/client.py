"""LLM client implementation using agno framework."""

from agno.agent import Agent
from agno.media import Image
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.models.openai.like import OpenAILike
from loguru import logger

from app.clients.llm.schema import LLMChatResponse
from app.models.enums import LLMProvider


class LLMClientError(Exception):
    """Exception raised when LLM client returns an error."""

    def __init__(self, message: str, provider: str | None = None):
        self.message = message
        self.provider = provider
        super().__init__(f"LLM error ({provider or 'unknown'}): {message}")


class LLMClient:
    """Unified LLM client using agno framework.
    
    Supports text and multimodal (text + images) interactions.
    """

    def __init__(
        self,
        provider: LLMProvider,
        model_id: str,
        base_url: str,
        api_key: str | None = None,
        config: dict | None = None,
    ):
        self.provider = provider
        self.model_id = model_id
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.api_key = api_key
        self.config = config or {}
        self._agent: Agent | None = None

    def _create_agent(self) -> Agent:
        """Create agno Agent based on provider type."""
        match self.provider:
            case LLMProvider.OPENAI:
                model = OpenAILike(
                    id=self.model_id,
                    api_key=self.api_key or "",
                    base_url=self.base_url or None,
                )
            case LLMProvider.OLLAMA:
                model = Ollama(
                    id=self.model_id,
                    host=self.base_url or "http://localhost:11434",
                )
            case LLMProvider.ANTHROPIC:
                # Use OpenAILike for Anthropic-compatible endpoints
                model = OpenAILike(
                    id=self.model_id,
                    api_key=self.api_key or "",
                    base_url=self.base_url or None,
                )
            case _:
                raise LLMClientError(
                    f"Unsupported provider: {self.provider}",
                    provider=self.provider.value,
                )

        return Agent(model=model, markdown=True)

    @property
    def agent(self) -> Agent:
        """Get or create agno agent."""
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent

    async def chat(self, message: str) -> LLMChatResponse:
        """Send a text-only chat request.

        Args:
            message: User message text

        Returns:
            Chat response from the model
        """
        try:
            response = self.agent.run(message)
            content = response.content if hasattr(response, "content") else str(response)
            return LLMChatResponse(content=content)
        except Exception as e:
            logger.error(f"Chat failed ({self.provider.value}): {e}")
            raise LLMClientError(str(e), provider=self.provider.value)

    async def analyze_image(
        self, image_bytes: bytes, prompt: str
    ) -> LLMChatResponse:
        """Analyze an image with a prompt.

        Args:
            image_bytes: Image bytes data
            prompt: Prompt text for analysis

        Returns:
            Analysis result from the model
        """
        try:
            image = Image(content=image_bytes)
            response = self.agent.run(prompt, images=[image])
            content = response.content if hasattr(response, "content") else str(response)
            return LLMChatResponse(content=content)
        except Exception as e:
            logger.error(f"Image analysis failed ({self.provider.value}): {e}")
            raise LLMClientError(str(e), provider=self.provider.value)

    async def close(self) -> None:
        """Cleanup resources."""
        self._agent = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
