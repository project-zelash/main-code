from src.repository.llm.base_language_model import BaseLanguageModel
import os
import time

class OpenAILLM(BaseLanguageModel):
    """
    OpenAI language model implementation.
    """
    
    def __init__(self, model="gpt-4o", api_key=None, temperature=0.7):
        """
        Constructor for OpenAI client.
        
        Args:
            model: OpenAI model identifier (e.g., "gpt-4o").
            api_key: OpenAI API authentication key.
            temperature: Float controlling response randomness.
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key)
        
    def chat(self, messages, tools=None):
        """
        Implementation for OpenAI's API.
        
        Args:
            messages: List of message dictionaries with role and content.
            tools: Optional list of tools available to the model.
            
        Returns:
            Response from the OpenAI language model.
        """
        last_error = None
        for attempt in range(3):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                }
                if tools:
                    kwargs["tools"] = tools
                response = self.client.chat.completions.create(**kwargs)
                message = response.choices[0].message
                result = {"content": message.content or "", "role": "assistant"}
                if message.tool_calls:
                    result["tool_calls"] = [
                        {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        }
                        for call in message.tool_calls
                    ]
                return result
            except Exception as exc:
                last_error = exc
                if "rate" in str(exc).lower() or "429" in str(exc):
                    time.sleep(2 ** attempt)
                    continue
                break
        raise RuntimeError(f"OpenAI API error after retries: {last_error}")
