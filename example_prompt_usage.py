#!/usr/bin/env python3
"""
Example script showing how to use the prompt manager from any repository.

This demonstrates various ways to get user prompts dynamically for orchestration workflows.
"""

import os
import sys

# Add the main-code directory to Python path to import from src
sys.path.append('/Users/saivishwasgooty/Documents/Projects/Hackathon/main-code')

from src.utils.prompt_manager import get_user_prompt, PromptManager


def example_interactive_usage():
    """Example: Interactive prompt input"""
    print("=== Interactive Prompt Example ===")
    prompt = get_user_prompt("interactive")
    print(f"Got prompt: {prompt}")
    return prompt


def example_preset_usage():
    """Example: Using preset prompts"""
    print("\n=== Preset Prompt Examples ===")
    
    # Use a built-in preset
    prompt1 = get_user_prompt("preset", prompt_key="todo_app")
    print(f"Todo app prompt: {prompt1}")
    
    prompt2 = get_user_prompt("preset", prompt_key="blog_app")
    print(f"Blog app prompt: {prompt2}")
    
    # Try a non-existent preset (falls back to default)
    prompt3 = get_user_prompt("preset", prompt_key="nonexistent")
    print(f"Fallback prompt: {prompt3}")
    
    return prompt1


def example_custom_usage():
    """Example: Custom prompt"""
    print("\n=== Custom Prompt Example ===")
    custom_prompt = "Build a machine learning pipeline with data ingestion, model training, and API serving using Python and FastAPI."
    prompt = get_user_prompt("custom", custom_prompt=custom_prompt)
    print(f"Custom prompt: {prompt}")
    return prompt


def example_env_usage():
    """Example: Environment variable prompt"""
    print("\n=== Environment Variable Example ===")
    
    # Set environment variable
    os.environ["ORCHESTRATION_PROMPT"] = "Create a microservices architecture with API gateway, service discovery, and monitoring."
    
    prompt = get_user_prompt("env")
    print(f"Environment prompt: {prompt}")
    
    # Clean up
    del os.environ["ORCHESTRATION_PROMPT"]
    return prompt


def example_advanced_usage():
    """Example: Advanced usage with PromptManager class"""
    print("\n=== Advanced PromptManager Usage ===")
    
    manager = PromptManager()
    
    # Add custom presets
    manager.add_preset_prompt("ml_app", "Build a machine learning web application with model serving and real-time predictions.")
    manager.add_preset_prompt("game_app", "Create a multiplayer web-based game with real-time communication and leaderboards.")
    
    # List all available presets
    presets = manager.list_presets()
    print("Available presets:")
    for key, desc in presets.items():
        print(f"  {key}: {desc[:60]}{'...' if len(desc) > 60 else ''}")
    
    # Use the new preset
    prompt = manager.get_user_prompt("preset", prompt_key="ml_app")
    print(f"\nUsing ML app preset: {prompt}")
    
    return prompt


def example_command_line_usage():
    """Example: Command line usage"""
    print("\n=== Command Line Usage Examples ===")
    print("You can run this script with a prompt as an argument:")
    print("python example_prompt_usage.py \"Build a social media platform\"")
    print("python example_prompt_usage.py \"Create an e-commerce store with payment integration\"")
    
    if len(sys.argv) > 1:
        from src.utils.prompt_manager import get_prompt_from_args
        prompt = get_prompt_from_args()
        print(f"Command line prompt: {prompt}")
        return prompt
    else:
        print("No command line arguments provided.")
        return None


def run_orchestration_with_prompt(prompt: str, project_name: str = "example_project"):
    """
    Example function showing how you might use the prompt in an orchestration workflow.
    This is just a placeholder - replace with your actual orchestration logic.
    """
    print(f"\n🚀 Running orchestration workflow...")
    print(f"Project: {project_name}")
    print(f"Prompt: {prompt}")
    print("(This would normally call your orchestration engine)")
    
    # Here you would normally do:
    # engine = OrchestrationEngine(workspace, llm_factory, tool_service)
    # result = engine.run_full_workflow(prompt, project_name=project_name)


if __name__ == "__main__":
    print("🎯 Prompt Manager Usage Examples")
    print("=" * 50)
    
    # Try command line first
    cmd_prompt = example_command_line_usage()
    if cmd_prompt:
        run_orchestration_with_prompt(cmd_prompt, "cmd_project")
        exit(0)
    
    # If no command line args, show all examples
    print("\nRunning all examples...\n")
    
    # Show different usage patterns
    example_preset_usage()
    example_custom_usage() 
    example_env_usage()
    example_advanced_usage()
    
    print("\n" + "=" * 50)
    print("Choose a method to get a prompt for orchestration:")
    print("1. Interactive (ask for input)")
    print("2. Use preset 'todo_app'")
    print("3. Use preset 'blog_app'")
    print("4. Custom prompt")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        prompt = get_user_prompt("interactive")
    elif choice == "2":
        prompt = get_user_prompt("preset", prompt_key="todo_app")
    elif choice == "3":
        prompt = get_user_prompt("preset", prompt_key="blog_app")
    elif choice == "4":
        custom = input("Enter custom prompt: ").strip()
        prompt = get_user_prompt("custom", custom_prompt=custom)
    else:
        prompt = get_user_prompt("preset", prompt_key="todo_app")
    
    print(f"\n✅ Final prompt selected: {prompt}")
    run_orchestration_with_prompt(prompt)
