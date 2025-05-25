#!/bin/bash

# Demo script for the Complete Automation Workflow System
# This script demonstrates the key features and capabilities

echo "🚀 Complete Automation Workflow System Demo"
echo "============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Set up demo directory
DEMO_DIR="automation_demo_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR"

echo ""
echo "📁 Demo directory created: $DEMO_DIR"
echo ""

# Copy automation script to demo directory
cp ../automation_main.py .
cp -r ../src .
cp -r ../examples .

echo "1️⃣ Creating example batch configuration..."
python3 automation_main.py create-example-config --output demo_batch.json
echo "✅ Example configuration created: demo_batch.json"
echo ""

echo "2️⃣ Demonstrating single workflow (React Todo App)..."
echo "This will generate, deploy, and test a React todo application"
echo ""

# Run single workflow with a simple project
python3 automation_main.py generate-deploy-test \
  --prompt "Create a simple React counter app with increment and decrement buttons" \
  --project-type react \
  --test-scenarios \
    "Test counter displays initial value of 0" \
    "Test increment button increases counter" \
    "Test decrement button decreases counter"

echo ""
echo "3️⃣ Listing workflow history..."
python3 automation_main.py list-workflows
echo ""

echo "4️⃣ Demonstrating batch workflow..."
echo "Running simple batch configuration with 2 projects"
echo ""

# Run batch workflow with simple configuration
python3 automation_main.py batch-workflow --config examples/batch_config_simple.json

echo ""
echo "5️⃣ Final workflow history after batch processing..."
python3 automation_main.py list-workflows
echo ""

echo "6️⃣ Cleanup demonstration..."
echo "Cleaning up all generated workflows..."
python3 automation_main.py cleanup --all
echo ""

echo "🎉 Demo completed successfully!"
echo ""
echo "📁 Demo files location: $(pwd)"
echo "📋 Available example configurations:"
echo "   - demo_batch.json (generated)"
echo "   - examples/batch_config_simple.json"
echo "   - examples/batch_config_comprehensive.json"
echo ""
echo "🔄 To run your own workflows:"
echo "   python3 automation_main.py generate-deploy-test --prompt 'Your project idea'"
echo "   python3 automation_main.py batch-workflow --config your_config.json"
echo ""
echo "📖 For more information, see README_AUTOMATION.md"
