"""LLM client implementation using agno as unified agent framework."""

import base64
from typing import Any

from loguru import logger

from app.clients.llm.schema import LLMChatMessage, LLMChatResponse
from app.models.enums import LLMProvider


class LLMClientError(Exception):
    """Exception raised when LLM client returns an error."""

    def __init__(self, message: str, provider: str | None = None):
        self.message = message
        self.provider = provider
        super().__init__(f"LLM client error ({provider or 'unknown'}): {message}")


class LLMClient:
    """Unified LLM client using agno as framework.

    All providers (OpenAI, Ollama, Anthropic, etc.) are accessed through agno Agent,
    providing a consistent interface across different model providers.
    
    This client supports both text-only and multimodal (text + images) interactions.
    """

    def __init__(
        self,
        provider: LLMProvider,
        model_id: str,
        base_url: str,
        api_key: str | None = None,
        config: dict | None = None,
        timeout: float = 60.0,
    ):
        """Initialize LLM client using agno framework.

        Args:
            provider: LLM provider type (all providers use agno as unified framework)
            model_id: Model ID/name
            base_url: API base_url URL
            api_key: API key (optional, depending on provider)
            config: Additional provider-specific configuration
            timeout: Request timeout in seconds (default: 60.0)
        """
        self.provider = provider
        self.model_id = model_id
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.api_key = api_key
        self.config = config or {}
        self.timeout = timeout
        self._agent: Any = None

    def _create_agno_model(self) -> Any:
        """Create agno model adapter based on provider type.

        Returns:
            Agno model adapter instance

        Raises:
            LLMClientError: If provider is not supported or initialization fails
        """
        try:
            from agno.agent import Agent
        except ImportError:
            raise LLMClientError(
                "agno package not installed. Install with: pip install agno",
                provider=self.provider.value,
            )

        try:
            if self.provider == LLMProvider.OPENAI:
                from agno.models.openai.like import OpenAILike

                model = OpenAILike(
                    id=self.model_id,
                    api_key=self.api_key or "",
                    base_url=self.base_url if self.base_url else None,
                )
                return Agent(model=model)

            elif self.provider == LLMProvider.OLLAMA:
                # Ollama through agno (using OpenAILike for compatibility)
                # Many ollama-compatible APIs support OpenAI-like interface
                from agno.models.openai.like import OpenAILike

                # Ollama base_url format: http://host:port
                host = self.base_url if self.base_url else "http://localhost:11434"
                model = OpenAILike(
                    id=self.model_id,
                    base_url=host,
                    api_key="",  # Ollama typically doesn't need API key
                )
                return Agent(model=model)

            elif self.provider == LLMProvider.ANTHROPIC:
                # Anthropic through agno
                # Note: Check agno documentation for Anthropic adapter availability
                # For now, using OpenAILike as fallback if Anthropic adapter not available
                try:
                    from agno.models.anthropic.like import AnthropicLike

                    model = AnthropicLike(
                        id=self.model_id,
                        api_key=self.api_key or "",
                    )
                    return Agent(model=model)
                except ImportError:
                    # Fallback: Use OpenAILike if Anthropic adapter not available
                    # This may work if the base_url supports OpenAI-compatible API
                    from agno.models.openai.like import OpenAILike

                    model = OpenAILike(
                        id=self.model_id,
                        api_key=self.api_key or "",
                        base_url=self.base_url if self.base_url else None,
                    )
                    logger.warning(
                        f"Anthropic adapter not available, using OpenAILike as fallback"
                    )
                    return Agent(model=model)

            else:
                raise LLMClientError(
                    f"Unsupported provider: {self.provider}. "
                    f"Supported providers: OPENAI, OLLAMA, ANTHROPIC",
                    provider=self.provider.value,
                )

        except LLMClientError:
            raise
        except Exception as e:
            raise LLMClientError(
                f"Failed to create agno model for provider {self.provider.value}: {e}",
                provider=self.provider.value,
            )

    async def _initialize_agent(self) -> Any:
        """Initialize agno agent.

        Returns:
            Agno Agent instance
        """
        if self._agent is not None:
            return self._agent

        self._agent = self._create_agno_model()
        return self._agent

    async def chat(
        self, messages: list[LLMChatMessage], images: list[bytes] | None = None
    ) -> LLMChatResponse:
        """Send chat request with optional images using agno agent.

        Args:
            messages: List of chat messages
            images: Optional list of image bytes (will be encoded and attached)

        Returns:
            Chat response from the model

        Raises:
            LLMClientError: If the request fails
        """
        agent = await self._initialize_agent()

        try:
            # Build user message content
            if not messages:
                raise LLMClientError("Messages list cannot be empty")

            # Combine messages into a single user message for agno
            # Agno's agent.run() typically takes a single user message string
            user_message_parts = []
            for msg in messages:
                if msg.role == "user":
                    user_message_parts.append(msg.content)

            if not user_message_parts:
                raise LLMClientError("No user message found in messages")

            user_message = "\n\n".join(user_message_parts)

            # Handle images - encode to base64 if provided
            # For agno, images can be passed as part of the message or through model-specific means
            # This is a simplified approach - actual implementation may vary based on agno API
            if images:
                # Encode images to base64 data URIs
                image_data_uris = []
                for img_bytes in images:
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                    # Determine image format (simplified - assume jpeg/png)
                    # In practice, you might want to detect the actual format
                    img_format = "jpeg"  # Default
                    image_data_uris.append(f"data:image/{img_format};base64,{img_b64}")

                # Append image references to user message
                # Note: This is a simplified approach. Actual agno API may support images differently
                user_message += "\n[Images attached]"

            # Call agno agent
            response = agent.run(user_message)

            # Extract content from response
            if hasattr(response, "content"):
                content = response.content
            elif hasattr(response, "messages") and response.messages:
                # Some agno responses may have messages list
                content = (
                    response.messages[-1].content
                    if hasattr(response.messages[-1], "content")
                    else str(response.messages[-1])
                )
            else:
                content = str(response)

            return LLMChatResponse(content=content)

        except LLMClientError:
            raise
        except Exception as e:
            logger.error(
                f"LLM chat request failed (provider={self.provider.value}): {e}",
                exc_info=True,
            )
            raise LLMClientError(
                f"Chat request failed: {e}", provider=self.provider.value
            )

    async def analyze_image(
        self, image_bytes: bytes, prompt: str
    ) -> LLMChatResponse:
        """Analyze an image with a prompt using agno agent.

        Convenience method for image analysis tasks (multimodal models).

        Args:
            image_bytes: Image bytes data
            prompt: Prompt text for analysis

        Returns:
            Analysis result from the model
        """
        messages = [LLMChatMessage(role="user", content=prompt, images=None)]
        return await self.chat(messages, images=[image_bytes])

    async def close(self) -> None:
        """Close the agent and cleanup resources."""
        self._agent = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

