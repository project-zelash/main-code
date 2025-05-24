class BaseLanguageModel:
    """
    Abstract interface for language model providers.
    """
    
    def chat(self, messages, tools=None):
        """
        Abstract method for generating completions.
        
        Args:
            messages: List of message dictionaries with role and content.
            tools: Optional list of tools available to the model.
            
        Returns:
            Response from the language model.
        """
        raise NotImplementedError("Subclasses must implement this method")