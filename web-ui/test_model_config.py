#!/usr/bin/env python3
"""
Test script for model_config helper functions
"""

import os
import sys

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Try direct import
    from src.helpers.model_config import set_default_model, get_current_model_config
    
    print("Testing model_config functions:")
    
    # Test set_default_model
    print("Setting default model...")
    config = set_default_model(
        provider="google",
        model_name="gemini-2.0-flash",
        temperature=0.7
    )
    print(f"Default model set: {config}")
    
    # Test get_current_model_config
    print("\nGetting current model config...")
    current_config = get_current_model_config()
    print(f"Current config: {current_config}")
    
    print("\nAll tests completed!")

except Exception as e:
    print(f"Error testing model_config: {e}")
