#!/bin/bash
# Test script for automation pipeline

echo "🚀 Starting automation pipeline test..."

# Activate virtual environment
source venv/bin/activate

# Set dummy API keys if not already set (these won't actually be used for this test)
export GEMINI_API_KEY=${GEMINI_API_KEY:-"dummy_key"}
export OPENAI_API_KEY=${OPENAI_API_KEY:-"dummy_key"}
export ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-"dummy_key"}

# Set model names
export GEMINI_MODEL="gemini-1.5-flash"
export OPENAI_MODEL="gpt-4o"
export ANTHROPIC_MODEL="claude-3-sonnet"

# Run the custom test automation script
echo "🧪 Running test for HTML buttons project..."
python test_automation_pipeline.py

# Show the result summary
echo "✅ Test completed!"
