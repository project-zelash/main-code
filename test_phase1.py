#!/usr/bin/env python3
"""
Test script for Phase 1 components: ToolCallAgent, BashTool, PlanningTool
This tests the foundation of our agent system before moving to the next phase.
"""

import sys
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("📁 Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed. Install it with: pip install python-dotenv")
    print("⚠️ For now, trying to load environment variables manually...")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.repository.agent.tool_call_agent import ToolCallAgent
from src.repository.tools.bash_tool import BashTool
from src.repository.tools.planning_tool import PlanningTool
from src.repository.llm.gemini_llm import GeminiLLM

def test_basic_functionality():
    """Test basic functionality without LLM integration first"""
    print("🧪 Testing Phase 1 Components - Basic Functionality")
    print("=" * 50)
    
    # Test BashTool
    print("\n1. Testing BashTool...")
    bash_tool = BashTool()
    
    # Test safe commands
    safe_commands = [
        "echo Hello World",
        "dir" if os.name == 'nt' else "ls",
        "python --version"
    ]
    
    for cmd in safe_commands:
        print(f"   Executing: {cmd}")
        result = bash_tool.run(cmd)
        print(f"   Result: {result[:100]}...")
        print()
    
    # Test security (should be blocked)
    print("   Testing security (should be blocked):")
    dangerous_cmd = "rm -rf /"
    result = bash_tool.run(dangerous_cmd)
    print(f"   Dangerous command result: {result}")
    print()
    
    # Test PlanningTool
    print("2. Testing PlanningTool...")
    planning_tool = PlanningTool()
    
    # Create a plan
    print("   Creating a plan...")
    plan_result = planning_tool.run(
        action="create_plan",
        goal="Test the Zelash AI Framework",
        steps=[
            "Implement basic agent functionality",
            "Test tool integration", 
            "Verify LLM connectivity",
            "Create simple demo"
        ]
    )
    print(f"   Plan created: {plan_result['plan_id']}")
    
    # Check status
    plan_id = plan_result['plan_id']
    status_result = planning_tool.run(action="check_status", plan_id=plan_id)
    print(f"   Plan status: {status_result['status']}")
    
    # Complete a step
    complete_result = planning_tool.run(action="complete_step", plan_id=plan_id, step_index=0)
    print(f"   Completed step: {complete_result['step_completed']}")
    
    print("\n✅ Basic functionality tests completed!")
    return True

def test_with_mock_llm():
    """Test agent with a mock LLM to verify tool calling flow"""
    print("\n🤖 Testing ToolCallAgent with Mock LLM")
    print("=" * 50)
    
    class MockLLM:
        """Simple mock LLM for testing tool calling flow"""
        def chat(self, messages, tools=None):
            # Simulate LLM deciding to use bash tool
            if tools and any(tool['function']['name'] == 'bash' for tool in tools):
                return {
                    'content': 'I need to check the current directory.',
                    'tool_calls': [
                        {
                            'name': 'bash',
                            'arguments': {'command': 'echo "Current directory: $(pwd)"'}
                        }
                    ]
                }
            else:
                return {
                    'content': 'I have completed the task successfully.',
                    'tool_calls': []
                }
    
    # Create agent with mock LLM
    mock_llm = MockLLM()
    tools = [BashTool(), PlanningTool()]
    
    agent = ToolCallAgent(
        llm=mock_llm,
        tools=tools,
        system_prompt="You are a helpful assistant that can use tools.",
        name="TestAgent",
        verbose=True
    )
    
    # Test agent execution
    print("   Testing agent with query...")
    response = agent.run("Please check what directory we're in")
    print(f"   Agent response: {response}")
    
    print("\n✅ Mock LLM test completed!")
    return True

def test_with_real_llm():
    """Test with real Gemini LLM if API key is available"""
    print("\n🌟 Testing with Real Gemini LLM")
    print("=" * 50)
    
    # Check if Gemini API key is available
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("   ⚠️ GEMINI_API_KEY not found in environment variables")
        print("   Skipping real LLM test...")
        return False
    
    try:
        # Create real LLM instance
        gemini_llm = GeminiLLM(model="gemini-2.0-flash", temperature=0.1)
        
        # Create agent with real LLM
        tools = [BashTool(), PlanningTool()]
        agent = ToolCallAgent(
            llm=gemini_llm,
            tools=tools,
            system_prompt="You are a helpful assistant. Use tools when appropriate to complete tasks.",
            name="GeminiAgent",
            verbose=True
        )
        
        # Test with a simple query
        print("   Testing with real LLM...")
        # Strongly specify the OS and required format
        prompt = (
            "My operating system is Windows. "
            "Please get the current directory using the bash tool and merge the code using git commands to browser-use-integration branch"
            "Respond ONLY in this format (no markdown, no explanation, no extra text):\n"
            "TOOL_CALL: bash\n"
            "ARGUMENTS: {\"command\": \"cd\"}\n"
            "Do NOT output code, markdown, or explanations. Only output the tool call block as shown above."
            "except for when you have finished executing the tool call, then you can output the result of the command."
            "do not try to access the github link, the github repo is already connected to github"
        )
        response = agent.run(prompt)
        print(f"   Agent response: {response}")
        
        print("\n✅ Real LLM test completed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Real LLM test failed: {str(e)}")
        return False

def main():
    """Main test runner"""
    print("🚀 ZELASH AI FRAMEWORK - Phase 1 Testing")
    print("Testing ToolCallAgent, BashTool, and PlanningTool")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Run tests
    try:
        if test_basic_functionality():
            tests_passed += 1
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
    
    try:
        if test_with_mock_llm():
            tests_passed += 1
    except Exception as e:
        print(f"❌ Mock LLM test failed: {e}")
    
    try:
        if test_with_real_llm():
            tests_passed += 1
    except Exception as e:
        print(f"❌ Real LLM test failed: {e}")
    
    # Results
    print("\n" + "=" * 60)
    print(f"🎯 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed >= 2:
        print("✅ PHASE 1 FOUNDATION: READY TO PROCEED!")
        print("🚀 Ready for Phase 2: Service Layer Development")
        return True
    else:
        print("❌ PHASE 1 NEEDS FIXES BEFORE PROCEEDING")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)