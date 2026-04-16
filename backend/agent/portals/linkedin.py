"""LinkedIn portal agent — single TinyFish call, Easy Apply only."""
import json
import re
import logging
from typing import Callable, List
from agent.tinyfish import TinyFishClient
from agent.claude_ai import ClaudeClient

logger = logging.getLogger("applypilot.linkedin")


class LinkedInAgent:
    BASE_URL = "https://www.linkedin.com/login"

    def __init__(self, tinyfish: TinyFishClient, claude: ClaudeClient):
        self.tf = tinyfish
        self.claude = claude

    async def run(self, run_id, profile, email, password, max_apps, emit_log) -> List[dict]:
        results = []
        roles = [r.strip() for r in (profile.target_roles or "").split(",") if r.strip()]
        if not roles:
            await emit_log("warning", "No target roles set - skipping LinkedIn")
            return results

        for role in roles[:2]:
            if len(results) >= max_apps:
                break

            await emit_log("info", f"LinkedIn: logging in and applying for '{role}'...")
            cover = await self._cover(role, profile)
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={role.replace(' ', '%20')}&f_AL=true"
            phone = profile.phone or "9999999999"

            result = await self.tf.run(
                url=self.BASE_URL,
                goal=(
                    "Complete these steps carefully:\n"
                    f"1. Type '{email}' in the email field\n"
                    f"2. Type '{password}' in the password field\n"
                    "3. Click Sign In and wait for the LinkedIn home feed to load fully\n"
                    "4. If a 2FA, phone verification or number-matching screen appears,\n"
                    "   return this JSON and stop: [{\"error\":\"2FA\",\"confirmed\":false}]\n"
                    f"5. Navigate to: {search_url}\n"
                    "6. Wait for job listings to load\n"
                    "7. Click the first job in the list\n"
                    "8. Find and click the Easy Apply button on the job detail panel\n"
                    "9. A modal will open - complete EVERY page:\n"
                    f"   - Phone number field: {phone}\n"
                    "   - Years of experience: 0\n"
                    f"   - Cover letter or message field: {cover[:250]}\n"
                    "   - Yes/No skill questions: select Yes\n"
                    "   - Click Next or Continue on each page\n"
                    "10. On the final page click Submit application\n"
                    "11. Wait for the Application submitted confirmation message\n"
                    "12. Record the job title and company from the confirmation screen\n"
                    "13. Close the modal\n"
                    "14. Repeat steps 7-13 for one more Easy Apply job\n"
                    "15. Return ONLY confirmed applications as JSON:\n"
                    "[{\"title\":\"exact title\",\"company\":\"exact company\",\"url\":\"url\",\"confirmed\":true}]\n"
                    "If nothing was confirmed, return: []"
                ),
                on_progress=lambda msg: emit_log("info", f"  -> {msg}"),
                stealth=True,
            )

            jobs = self._parse_jobs(result.output, role, search_url)
            # Filter out error entries and unconfirmed
            jobs = [j for j in jobs if not j.get("error") and j.get("confirmed", True)]

            if not jobs:
                await emit_log("warning", f"LinkedIn: no confirmed submissions for '{role}'")
                raw = (result.output or "")[:400]
                await emit_log("info", f"  Agent output: {raw}")
                await emit_log("info", f"  TinyFish status: {result.status}, run_id: {result.run_id}, result dict: {str(result.result)[:300]}")
                # Still record as failed so we can debug
                results.append({
                    "job_title": role, "company": "Unknown",
                    "job_url": search_url, "status": "failed",
                    "cover_letter": cover, "match_score": 0.0,
                    "error": result.output[:200] if result.output else "No confirmation received",
                })
                continue

            for job in jobs:
                if len(results) >= max_apps:
                    break
                await emit_log("success", f"Confirmed: {job.get('title', role)} at {job.get('company', '?')}")
                results.append({
                    "job_title": job.get("title", role),
                    "company": job.get("company", "Unknown"),
                    "job_url": job.get("url", search_url),
                    "status": "applied",
                    "cover_letter": cover,
                    "match_score": 78.0,
                    "tinyfish_run_id": result.run_id,
                })
        return results

    async def _cover(self, role: str, profile) -> str:
        try:
            return await self.claude.generate_cover_letter(
                jd_text=role,
                resume_text=profile.resume_text or profile.summary or "",
                company="the company", role=role,
            )
        except Exception:
            return (
                f"Dear Hiring Team, I am excited to apply for the {role} position. "
                f"With my background in {profile.skills or 'software development'}, "
                f"I am confident I can contribute meaningfully. Best regards"
            )

    def _parse_jobs(self, text: str, role: str = "", url: str = "") -> list:
        if not text:
            return []
        bracket = text.find("[")
        if bracket != -1:
            end = text.rfind("]")
            if end != -1:
                try:
                    jobs = json.loads(text[bracket:end + 1])
                    if isinstance(jobs, list):
                        return jobs
                except Exception:
                    pass
        found = re.findall(r"\{[^{}]+\}", text)
        if found:
            result = []
            for obj in found:
                try:
                    result.append(json.loads(obj))
                except Exception:
                    pass
            if result:
                return result
        if any(s in text.lower() for s in ["application submitted", "successfully applied"]):
            return [{"title": role, "company": "via LinkedIn", "url": url, "confirmed": True}]
        return []