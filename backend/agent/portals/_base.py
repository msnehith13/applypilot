"""
Shared utilities for all portal agents.
"""
import json
import re
import logging

logger = logging.getLogger("applypilot.portals")


def parse_jobs(text: str, fallback_role: str, fallback_url: str) -> list:
    """
    Robustly extract a list of applied jobs from TinyFish output.
    Tries multiple patterns before falling back to a single generic entry.
    """
    if not text:
        return []

    # Pattern 1: proper JSON array (greedy — handles multiline)
    m = re.search(r'\[[\s\S]*?\]', text)
    if m:
        try:
            jobs = json.loads(m.group())
            if isinstance(jobs, list) and jobs:
                return jobs
        except Exception:
            pass

    # Pattern 2: extract individual objects and build list
    objects = re.findall(r'\{[^{}]+\}', text)
    if objects:
        result = []
        for obj in objects:
            try:
                result.append(json.loads(obj))
            except Exception:
                pass
        if result:
            return result

    # Pattern 3: look for "Applied to X at Y" patterns in plain text
    applied = re.findall(
        r'[Aa]pplied[^\n]*?([A-Z][^,\n]+?)\s+at\s+([A-Z][^,\n.]+)',
        text
    )
    if applied:
        return [{"title": t.strip(), "company": c.strip(), "url": fallback_url}
                for t, c in applied[:5]]

    # Pattern 4: if TinyFish says it succeeded but returned no structure,
    # treat it as one successful application with the role name
    success_signals = ["successfully", "submitted", "applied", "confirmed", "complete"]
    if any(s in text.lower() for s in success_signals):
        logger.info(f"No structured output but success signals found — counting as 1 application")
        return [{"title": fallback_role, "company": "via portal", "url": fallback_url}]

    return []