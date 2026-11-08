#!/usr/bin/env python3
"""
Script kiểm tra sức khỏe các dịch vụ.
Dùng trong Docker healthcheck và runbook.
"""

from __future__ import annotations

import asyncio
import sys

import httpx


async def check_api() -> bool:
    """Kiểm tra API health endpoint."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            return response.status_code == 200
    except Exception as e:
        print(f"API check failed: {e}", file=sys.stderr)
        return False


async def main() -> None:
    api_ok = await check_api()

    if not api_ok:
        print("HEALTH CHECK FAILED", file=sys.stderr)
        sys.exit(1)

    print("HEALTH CHECK OK")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
