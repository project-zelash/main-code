from src.repository.llm.base_language_model import BaseLanguageModel
import google.generativeai as genai
import os

import re
import json


def extract_tool_code_block(response_text):
        """
        Extracts the code inside a ```tool_code ... ``` block from the response text.
        Returns the code as a string, or None if not found.
        """
        pattern = r"```tool_code\s*([\s\S]*?)```"
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
class GeminiLLM(BaseLanguageModel):
    """
    Google Gemini language model implementation.
    """
    
    def __init__(self, model="gemini-2.0-flash", api_key=None, temperature=0.7):
        """
        Constructor for Gemini client.
        
        Args:
            model: Gemini model identifier (e.g., "gemini-1.5-pro").
            api_key: Google AI API key.
            temperature: Float controlling response randomness.
        """
        self.model = model
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.temperature = temperature
        
        # Initialize Gemini API client
        if self.api_key:
            # Set environment variable for Google AI to use
            os.environ['GOOGLE_API_KEY'] = self.api_key
            genai.configure(api_key=self.api_key)
        else:
            raise ValueError("GEMINI_API_KEY not provided and not found in environment variables")
    
    def chat(self, messages, tools=None):
        """
        Implementation for Gemini's API using the new google.genai client.
        
        Args:
            messages: List of message dictionaries with role and content.
            tools: Optional list of tools available to the model.
            
        Returns:
            Response from the Gemini language model.
        """
        try:
            # Try to use the new google.genai client for function calling
            from google import genai as new_genai
            from google.genai import types
            
            # Configure the client
            client = new_genai.Client(api_key=self.api_key)
            
            # Handle tools if provided
            config = None
            if tools:
                gemini_tools = self._convert_tools_to_gemini_format(tools)
                config = types.GenerateContentConfig(
                    tools=gemini_tools,
                    temperature=self.temperature
                )
            else:
                config = types.GenerateContentConfig(temperature=self.temperature)
            
            # Send request
            response = client.models.generate_content(
                model=self.model,
                config=config,
                contents=messages
            )
            
            # Format response
            formatted_response = self._format_new_gemini_response(response)
            return formatted_response
            
        except ImportError:
            # Fallback to old genai client without function calling
            return self._chat_fallback(messages, tools)
        except Exception as e:
            # Fallback to old genai client if new one fails
            return self._chat_fallback(messages, tools)
    
    def _convert_tools_to_gemini_format(self, tools):
        """
        Convert tools to Gemini function declarations format.
        
        Args:
            tools: List of tool dictionaries.
            
        Returns:
            List of Gemini tools.
        """
        from google.genai import types
        
        function_declarations = []
        
        for tool in tools:
            # Handle both formats: direct tool object or nested function format
            if "function" in tool:
                # Standard OpenAI-style format
                func_def = tool["function"]
                name = func_def.get("name")
                description = func_def.get("description")
                parameters = func_def.get("parameters", {})
            else:
                # Direct format
                name = tool.get("name")
                description = tool.get("description")
                parameters = tool.get("parameters", {})
            
            # Create Gemini function declaration
            function_declaration = {
                "name": name,
                "description": description,
                "parameters": parameters
            }
            
            function_declarations.append(function_declaration)
        
        # Return Gemini Tool object
        return [types.Tool(function_declarations=function_declarations)]
    
    def _format_new_gemini_response(self, response):
        """
        Format new Gemini API response to match the standard format.
        
        Args:
            response: Response from new Gemini API.
            
        Returns:
            Standardized response format.
        """
        # Extract content and function calls
        content = ""
        function_calls = []
        
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        content += part.text
                    elif hasattr(part, 'function_call') and part.function_call:
                        function_calls.append({
                            "name": part.function_call.name,
                            "arguments": dict(part.function_call.args)
                        })
        
        # Construct standardized response
        response_dict = {
            "content": content,
        }
        
        if function_calls:
            response_dict["tool_calls"] = function_calls
        
        return response_dict
    
    def _parse_response_for_tools(self, response_text, tools):
        """
        Parse the response text for tool calls.
        
        Args:
            response_text: Text of the response from the model.
            tools: List of available tools for validation.
            
        Returns:
            Parsed response with tool call information.
        """
        # Look for tool call pattern
        tool_call_pattern = r'TOOL_CALL:\s*(\w+)\s*\nARGUMENTS:\s*(\{[\s\S]*?\})'
        matches = re.findall(tool_call_pattern, response_text, re.IGNORECASE)
        tool_calls = []
        content = response_text
        if matches:
            for tool_name, args_json in matches:
                try:
                    arguments = json.loads(args_json)
                except Exception:
                    arguments = {"raw": args_json}
                tool_calls.append({
                    "name": tool_name,
                    "arguments": arguments
                })
            # Remove all tool call blocks from the content
            content = re.sub(tool_call_pattern, '', response_text, flags=re.IGNORECASE).strip()
        response = {
            "content": content,
            "role": "assistant"
        }
        if tool_calls:
            response["tool_calls"] = tool_calls
        return response

    def _chat_fallback(self, messages, tools):
        """
        Fallback implementation using the old genai client without function calling.
        
        Args:
            messages: List of message dictionaries with role and content.
            tools: Optional list of tools (ignored in fallback).
            
        Returns:
            Response from the Gemini language model.
        """
        # Convert standard message format to simple text
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.insert(0, f"Instructions: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt = "\n".join(prompt_parts)
        
        # If tools are provided, add them as text descriptions
        if tools:
            tool_descriptions = []
            for tool in tools:
                if "function" in tool:
                    func_def = tool["function"]
                    name = func_def.get("name")
                    description = func_def.get("description")
                else:
                    name = tool.get("name")
                    description = tool.get("description")
                tool_descriptions.append(f"- {name}: {description}")
            
            prompt += f"\n\nAvailable tools:\n" + "\n".join(tool_descriptions)
            prompt += "\n\nIf you need to use a tool, please mention which tool you would use and why."
        
        # Initialize model and generate response
        model = genai.GenerativeModel(
            model_name=self.model,
            generation_config=genai.GenerationConfig(temperature=self.temperature)
        )
        
        try:
            response = model.generate_content(self._convert_messages_to_prompt(messages))
            # Always use _parse_response_for_tools to process the response
            return self._parse_response_for_tools(response.text, tools)
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def _format_tools_as_prompt(self, tools):
        """
        Format tools for prompt injection, adding strict examples for tool usage.
        
        Args:
            tools: List of tool dictionaries.
            
        Returns:
            Formatted string for prompt injection.
        """
        tool_descriptions = ["AVAILABLE TOOLS:"]
        for tool in tools:
            # Handle both formats: direct tool object or nested function format
            if "function" in tool:
                # Standard OpenAI-style format
                func_def = tool["function"]
                name = func_def.get("name")
                description = func_def.get("description")
                parameters = func_def.get("parameters", {})
            else:
                name = tool.get("name")
                description = tool.get("description")
                parameters = tool.get("parameters", {})
            param_info = ""
            if parameters and "properties" in parameters:
                param_list = []
                for param_name, param_def in parameters["properties"].items():
                    param_type = param_def.get("type", "string")
                    param_desc = param_def.get("description", "")
                    param_list.append(f"  - {param_name} ({param_type}): {param_desc}")
                if param_list:
                    param_info = f"\n  Parameters:\n" + "\n".join(param_list)
            tool_descriptions.append(f"- {name}: {description}{param_info}")
        # Add a strict, OS-specific example and negative instructions for bash tool usage on Windows
        tool_descriptions.append(
            "\nWhen you want to use the bash tool to show the current directory on Windows, respond ONLY in this format (no markdown, no explanation, no extra text):\n"
            "TOOL_CALL: bash\n"
            "ARGUMENTS: {\"command\": \"cd\"}\n"
            "For example, to show the current directory, respond exactly as above.\n"
            "Do NOT output: ```tool_code print(os.getcwd()) ``` or any Python code or markdown block.\n"
            "Do NOT use print(os.getcwd()), do NOT use pwd, do NOT use markdown, do NOT explain, do NOT add any extra text. Only output the tool call block as shown above."
        )
        return "\n".join(tool_descriptions)
    
    def _convert_messages_to_prompt(self, messages):
        """
        Convert a list of message dicts into a single prompt string for Gemini.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            
        Returns:
            A single prompt string.
        """
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                prompt_parts.append(f"SYSTEM: {content}")
            elif role == "user":
                prompt_parts.append(f"USER: {content}")
            elif role == "assistant":
                prompt_parts.append(f"ASSISTANT: {content}")
            else:
                prompt_parts.append(f"{role.upper()}: {content}")
        return "\n\n".join(prompt_parts)


