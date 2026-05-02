from src.repository.llm.base_language_model import BaseLanguageModel
import os
import time

class AnthropicLLM(BaseLanguageModel):
    """
    Anthropic Claude language model implementation.
    """
    
    def __init__(self, model="claude-3-sonnet", api_key=None, temperature=0.7):
        """
        Constructor for Anthropic client.
        
        Args:
            model: Claude model identifier (e.g., "claude-3-sonnet").
            api_key: Anthropic API authentication key.
            temperature: Float controlling response randomness.
        """
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.temperature = temperature
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        from anthropic import Anthropic
        self.client = Anthropic(api_key=self.api_key)
        
    def chat(self, messages, tools=None):
        """
        Implementation for Claude's API.
        
        Args:
            messages: List of message dictionaries with role and content.
            tools: Optional list of tools available to the model.
            
        Returns:
            Response from the Anthropic language model.
        """
        system = ""
        anthropic_messages = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                system = content if not system else f"{system}\n\n{content}"
            else:
                anthropic_messages.append({"role": role if role in {"user", "assistant"} else "user", "content": content})

        last_error = None
        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=self.temperature,
                    system=system or None,
                    messages=anthropic_messages,
                )
                content = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
                return {"content": content, "role": "assistant"}
            except Exception as exc:
                last_error = exc
                if "rate" in str(exc).lower() or "429" in str(exc):
                    time.sleep(2 ** attempt)
                    continue
                break
        raise RuntimeError(f"Anthropic API error after retries: {last_error}")
