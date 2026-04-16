"""
TinyFish Web Agent API wrapper.
Uses the SSE streaming endpoint: POST /v1/automation/run-sse
"""
import json
import asyncio
import logging
import os
from typing import Callable, Optional
import httpx
from config import get_settings

settings = get_settings()
logger = logging.getLogger("applypilot.tinyfish")

TINYFISH_BASE = "https://agent.tinyfish.ai/v1"
TIMEOUT       = 300


class TinyFishResult:
    def __init__(self, run_id: str, status: str, result: dict):
        self.run_id  = run_id
        self.status  = status
        self.result  = result
        self.success = status == "COMPLETED"
        self.output  = result.get("output", "") or result.get("message", "")


class TinyFishClient:

    def __init__(self):
        pass  # key is read fresh on every call

    @property
    def api_key(self) -> str:
        """Always read fresh from settings so key rotations take effect immediately."""
        return get_settings().tinyfish_api_key

    @property
    def headers(self) -> dict:
        return {
            "X-API-Key":    self.api_key,
            "Content-Type": "application/json",
            "Accept":       "text/event-stream",
        }

    def _proxy(self) -> Optional[str]:
        for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
            v = os.environ.get(key, "")
            if v:
                return v
        return None

    async def run(
        self,
        url: str,
        goal: str,
        on_progress: Optional[Callable] = None,
        stealth: bool = False,
    ) -> TinyFishResult:

        payload = {
            "url":             url,
            "goal":            goal,
            "browser_profile": "stealth" if stealth else "lite",
        }

        run_id = None
        result = {}
        status = "FAILED"

        proxy = self._proxy()
        transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(TIMEOUT, connect=30),
                transport=transport,
                follow_redirects=True,
            ) as client:

                # Use a plain POST and read lines manually to avoid
                # the "must call read() first" streaming bug
                async with client.stream(
                    "POST",
                    f"{TINYFISH_BASE}/automation/run-sse",
                    headers=self.headers,
                    json=payload,
                ) as response:

                    if response.status_code != 200:
                        # Read error body safely
                        await response.aread()
                        err = response.text[:300]
                        logger.error(f"TinyFish HTTP {response.status_code}: {err}")
                        return TinyFishResult("", "FAILED", {"message": f"HTTP {response.status_code}: {err}"})

                    async for raw_line in response.aiter_lines():
                        line = raw_line.strip()
                        if not line or not line.startswith("data:"):
                            continue

                        raw = line[5:].strip()
                        if not raw:
                            continue

                        try:
                            event = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        etype  = event.get("type", "")
                        run_id = event.get("run_id", run_id)

                        if etype == "STARTED":
                            logger.info(f"TinyFish started: {run_id}")

                        elif etype == "PROGRESS":
                            purpose = event.get("purpose", "")
                            if purpose:
                                logger.debug(f"TinyFish [{run_id}]: {purpose}")
                                if on_progress:
                                    if asyncio.iscoroutinefunction(on_progress):
                                        await on_progress(purpose)
                                    else:
                                        on_progress(purpose)

                        elif etype == "COMPLETE":
                            status = event.get("status", "FAILED")
                            result = event.get("result", {})
                            logger.info(f"TinyFish complete [{run_id}]: {status}")
                            break

                        elif etype == "HEARTBEAT":
                            pass

        except httpx.ConnectError as e:
            msg = (
                f"Cannot reach TinyFish: {e}. "
                "Check firewall/antivirus — allow python.exe outbound HTTPS. "
                "Or set HTTPS_PROXY in .env if behind a proxy."
            )
            logger.error(msg)
            result = {"message": msg}

        except httpx.TimeoutException:
            logger.error(f"TinyFish timeout after {TIMEOUT}s")
            result = {"message": "Task timed out"}

        except Exception as e:
            logger.error(f"TinyFish unexpected error: {type(e).__name__}: {e}")
            result = {"message": f"{type(e).__name__}: {e}"}

        return TinyFishResult(run_id=run_id or "", status=status, result=result)

    async def test_connection(self) -> tuple[bool, str]:
        """Returns (ok, message). Call /api/test-tinyfish to use this."""
        try:
            proxy = self._proxy()
            transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None
            async with httpx.AsyncClient(timeout=10, transport=transport) as client:
                r = await client.get(
                    "https://agent.tinyfish.ai",
                    headers={"X-API-Key": self.api_key},
                )
                return True, f"Reachable — HTTP {r.status_code}"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"