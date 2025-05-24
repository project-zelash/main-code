# Browser Agent Helper Functions

This directory contains helper functions for working with the Browser AI Agent outside of the WebUI.

## Overview

These helper functions provide ways to programmatically control the browser agent, allowing you to:
- Run browser tasks with a visible browser window
- Configure model settings
- Use utility functions for formatting and printing

## Available Modules

### `browser_task_runner.py`

This is the main script for running browser agent tasks directly, without needing the WebUI. It opens a visible browser window and performs tasks autonomously.

**Features:**
- Uses Google Gemini 2.0 Flash as the default language model
- Opens a visible Chrome browser window
- Performs tasks similar to the WebUI's "Submit Task" button
- Shows detailed step-by-step progress in the terminal

**Usage:**

1. **Run with default task** (search for Andhra restaurants in Bangalore):
   ```bash
   python src/helpers/browser_task_runner.py
   ```

2. **Run with custom task:**
   ```bash
   python src/helpers/browser_task_runner.py "Go to amazon.com and search for headphones"
   ```

### `model_config.py`

Contains functions for configuring the language model settings.

**Usage:**
```python
from src.helpers.model_config import set_default_model

# Set Google Gemini 2.0 Flash as the default model
set_default_model()
```

### `utils.py`

Contains utility functions for formatting and printing.

**Usage:**
```python
from src.helpers.utils import print_colored

# Print colored text to the console
print_colored("Task completed successfully!", "green")
```

## Example: Using Browser Agent in Your Own Script

If you want to use the browser agent in your own Python script, you can import the necessary functions:

```python
import asyncio
from src.helpers.browser_task_runner import run_browser_task

async def main():
    # Define your task
    task = "Go to github.com and search for 'browser-use'"
    
    # Run the browser agent with your task
    await run_browser_task(task)

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting

If you encounter any issues:

1. **Environment Variables**: Make sure your `.env` file contains the necessary API keys:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

2. **Dependencies**: Ensure all dependencies are installed:
   ```bash
   pip install browser-use playwright
   ```

3. **Playwright Installation**: If browser doesn't launch, make sure Playwright is installed:
   ```bash
   playwright install
   ```

4. **Visible Browser**: If you don't see a browser window, ensure `headless=False` is set in the browser configuration.

## Notes

- The browser agent uses the Google Gemini 2.0 Flash model by default
- Tasks are executed autonomously with the agent making decisions based on the task description
- The agent can see and interact with web pages using computer vision capabilities
