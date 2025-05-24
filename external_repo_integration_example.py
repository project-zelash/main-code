"""
Integration example: How to use the prompt manager from any external repository.

This shows how you can import and use the prompt functionality
from a different project/repository.
"""

import sys
import os

# Method 1: Add the main-code path to import the prompt manager
MAIN_CODE_PATH = "/Users/saivishwasgooty/Documents/Projects/Hackathon/main-code"
if MAIN_CODE_PATH not in sys.path:
    sys.path.append(MAIN_CODE_PATH)

# Now you can import the prompt utilities
from src.utils.prompt_manager import get_user_prompt, PromptManager


class ExternalOrchestrator:
    """Example orchestrator class that uses the prompt manager."""
    
    def __init__(self):
        self.prompt_manager = PromptManager()
        
        # Add project-specific presets
        self.prompt_manager.add_preset_prompt(
            "data_pipeline", 
            "Build a data processing pipeline with ETL, data validation, and reporting using Python and Apache Airflow."
        )
        self.prompt_manager.add_preset_prompt(
            "mobile_app", 
            "Create a cross-platform mobile application with user authentication and real-time sync using React Native."
        )
    
    def run_workflow_interactive(self):
        """Run workflow with interactive prompt input."""
        print("🎯 External Repository Orchestration")
        print("=" * 40)
        
        prompt = self.prompt_manager.get_user_prompt("interactive")
        return self._execute_workflow(prompt)
    
    def run_workflow_preset(self, preset_key: str):
        """Run workflow with a preset prompt."""
        prompt = self.prompt_manager.get_user_prompt("preset", prompt_key=preset_key)
        return self._execute_workflow(prompt)
    
    def run_workflow_custom(self, custom_prompt: str):
        """Run workflow with a custom prompt."""
        prompt = self.prompt_manager.get_user_prompt("custom", custom_prompt=custom_prompt)
        return self._execute_workflow(prompt)
    
    def _execute_workflow(self, prompt: str):
        """Execute the actual workflow (placeholder)."""
        print(f"\n🚀 Executing workflow with prompt:")
        print(f"   {prompt}")
        print("\n✅ Workflow completed!")
        return {"success": True, "prompt": prompt}


def quick_orchestration(method: str = "interactive", **kwargs):
    """
    Quick function to run orchestration from any repository.
    
    Usage examples:
        # Interactive mode
        quick_orchestration("interactive")
        
        # Preset mode
        quick_orchestration("preset", prompt_key="todo_app")
        
        # Custom mode
        quick_orchestration("custom", custom_prompt="Build a weather app")
        
        # Environment variable mode
        quick_orchestration("env")
    """
    prompt = get_user_prompt(method, **kwargs)
    print(f"🎯 Quick Orchestration")
    print(f"📝 Prompt: {prompt}")
    print("🚀 (This would run your orchestration workflow)")
    return prompt


if __name__ == "__main__":
    # Example usage from external repository
    
    print("External Repository Integration Example")
    print("=" * 50)
    
    # Method 1: Using the orchestrator class
    orchestrator = ExternalOrchestrator()
    
    print("\nAvailable presets in external orchestrator:")
    for key, prompt in orchestrator.prompt_manager.list_presets().items():
        print(f"  {key}: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")
    
    print("\nChoose how to run the workflow:")
    print("1. Interactive prompt")
    print("2. Use 'todo_app' preset")
    print("3. Use 'data_pipeline' preset")
    print("4. Quick orchestration")
    print("5. Custom prompt")
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        result = orchestrator.run_workflow_interactive()
    elif choice == "2":
        result = orchestrator.run_workflow_preset("todo_app")
    elif choice == "3":
        result = orchestrator.run_workflow_preset("data_pipeline")
    elif choice == "4":
        prompt = quick_orchestration("interactive")
    elif choice == "5":
        custom = input("Enter custom prompt: ").strip()
        result = orchestrator.run_workflow_custom(custom)
    else:
        print("Invalid choice, using interactive mode.")
        result = orchestrator.run_workflow_interactive()
    
    print(f"\n✅ Integration example completed!")
