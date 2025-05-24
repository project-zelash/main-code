from src.repository.llm.base_language_model import BaseLanguageModel
import google.generativeai as genai

class GeminiLLM(BaseLanguageModel):
    """
    Google Gemini language model implementation.
    """
    
    def __init__(self, model="gemini-1.5-pro", api_key=None, temperature=0.7):
        """
        Constructor for Gemini client.
        
        Args:
            model: Gemini model identifier (e.g., "gemini-1.5-pro").
            api_key: Google AI API key.
            temperature: Float controlling response randomness.
        """
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        
        # Initialize Gemini API client
        if api_key:
            genai.configure(api_key=api_key)
    
    def chat(self, messages, tools=None):
        """
        Implementation for Gemini's API.
        
        Args:
            messages: List of message dictionaries with role and content.
            tools: Optional list of tools available to the model.
            
        Returns:
            Response from the Gemini language model.
        """
        # Convert standard message format to Gemini format
        gemini_messages = self._convert_messages(messages)
        
        # Initialize model
        model = genai.GenerativeModel(
            model_name=self.model,
            generation_config={"temperature": self.temperature}
        )
        
        # Handle tools if provided
        if tools:
            # Convert tools to Gemini function calling format
            tool_config = self._convert_tools(tools)
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config={"temperature": self.temperature},
                tools=tool_config
            )
        
        # Create chat session and send messages
        chat = model.start_chat()
        response = chat.send_message(gemini_messages)
        
        # Format response for consistency with other LLMs
        formatted_response = self._format_response(response)
        
        return formatted_response
    
    def _convert_messages(self, messages):
        """
        Convert standard message format to Gemini format.
        
        Args:
            messages: List of message dictionaries with role and content.
            
        Returns:
            Messages formatted for Gemini's API.
        """
        # Gemini has a different handling for chat history
        # For simple implementation, concatenate all messages into a single prompt
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                # Prepend system message as instructions
                prompt_parts.insert(0, f"Instructions: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n".join(prompt_parts)
    
    def _convert_tools(self, tools):
        """
        Convert tools to Gemini function calling format.
        
        Args:
            tools: List of tool dictionaries.
            
        Returns:
            Tools formatted for Gemini's API.
        """
        gemini_tools = []
        
        for tool in tools:
            # Extract tool information
            name = tool.get("name")
            description = tool.get("description")
            parameters = tool.get("parameters", {})
            
            # Create Gemini tool definition
            gemini_tool = {
                "function_declarations": [
                    {
                        "name": name,
                        "description": description,
                        "parameters": parameters
                    }
                ]
            }
            
            gemini_tools.append(gemini_tool)
        
        return gemini_tools
    
    def _format_response(self, gemini_response):
        """
        Format Gemini response to match the standard format.
        
        Args:
            gemini_response: Response from Gemini API.
            
        Returns:
            Standardized response format.
        """
        # Extract the text content from Gemini response
        content = gemini_response.text
        
        # Check if there are function calls (tool calls) in the response
        function_calls = []
        if hasattr(gemini_response, 'candidates') and gemini_response.candidates:
            for candidate in gemini_response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            function_calls.append({
                                "name": part.function_call.name,
                                "arguments": part.function_call.args
                            })
        
        # Construct standardized response
        response = {
            "content": content,
            "role": "assistant"
        }
        
        if function_calls:
            response["tool_calls"] = function_calls
        
        return response