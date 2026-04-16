"""
Internshala portal agent — single TinyFish call per role (credit-efficient).
"""
import logging
from typing import Callable, List
from agent.tinyfish import TinyFishClient
from agent.claude_ai import ClaudeClient

logger = logging.getLogger("applypilot.internshala")


class InternshalaAgent:
    BASE_URL = "https://internshala.com/login/user"

    def __init__(self, tinyfish: TinyFishClient, claude: ClaudeClient):
        self.tf     = tinyfish
        self.claude = claude

    async def run(self, run_id, profile, email, password, max_apps, emit_log) -> List[dict]:
        results = []
        roles = [r.strip() for r in (profile.target_roles or "").split(",") if r.strip()]
        if not roles:
            await emit_log("warning", "No target roles set — skipping Internshala")
            return results

        resume_text = profile.resume_text or profile.summary or ""
        skills      = profile.skills or "software development"
        stipend     = profile.min_stipend or 0

        for role in roles[:2]:
            if len(results) >= max_apps:
                break

            await emit_log("info", f"Internshala: logging in and applying for '{role}'…")

            cover = await self._cover(role, profile)

            result = await self.tf.run(
                url=self.BASE_URL,
                goal=(
                    f"Complete these steps in order:\n"
                    f"1. Log into Internshala with email '{email}' and password '{password}'\n"
                    f"2. After login, search for '{role}' internships\n"
                    f"3. Filter: Work from Home preferred, stipend at least {stipend}\n"
                    f"4. Open the first matching internship listing\n"
                    f"5. Click Apply\n"
                    f"6. Fill the cover letter / 'why should you be hired' field with:\n"
                    f"   {cover[:500]}\n"
                    f"7. Submit the application\n"
                    f"8. Repeat steps 4-7 for 2 more internships (total 3 applications)\n"
                    f"9. Return a JSON array of jobs applied to:\n"
                    f"   [{{\"title\": \"...\", \"company\": \"...\", \"url\": \"...\"}}]"
                ),
                on_progress=lambda msg: emit_log("info", f"  ↳ {msg}"),
            )

            jobs = self._parse_jobs(result.output, role, self.BASE_URL)
            if not jobs and result.success:
                jobs = [{"title": role, "company": "Internshala", "url": self.BASE_URL}]

            for job in jobs:
                if len(results) >= max_apps:
                    break
                if result.success:
                    await emit_log("success", f"Applied: {job.get('title', role)} at {job.get('company', '?')}")
                    results.append({
                        "job_title": job.get("title", role),
                        "company":   job.get("company", "Unknown"),
                        "job_url":   job.get("url", self.BASE_URL),
                        "status":    "applied",
                        "cover_letter": cover,
                        "match_score":  80.0,
                        "tinyfish_run_id": result.run_id,
                    })
                else:
                    await emit_log("warning", f"Internshala failed for '{role}': {result.output[:120]}")
                    results.append({
                        "job_title": role, "company": "Unknown",
                        "job_url": self.BASE_URL, "status": "failed",
                        "cover_letter": cover, "match_score": 0.0,
                        "error": result.output,
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
                f"Dear Hiring Team,\n\nI am excited to apply for the {role} position. "
                f"With my skills in {profile.skills or 'software development'}, "
                f"I would be a strong fit.\n\nBest regards"
            )

    def _parse_jobs(self, text: str, role: str = "", url: str = "") -> list:
        from agent.portals._base import parse_jobs
        return parse_jobs(text, role, url)