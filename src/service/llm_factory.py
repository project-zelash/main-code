from src.repository.llm.openai_llm import OpenAILLM
from src.repository.llm.anthropic_llm import AnthropicLLM
from src.repository.llm.bedrock_llm import BedrockLLM
from src.repository.llm.gemini_llm import GeminiLLM

class LLMFactory:
    """
    Factory service for creating LLM instances.
    """
    
    def __init__(self, config=None):
        """
        Initialize the LLM factory.
        
        Args:
            config: Configuration for default LLM settings.
        """
        self.config = config or {}
        
    def create_llm(self, provider, model=None, temperature=None, api_key=None, credentials=None):
        """
        Create an LLM instance based on specified parameters.
        
        Args:
            provider: LLM provider name ('openai', 'anthropic', 'bedrock', 'gemini').
            model: Model name (specific to provider).
            temperature: Temperature setting for generation.
            api_key: API key for the provider.
            credentials: AWS credentials for Bedrock.
            
        Returns:
            LLM instance.
        """
        # Get default values from config if not specified
        provider_config = self.config.get(provider, {})
        
        model = model or provider_config.get('model')
        temperature = temperature if temperature is not None else provider_config.get('temperature', 0.7)
        api_key = api_key or provider_config.get('api_key')
        credentials = credentials or provider_config.get('credentials')
        
        # Create LLM instance based on provider
        if provider == 'openai':
            if not model:
                model = 'gpt-4o'
            return OpenAILLM(model=model, api_key=api_key, temperature=temperature)
        
        elif provider == 'anthropic':
            if not model:
                model = 'claude-3-sonnet'
            return AnthropicLLM(model=model, api_key=api_key, temperature=temperature)
        
        elif provider == 'bedrock':
            if not model:
                model = 'anthropic.claude-v2'
            region_name = provider_config.get('region_name', 'us-east-1')
            return BedrockLLM(
                model=model, 
                region_name=region_name,
                credentials=credentials, 
                temperature=temperature
            )
        
        elif provider == 'gemini':
            if not model:
                model = 'gemini-1.5-pro'
            return GeminiLLM(model=model, api_key=api_key, temperature=temperature)
        
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def update_config(self, new_config):
        """
        Update the factory configuration.
        
        Args:
            new_config: New configuration to merge with existing.
            
        Returns:
            Updated configuration.
        """
        self.config.update(new_config)
        return self.config