#!/usr/bin/env python3
"""
Test script to figure out which environment variable LiveKit uses for server URL
"""

import asyncio
import os

from livekit import agents


async def test_connection(env_vars):
    """Test connection with given environment variables"""
    print(f"\n🔍 Testing with environment variables: {env_vars}")

    # Clear all LiveKit env vars first
    lk_vars = [k for k in os.environ.keys() if k.startswith("LIVEKIT")]
    for var in lk_vars:
        if var in os.environ:
            del os.environ[var]

    # Set test variables
    os.environ.update(env_vars)

    # Always set these
    os.environ["LIVEKIT_API_KEY"] = "APIzCnE2dZJx2EL"
    os.environ["LIVEKIT_API_SECRET"] = "gljyQPehxHDcu6raQVtxRWQSmJMsoWWZyDEuQDHV53b"

    try:
        worker_options = agents.WorkerOptions(
            entrypoint_fnc=lambda ctx: None,
        )
        worker = agents.Worker(worker_options)

        # Try to start connection (this will show us the URL it's trying to connect to)
        print("   📡 Attempting connection...")
        await asyncio.wait_for(worker.run(), timeout=3.0)

    except asyncio.TimeoutError:
        print("   ⏰ Connection attempt timed out (this is expected)")
    except Exception as e:
        error_str = str(e)
        if "localhost:7880" in error_str:
            print("   ❌ Still trying localhost:7880 - env var not working")
        elif "spaced-3zrvc2b8.livekit.cloud" in error_str:
            print("   ✅ Connecting to correct cloud server!")
        else:
            print(f"   ❓ Other error: {error_str[:100]}...")


async def main():
    """Test different environment variable combinations"""

    server_url = "wss://spaced-3zrvc2b8.livekit.cloud"

    test_cases = [
        {"LIVEKIT_URL": server_url},
        {"LIVEKIT_SERVER_URL": server_url},
        {"LIVEKIT_HOST": server_url},
        {"LIVEKIT_WS_URL": server_url},
        {"LIVEKIT_SERVER": server_url},
        {"LIVEKIT_ENDPOINT": server_url},
        # Try without wss:// prefix
        {"LIVEKIT_URL": "spaced-3zrvc2b8.livekit.cloud"},
        {"LIVEKIT_HOST": "spaced-3zrvc2b8.livekit.cloud"},
        # Try with different formats
        {"LIVEKIT_URL": "wss://spaced-3zrvc2b8.livekit.cloud:443"},
    ]

    print("🧪 Testing LiveKit environment variable names...")

    for env_vars in test_cases:
        await test_connection(env_vars)

    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
