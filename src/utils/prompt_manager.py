"""
Prompt Manager Utility

This module provides utilities for managing user prompts dynamically
instead of hardcoding them in the orchestration workflow.
"""

import sys
from typing import Optional, Dict, Any


class PromptManager:
    """Manages user prompts for orchestration workflows."""
    
    def __init__(self):
        self.default_prompts = {
            "todo_app": "Build a simple to-do app with backend and frontend using FastAPI and React.",
            "blog_app": "Create a full-stack blog application with user authentication using Django and Vue.js.",
            "ecommerce": "Build an e-commerce platform with product catalog, shopping cart, and payment integration using Node.js and React.",
            "chat_app": "Develop a real-time chat application with websockets using Flask and vanilla JavaScript.",
            "api_service": "Create a REST API service with CRUD operations, authentication, and documentation using FastAPI.",
        }
    
    def get_user_prompt(self, method: str = "interactive", prompt_key: Optional[str] = None, custom_prompt: Optional[str] = None) -> str:
        """
        Get user prompt using specified method.
        
        Args:
            method: How to get the prompt ("interactive", "preset", "custom", "env")
            prompt_key: Key for preset prompt (if method="preset")
            custom_prompt: Direct prompt string (if method="custom")
            
        Returns:
            User prompt string
        """
        if method == "interactive":
            return self._get_interactive_prompt()
        elif method == "preset":
            return self._get_preset_prompt(prompt_key)
        elif method == "custom":
            return custom_prompt or self._get_interactive_prompt()
        elif method == "env":
            return self._get_env_prompt()
        else:
            raise ValueError(f"Unknown prompt method: {method}")
    
    def _get_interactive_prompt(self) -> str:
        """Get prompt through interactive user input."""
        print("\n🎯 Orchestration Workflow - User Prompt Input")
        print("=" * 50)
        
        # Show available preset options
        print("\nAvailable preset prompts:")
        for key, desc in self.default_prompts.items():
            print(f"  {key}: {desc[:80]}{'...' if len(desc) > 80 else ''}")
        
        print(f"\nOptions:")
        print("1. Enter a custom prompt")
        print("2. Use a preset prompt (enter key from above)")
        print("3. Use default todo app prompt")
        
        choice = input("\nYour choice (1/2/3): ").strip()
        
        if choice == "1":
            print("\nEnter your custom prompt:")
            prompt = input("> ").strip()
            if not prompt:
                print("Empty prompt provided, using default.")
                return self.default_prompts["todo_app"]
            return prompt
        
        elif choice == "2":
            preset_key = input("Enter preset key: ").strip()
            return self._get_preset_prompt(preset_key)
        
        elif choice == "3" or not choice:
            return self.default_prompts["todo_app"]
        
        else:
            print("Invalid choice, using default prompt.")
            return self.default_prompts["todo_app"]
    
    def _get_preset_prompt(self, key: Optional[str]) -> str:
        """Get a preset prompt by key."""
        if not key:
            print("No preset key provided, using default.")
            return self.default_prompts["todo_app"]
        
        if key in self.default_prompts:
            print(f"Using preset prompt: {key}")
            return self.default_prompts[key]
        else:
            print(f"Preset '{key}' not found. Available presets: {list(self.default_prompts.keys())}")
            return self.default_prompts["todo_app"]
    
    def _get_env_prompt(self) -> str:
        """Get prompt from environment variable."""
        import os
        prompt = os.getenv("ORCHESTRATION_PROMPT")
        if prompt:
            print("Using prompt from ORCHESTRATION_PROMPT environment variable.")
            return prompt
        else:
            print("ORCHESTRATION_PROMPT not set, falling back to interactive mode.")
            return self._get_interactive_prompt()
    
    def add_preset_prompt(self, key: str, prompt: str) -> None:
        """Add a new preset prompt."""
        self.default_prompts[key] = prompt
        print(f"Added preset prompt: {key}")
    
    def list_presets(self) -> Dict[str, str]:
        """Get all available preset prompts."""
        return self.default_prompts.copy()


def get_user_prompt(method: str = "interactive", **kwargs) -> str:
    """
    Convenience function to get user prompt.
    
    Args:
        method: "interactive", "preset", "custom", or "env"
        **kwargs: Additional arguments (prompt_key, custom_prompt)
    
    Returns:
        User prompt string
    
    Examples:
        # Interactive mode (asks user for input)
        prompt = get_user_prompt("interactive")
        
        # Use preset
        prompt = get_user_prompt("preset", prompt_key="todo_app")
        
        # Custom prompt
        prompt = get_user_prompt("custom", custom_prompt="Build a social media app")
        
        # From environment variable
        prompt = get_user_prompt("env")
    """
    manager = PromptManager()
    return manager.get_user_prompt(method, **kwargs)


def get_prompt_from_args() -> str:
    """
    Get prompt from command line arguments.
    Usage: python script.py "Your prompt here"
    """
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(f"Using command line prompt: {prompt}")
        return prompt
    else:
        print("No command line prompt provided, falling back to interactive mode.")
        return get_user_prompt("interactive")


if __name__ == "__main__":
    # Test the prompt manager
    manager = PromptManager()
    
    print("Testing Prompt Manager")
    print("=" * 30)
    
    # Test preset
    prompt1 = manager.get_user_prompt("preset", prompt_key="todo_app")
    print(f"Preset prompt: {prompt1}")
    
    # Test custom
    prompt2 = manager.get_user_prompt("custom", custom_prompt="Build a weather app")
    print(f"Custom prompt: {prompt2}")
    
    # List all presets
    print(f"Available presets: {list(manager.list_presets().keys())}")
