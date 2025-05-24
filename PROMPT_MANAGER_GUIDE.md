# 🎯 Dynamic Prompt Manager for Orchestration Workflows

## Overview

This system provides a flexible way to handle user prompts for orchestration workflows instead of hardcoding them. You can now use it from any repository with multiple input methods.

## ✅ What's Been Implemented

### 1. **Prompt Manager Module** (`src/utils/prompt_manager.py`)
- **PromptManager class**: Manages preset and custom prompts
- **get_user_prompt()**: Convenience function for getting prompts
- **get_prompt_from_args()**: Command line argument support
- **Built-in presets**: todo_app, blog_app, ecommerce, chat_app, api_service

### 2. **Updated Workflow Script** (`manual_orchestration_workflow_check.py`)
- Now uses dynamic prompt input instead of hardcoded prompts
- Supports command line arguments
- Interactive prompt selection

### 3. **Example Scripts**
- `example_prompt_usage.py`: Comprehensive usage examples
- `external_repo_integration_example.py`: Shows how to use from other repositories

## 🚀 Usage Methods

### **Method 1: Interactive Mode**
```bash
cd /Users/saivishwasgooty/Documents/Projects/Hackathon/main-code && source venv_312/bin/activate && PYTHONPATH=. python src/repository/mcp/run_mcp_server.py & sleep 3 && PYTHONPATH=. python manual_orchestration_workflow_check.py
```

This will show an interactive menu:
```
🎯 Orchestration Workflow - User Prompt Input
==================================================

Available preset prompts:
  todo_app: Build a simple to-do app with backend and frontend using FastAPI and React.
  blog_app: Create a full-stack blog application with user authentication using Django and V...
  ecommerce: Build an e-commerce platform with product catalog, shopping cart, and payment in...
  chat_app: Develop a real-time chat application with websockets using Flask and vanilla Jav...
  api_service: Create a REST API service with CRUD operations, authentication, and documentatio...

Options:
1. Enter a custom prompt
2. Use a preset prompt (enter key from above)
3. Use default todo app prompt

Your choice (1/2/3):
```

### **Method 2: Command Line Arguments**
```bash
cd /Users/saivishwasgooty/Documents/Projects/Hackathon/main-code && source venv_312/bin/activate && PYTHONPATH=. python src/repository/mcp/run_mcp_server.py & sleep 3 && PYTHONPATH=. python manual_orchestration_workflow_check.py "Build a machine learning web application with model training, prediction API, and real-time dashboard using Python and Streamlit"
```

### **Method 3: Programmatic Usage**
```python
from src.utils.prompt_manager import get_user_prompt

# Interactive mode
prompt = get_user_prompt("interactive")

# Use preset
prompt = get_user_prompt("preset", prompt_key="todo_app")

# Custom prompt
prompt = get_user_prompt("custom", custom_prompt="Build a social media app")

# From environment variable
prompt = get_user_prompt("env")  # Uses ORCHESTRATION_PROMPT env var
```

### **Method 4: Environment Variable**
```bash
export ORCHESTRATION_PROMPT="Create a microservices architecture with API gateway"
cd /Users/saivishwasgooty/Documents/Projects/Hackathon/main-code && source venv_312/bin/activate && PYTHONPATH=. python src/repository/mcp/run_mcp_server.py & sleep 3 && PYTHONPATH=. python manual_orchestration_workflow_check.py
```

## 📂 Integration from External Repositories

### **Option 1: Direct Import** (if you can modify Python path)
```python
import sys
sys.path.append('/Users/saivishwasgooty/Documents/Projects/Hackathon/main-code')

from src.utils.prompt_manager import get_user_prompt, PromptManager

# Use it in your orchestration workflow
prompt = get_user_prompt("interactive")
```

### **Option 2: Copy the Module**
Copy `src/utils/prompt_manager.py` to your repository and import it locally.

### **Option 3: Create a Symlink**
```bash
ln -s /Users/saivishwasgooty/Documents/Projects/Hackathon/main-code/src/utils/prompt_manager.py your_repo/prompt_manager.py
```

## 🎯 Available Preset Prompts

1. **todo_app**: "Build a simple to-do app with backend and frontend using FastAPI and React."
2. **blog_app**: "Create a full-stack blog application with user authentication using Django and Vue.js."
3. **ecommerce**: "Build an e-commerce platform with product catalog, shopping cart, and payment integration using Node.js and React."
4. **chat_app**: "Develop a real-time chat application with websockets using Flask and vanilla JavaScript."
5. **api_service**: "Create a REST API service with CRUD operations, authentication, and documentation using FastAPI."

## 📝 Custom Presets

You can add your own presets programmatically:

```python
from src.utils.prompt_manager import PromptManager

manager = PromptManager()
manager.add_preset_prompt("ml_app", "Build a machine learning pipeline with data processing, model training, and API serving.")

prompt = manager.get_user_prompt("preset", prompt_key="ml_app")
```

## ✅ Test Results

**Successfully tested with:**
- ✅ Interactive prompt selection
- ✅ Command line argument prompts
- ✅ Preset prompt usage
- ✅ Custom ML application generation (28 files created)
- ✅ Full orchestration workflow completion

**Recent successful runs:**
1. **Todo App** (preset): 21 files generated, 7/7 tasks successful
2. **ML Application** (custom): 28 files generated, 8/8 tasks successful

## 🔧 Advanced Usage

### **Custom PromptManager with Additional Presets**
```python
from src.utils.prompt_manager import PromptManager

class MyOrchestrator:
    def __init__(self):
        self.prompt_manager = PromptManager()
        
        # Add domain-specific presets
        self.prompt_manager.add_preset_prompt(
            "fintech_app", 
            "Build a fintech application with payment processing, transaction history, and compliance reporting using Python and React."
        )
        
    def run_with_preset(self, preset_key):
        prompt = self.prompt_manager.get_user_prompt("preset", prompt_key=preset_key)
        return self.execute_workflow(prompt)
```

### **Validation and Error Handling**
```python
from src.utils.prompt_manager import get_user_prompt

try:
    prompt = get_user_prompt("preset", prompt_key="nonexistent")
    # Will fallback to default prompt with warning
except Exception as e:
    print(f"Error getting prompt: {e}")
    prompt = "Build a simple web application"  # fallback
```

## 🎉 Summary

The dynamic prompt manager provides a flexible, reusable way to handle user input for orchestration workflows. It supports multiple input methods, preset management, and can be easily integrated into any repository or workflow system.

**No more hardcoded prompts!** 🚀
