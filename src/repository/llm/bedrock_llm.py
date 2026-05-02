from src.repository.llm.base_language_model import BaseLanguageModel
import json
import time

class BedrockLLM(BaseLanguageModel):
    """
    Amazon Bedrock language model implementation.
    """
    
    def __init__(self, model="anthropic.claude-v2", region_name="us-east-1", credentials=None, temperature=0.7):
        """
        Constructor for Bedrock client.
        
        Args:
            model: Bedrock model identifier (e.g., "anthropic.claude-v2").
            region_name: AWS region for Bedrock.
            credentials: AWS credentials object.
            temperature: Response randomness parameter.
        """
        self.model = model
        self.region_name = region_name
        self.credentials = credentials
        self.temperature = temperature
        import boto3
        kwargs = {"region_name": self.region_name}
        if credentials:
            kwargs.update(credentials)
        self.client = boto3.client("bedrock-runtime", **kwargs)
        
    def chat(self, messages, tools=None):
        """
        Implementation for Bedrock's API.
        
        Args:
            messages: List of message dictionaries with role and content.
            tools: Optional list of tools available to the model.
            
        Returns:
            Response from the Bedrock language model.
        """
        last_error = None
        for attempt in range(3):
            try:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4096,
                    "temperature": self.temperature,
                    "messages": self._convert_messages(messages),
                })
                response = self.client.invoke_model(modelId=self.model, body=body)
                payload = json.loads(response["body"].read())
                content = "".join(block.get("text", "") for block in payload.get("content", []))
                return {"content": content, "role": "assistant"}
            except Exception as exc:
                last_error = exc
                if "throttl" in str(exc).lower() or "rate" in str(exc).lower():
                    time.sleep(2 ** attempt)
                    continue
                break
        raise RuntimeError(f"Bedrock API error after retries: {last_error}")
    
    def _convert_messages(self, messages):
        """
        Converts standard message format to Bedrock format.
        
        Args:
            messages: List of message dictionaries with role and content.
            
        Returns:
            Messages formatted for Bedrock's API.
        """
        converted = []
        system_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                system_parts.append(content)
            else:
                converted.append({
                    "role": role if role in {"user", "assistant"} else "user",
                    "content": [{"type": "text", "text": content}],
                })
        if system_parts:
            converted.insert(0, {"role": "user", "content": [{"type": "text", "text": "\n\n".join(system_parts)}]})
        return converted
