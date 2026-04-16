"""
LLM client using Groq API.
Handles cover letter generation, JD parsing, match scoring, and resume extraction.
"""
import json
import re
import logging
from groq import Groq
from config import get_settings

settings = get_settings()
logger = logging.getLogger("applypilot.llm")

MODEL = "llama-3.3-70b-versatile"
MIN_MATCH_SCORE = 60.0   # skip jobs below this threshold


class ClaudeClient:
    """Groq-backed LLM client. Named ClaudeClient for import consistency."""

    def __init__(self):
        self.client = Groq(api_key=settings.anthropic_api_key)

    def _chat(self, prompt: str, max_tokens: int = 500) -> str:
        resp = self.client.chat.completions.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

    # ── Cover Letter ───────────────────────────────────────────────────────────

    async def generate_cover_letter(
        self,
        jd_text: str,
        resume_text: str,
        company: str,
        role: str,
    ) -> str:
        prompt = f"""Write a concise, tailored cover letter for this internship application.

Role: {role}
Company: {company}
Job description: {jd_text[:800]}

Candidate profile:
{resume_text[:1200] if resume_text else "Final-year CS student skilled in full-stack development, Python, React, and ML."}

Rules:
- Maximum 3 short paragraphs, 150 words total
- Mention 2 specific skills that match the JD
- Professional but enthusiastic tone
- Do NOT include any placeholder like [Your Name] or [Date]
- End with exactly: "Best regards"
- No name or signature after "Best regards"
"""
        try:
            return self._chat(prompt, max_tokens=400)
        except Exception as e:
            logger.error(f"Cover letter generation failed: {e}")
            return self._fallback_cover(role, company)

    def _fallback_cover(self, role: str, company: str) -> str:
        skills = getattr(self, "_profile_skills", "software development")
        return (
            f"Dear Hiring Team at {company},\n\n"
            f"I am excited to apply for the {role} position. "
            f"My background in {skills} makes me a strong fit for this role. "
            f"I am eager to contribute to your team and grow professionally.\n\n"
            f"Best regards"
        )

    # ── JD Parsing ─────────────────────────────────────────────────────────────

    async def parse_jd(self, jd_text: str) -> dict:
        prompt = f"""Extract structured info from this job description.
Return ONLY a JSON object, no explanation, no markdown.

JD: {jd_text[:1500]}

JSON format:
{{
  "required_skills": ["skill1", "skill2"],
  "nice_to_have": ["skill1"],
  "experience_required": "fresher",
  "role_type": "internship",
  "stipend": "15000",
  "duration": "3 months",
  "summary": "one sentence summary of the role"
}}"""
        try:
            text  = self._chat(prompt, max_tokens=350)
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.error(f"JD parse failed: {e}")
        return {
            "required_skills": [],
            "nice_to_have": [],
            "experience_required": "fresher",
            "role_type": "internship",
            "stipend": "",
            "duration": "",
            "summary": "",
        }

    # ── Match Scoring ──────────────────────────────────────────────────────────

    async def score_match(self, jd_text: str, resume_text: str) -> float:
        """
        Score 0-100 how well the candidate matches the job.
        Uses skill overlap + experience fit + role relevance.
        """
        if not resume_text or not jd_text:
            return 70.0

        prompt = f"""Rate how well this candidate matches this job description.
Consider: skill overlap, experience level fit, role relevance.
Return ONLY a single integer between 0 and 100. Nothing else.

Job description:
{jd_text[:700]}

Candidate profile:
{resume_text[:700]}

Score (0-100):"""
        try:
            text  = self._chat(prompt, max_tokens=5)
            match = re.search(r'\d+', text)
            if match:
                score = float(match.group())
                return max(0.0, min(100.0, score))
        except Exception as e:
            logger.error(f"Match scoring failed: {e}")
        return 70.0

    async def should_apply(self, jd_text: str, resume_text: str) -> tuple[bool, float]:
        """
        Returns (should_apply: bool, score: float).
        Skips jobs below MIN_MATCH_SCORE threshold.
        """
        score = await self.score_match(jd_text, resume_text)
        return score >= MIN_MATCH_SCORE, score

    # ── Resume Text Extraction ─────────────────────────────────────────────────

    @staticmethod
    def extract_resume_text(filepath: str) -> str:
        """
        Extract plain text from a PDF resume.
        Falls back gracefully if PyMuPDF isn't installed.
        """
        try:
            import fitz  # PyMuPDF
            doc  = fitz.open(filepath)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            logger.info(f"Extracted {len(text)} chars from resume")
            return text.strip()
        except ImportError:
            logger.warning("PyMuPDF not installed — install with: pip install pymupdf")
        except Exception as e:
            logger.error(f"Resume extraction failed: {e}")
        return ""

    # ── Resume Tailoring ───────────────────────────────────────────────────────

    async def tailor_resume_summary(
        self,
        jd_text: str,
        resume_text: str,
        role: str,
        company: str,
    ) -> str:
        """
        Generate a tailored professional summary for the resume
        that highlights the most relevant skills for this specific JD.
        """
        prompt = f"""Write a 2-sentence professional summary tailored for this specific job.
Highlight only skills that are relevant to the job description.
Keep it factual — only mention skills the candidate actually has.

Role: {role} at {company}
Job description: {jd_text[:600]}
Candidate profile: {resume_text[:800]}

Return ONLY the 2-sentence summary, nothing else:"""
        try:
            return self._chat(prompt, max_tokens=150)
        except Exception as e:
            logger.error(f"Resume tailoring failed: {e}")
            return ""