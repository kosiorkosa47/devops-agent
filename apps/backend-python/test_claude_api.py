#!/usr/bin/env python3
"""
Test real Claude API connection and features
"""
import asyncio
from app.core.claude_agent import claude_agent
from app.core.tools import ToolDefinitions

print("=" * 70)
print("🔥 REAL CLAUDE API TESTS")
print("=" * 70)

async def test_claude_api():
    print("\n1. Testing Claude API connection...")
    
    try:
        # Simple test message
        result = await claude_agent.chat_with_tools(
            user_message="Hello! Can you confirm you can see your available tools?",
            conversation_history=[],
            user_id="test-user",
            conversation_id="test-conv-1",
            auto_approve_safe=True,
            approval_mode="normal"
        )
        
        print("✅ Claude API connected successfully!")
        print(f"\nClaude's response:")
        print("-" * 70)
        print(result.get("response", "No response"))
        print("-" * 70)
        
        if result.get("tool_uses"):
            print(f"\n✅ Claude used {len(result['tool_uses'])} tools")
        
        print(f"\n📊 Token usage:")
        if result.get("usage"):
            print(f"  Input: {result['usage']['input_tokens']} tokens")
            print(f"  Output: {result['usage']['output_tokens']} tokens")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n2. Testing explicit reasoning...")
    try:
        result = await claude_agent.chat_with_tools(
            user_message="I need you to demonstrate your thinking process. What tools do you have available and how would you use them?",
            conversation_history=[],
            user_id="test-user",
            conversation_id="test-conv-2",
            auto_approve_safe=True,
            approval_mode="normal"
        )
        
        response = result.get("response", "")
        
        # Check for reasoning tags
        has_think = "<think>" in response
        has_plan = "<plan>" in response
        
        print(f"✅ Response received ({len(response)} chars)")
        print(f"  Has <think> tags: {has_think}")
        print(f"  Has <plan> tags: {has_plan}")
        
        if has_think or has_plan:
            print("\n🎉 Claude is using explicit reasoning!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n3. Testing tool awareness...")
    tools = ToolDefinitions.get_all_tools()
    tool_categories = {
        "Kubernetes": [t for t in tools if "kubectl" in t['name'] or "analyze" in t['name'] or "auto_" in t['name']],
        "Predictive": [t for t in tools if "predict" in t['name'] or "suggest" in t['name'] or "identify" in t['name']],
        "Security": [t for t in tools if "scan" in t['name'] or "fix" in t['name']],
    }
    
    print(f"\nAvailable tools by category:")
    for category, tools_list in tool_categories.items():
        print(f"  {category}: {len(tools_list)} tools")
        for tool in tools_list[:3]:  # Show first 3
            print(f"    - {tool['name']}")
    
    print(f"\n✅ Total: {len(tools)} tools configured")

print("\n" + "=" * 70)
print("Running async tests...")
print("=" * 70)

asyncio.run(test_claude_api())

print("\n" + "=" * 70)
print("✅ ALL CLAUDE API TESTS COMPLETE!")
print("=" * 70)
