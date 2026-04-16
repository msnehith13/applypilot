"""Naukri portal agent — single TinyFish call, direct email/password login."""
import json
import re
import logging
from typing import Callable, List
from agent.tinyfish import TinyFishClient
from agent.claude_ai import ClaudeClient

logger = logging.getLogger("applypilot.naukri")


class NaukriAgent:
    LOGIN_URL = "https://www.naukri.com/nlogin/login"

    def __init__(self, tinyfish: TinyFishClient, claude: ClaudeClient):
        self.tf = tinyfish
        self.claude = claude

    async def run(self, run_id, profile, email, password, max_apps, emit_log) -> List[dict]:
        results = []
        roles = [r.strip() for r in (profile.target_roles or "").split(",") if r.strip()]
        if not roles:
            await emit_log("warning", "No target roles set - skipping Naukri")
            return results

        for role in roles[:2]:
            if len(results) >= max_apps:
                break

            await emit_log("info", f"Naukri: logging in and applying for '{role}'...")
            cover = await self._cover(role, profile)
            search_url = f"https://www.naukri.com/{role.lower().replace(' ', '-')}-jobs"

            result = await self.tf.run(
                url=self.LOGIN_URL,
                goal=(
                    "Complete these steps carefully:\n"
                    "1. You are on the Naukri login page\n"
                    "2. DO NOT click 'Continue with Google' or any Google/social login button\n"
                    "3. Find the email/username input field and type: "
                    f"'{email}'\n"
                    "4. Find the password input field and type: "
                    f"'{password}'\n"
                    "5. Click the Login button (not the Google button)\n"
                    "6. If an OTP or verification is asked, stop and return: "
                    "[{\"error\":\"OTP required\",\"confirmed\":false}]\n"
                    "7. Wait for the Naukri dashboard/home to load\n"
                    f"8. In the search bar at the top, search for '{role}'\n"
                    "9. On the search results page, click the first job listing\n"
                    "10. On the job detail page, click the Apply button\n"
                    "11. If a Quick Apply or Easy Apply form appears, fill it:\n"
                    "    - Notice period: Immediate\n"
                    "    - Current salary/CTC: 0\n"
                    f"    - Expected salary/CTC: {profile.min_stipend or 15000}\n"
                    f"    - Cover letter or message: {cover[:250]}\n"
                    "12. Click Submit or Apply Now to submit the application\n"
                    "13. Wait for a confirmation like 'Application submitted' or "
                    "'Applied successfully'\n"
                    "14. Record the exact job title and company name\n"
                    "15. Go back to search results and repeat steps 9-14 for one more job\n"
                    "16. Return ONLY confirmed applications:\n"
                    "[{\"title\":\"job title\",\"company\":\"company\","
                    "\"url\":\"url\",\"confirmed\":true}]\n"
                    "If nothing was confirmed, return: []"
                ),
                on_progress=lambda msg: emit_log("info", f"  -> {msg}"),
                stealth=True,
            )

            jobs = self._parse_jobs(result.output, role, search_url)
            jobs = [j for j in jobs if not j.get("error") and j.get("confirmed", True)]

            if not jobs:
                await emit_log("warning", f"Naukri: no confirmed submissions for '{role}'")
                raw = (result.output or "")[:400]
                await emit_log("info", f"  Agent output: {raw}")
                await emit_log("info", f"  TinyFish status: {result.status}, run_id: {result.run_id}, result dict: {str(result.result)[:300]}")
                await emit_log("info", f"  TinyFish output: {(result.output or chr(40)+chr(41))[:300]}")
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
                    "match_score": 74.0,
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
                f"With my skills in {profile.skills or 'software development'}, "
                f"I believe I would be a strong fit. Best regards"
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
        if any(s in text.lower() for s in ["application submitted", "applied successfully", "successfully applied"]):
            return [{"title": role, "company": "via Naukri", "url": url, "confirmed": True}]
        return []