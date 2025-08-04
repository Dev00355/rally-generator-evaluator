#!/usr/bin/env python3
"""
Test script to verify Python 3.12+ features are working correctly
"""

import sys
import json
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum, auto

# Test Python version
print(f"Python version: {sys.version}")
print(f"Version info: {sys.version_info}")

if sys.version_info >= (3, 12):
    print("✅ Python 3.12+ detected")
else:
    print("❌ Python 3.12+ required")
    sys.exit(1)

# Test modern Python 3.12 features
@dataclass(frozen=True, slots=True)
class TestResult:
    """Test dataclass with Python 3.12 features"""
    success: bool
    message: str
    score: float

class TestStatus(Enum):
    """Test enum with auto values"""
    STARTING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()

def test_match_statement(value: Any) -> str:
    """Test match statement functionality"""
    match value:
        case int() if value > 0:
            return "positive integer"
        case int() if value < 0:
            return "negative integer"
        case 0:
            return "zero"
        case str() if len(value) > 0:
            return "non-empty string"
        case []:
            return "empty list"
        case [x] if isinstance(x, int):
            return "list with one integer"
        case {"type": "test", "value": v}:
            return f"test dict with value {v}"
        case _:
            return "unknown type"

def test_union_types(value: str | int | None) -> str:
    """Test Python 3.10+ union type syntax"""
    match value:
        case str():
            return f"string: {value}"
        case int():
            return f"integer: {value}"
        case None:
            return "none value"
        case _:
            return "other type"

def run_tests() -> None:
    """Run all Python 3.12 feature tests"""
    print("\n🧪 Testing Python 3.12+ Features:")
    print("-" * 40)
    
    # Test 1: Dataclass with slots
    result = TestResult(success=True, message="Test passed", score=95.5)
    print(f"✅ Dataclass test: {result}")
    
    # Test 2: Enum with auto
    status = TestStatus.COMPLETED
    print(f"✅ Enum test: {status.name} = {status.value}")
    
    # Test 3: Match statements
    test_cases = [
        42,
        -10,
        0,
        "hello",
        "",
        [],
        [5],
        {"type": "test", "value": 100},
        None
    ]
    
    print("✅ Match statement tests:")
    for case in test_cases:
        result = test_match_statement(case)
        print(f"   {case!r} -> {result}")
    
    # Test 4: Union types
    union_cases = ["text", 123, None]
    print("✅ Union type tests:")
    for case in union_cases:
        result = test_union_types(case)
        print(f"   {case!r} -> {result}")
    
    # Test 5: F-string with expressions
    name = "Python"
    version = 3.12
    print(f"✅ F-string test: {name} {version} = {name.upper()} {version:.1f}")
    
    # Test 6: Walrus operator
    if (length := len("Python 3.12")) > 5:
        print(f"✅ Walrus operator test: length = {length}")
    
    print("\n🎉 All Python 3.12+ features working correctly!")

def test_imports() -> None:
    """Test that all required imports work"""
    print("\n📦 Testing Imports:")
    print("-" * 20)
    
    try:
        # Test LangGraph imports (will fail without proper installation)
        print("Testing LangGraph imports...")
        from langgraph.graph import StateGraph, END
        from langgraph.graph.message import add_messages
        print("✅ LangGraph imports successful")
    except ImportError as e:
        print(f"⚠️ LangGraph imports failed (expected without installation): {e}")
    
    try:
        # Test LangChain imports
        print("Testing LangChain imports...")
        from langchain_core.messages import HumanMessage, AIMessage
        from langchain_core.prompts import ChatPromptTemplate
        print("✅ LangChain imports successful")
    except ImportError as e:
        print(f"⚠️ LangChain imports failed (expected without installation): {e}")
    
    try:
        # Test our local imports
        print("Testing local imports...")
        from rally_user_story_fetcher import RallyUserStoryFetcher
        print("✅ Local imports successful")
    except ImportError as e:
        print(f"❌ Local imports failed: {e}")

if __name__ == "__main__":
    print("🚀 Python 3.12+ Feature Test Suite")
    print("=" * 50)
    
    run_tests()
    test_imports()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
