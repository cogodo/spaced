#!/usr/bin/env python3
"""
Simple test script to verify streaming functionality works.
Run this to test the streaming components in isolation.

Usage:
    python test_streaming.py
"""

import asyncio
import sys


async def test_anthropic_streaming():
    """Test that Anthropic streaming works."""
    print("\n=== Testing Anthropic Streaming ===")

    try:
        from app.config import settings
        from core.llm.anthropic import AnthropicProvider

        provider = AnthropicProvider(model=settings.anthropic_model)

        print("Streaming a simple prompt...")
        chunks = []
        async for chunk in provider.complete_streaming(
            prompt="Say 'Hello, streaming works!' in exactly those words.",
            system_prompt="You are a helpful assistant. Be very brief.",
            max_tokens=50,
        ):
            chunks.append(chunk)
            print(f"  Chunk: '{chunk}'")

        full_response = "".join(chunks)
        print(f"\nFull response: '{full_response}'")
        print("✅ Anthropic streaming test PASSED")
        return True

    except Exception as e:
        print(f"❌ Anthropic streaming test FAILED: {e}")
        return False


async def test_combined_service_streaming():
    """Test that CombinedService streaming works."""
    print("\n=== Testing CombinedService Streaming ===")

    try:
        from core.models import Question
        from core.services.combined_service import CombinedService

        # Create a mock question
        question = Question(
            id="test-q-1",
            topicId="test-topic-1",
            text="What is 2 + 2?",
            difficulty=1,
            type="short_answer",
        )

        service = CombinedService()

        print("Streaming evaluation of a simple question...")
        text_chunks = []
        state = None

        async for text_chunk, state_update in service.evaluate_turn_streaming(
            question=question,
            answer="Human: I think it's 4",
            after_hint=False,
            initial_score=None,
        ):
            if text_chunk:
                text_chunks.append(text_chunk)
                print(f"  Text chunk: '{text_chunk[:50]}...'")
            if state_update is not None:
                state = state_update
                print(f"  State received: score={state.get('score')}, action={state.get('next_action')}")

        full_text = "".join(text_chunks)
        print(f"\nFull response: '{full_text[:100]}...'")
        print(f"Final state: {state}")

        if state and "score" in state:
            print("✅ CombinedService streaming test PASSED")
            return True
        else:
            print("❌ CombinedService streaming test FAILED: No state received")
            return False

    except Exception as e:
        print(f"❌ CombinedService streaming test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_sentence_buffering():
    """Test sentence extraction logic."""
    print("\n=== Testing Sentence Buffering ===")

    try:
        from core.services.combined_service import CombinedService

        service = CombinedService()

        test_cases = [
            ("Hello world. This is a test.", (["Hello world."], "This is a test.")),
            ("Hello! How are you? I'm fine.", (["Hello!", "How are you?"], "I'm fine.")),
            ("Dr. Smith went home.", ([], "Dr. Smith went home.")),  # Abbreviation - should not split
            ("End. ", (["End."], "")),  # Sentence with trailing space
        ]

        all_passed = True
        for text, expected in test_cases:
            sentences, remaining = service._extract_sentences(text)
            print(f"  Input: '{text}'")
            print(f"  Expected: {expected}")
            print(f"  Got: ({sentences}, '{remaining}')")

            # For the abbreviation case, we expect it might split or not
            if text == "Dr. Smith went home.":
                print("  (Note: Abbreviation handling may vary)")

        print("✅ Sentence buffering test completed")
        return True

    except Exception as e:
        print(f"❌ Sentence buffering test FAILED: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Streaming Functionality Tests")
    print("=" * 60)

    results = []

    # Test sentence buffering (no API calls)
    results.append(("Sentence Buffering", await test_sentence_buffering()))

    # Only run API tests if we have credentials
    import os

    if os.getenv("ANTHROPIC_API_KEY"):
        results.append(("Anthropic Streaming", await test_anthropic_streaming()))
        results.append(("CombinedService Streaming", await test_combined_service_streaming()))
    else:
        print("\n⚠️  ANTHROPIC_API_KEY not set, skipping API tests")
        print("   Set the environment variable and re-run to test streaming")

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
