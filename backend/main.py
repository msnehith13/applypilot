import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import get_settings
from models import (
    init_db, get_db,
    UserProfile, AgentRun, Application, AgentLog,
    Portal, AppStatus, RunStatus
)

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("applypilot")


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("ApplyPilot backend started")
    yield
    logger.info("ApplyPilot backend stopped")


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="ApplyPilot API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/app")
async def serve_frontend():
    from fastapi.responses import FileResponse
    import os
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "applypilot.html")
    return FileResponse(html_path)

# ── WebSocket Manager ──────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


manager = ConnectionManager()


async def emit_log(run_id: str, level: str, message: str, db: Session):
    """Write a log entry to DB and broadcast to all WS clients."""
    log = AgentLog(run_id=run_id, level=level, message=message)
    db.add(log)
    db.commit()
    await manager.broadcast({
        "type": "log",
        "run_id": run_id,
        "level": level,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    })


# ── Pydantic Schemas ───────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    target_roles: Optional[str] = None
    target_locations: Optional[str] = None
    experience_level: Optional[str] = None
    skills: Optional[str] = None
    min_stipend: Optional[int] = None
    summary: Optional[str] = None


class RunRequest(BaseModel):
    portals: List[str]
    max_applications: Optional[int] = None


class ProfileOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    target_roles: str
    target_locations: str
    experience_level: str
    skills: str
    min_stipend: int
    summary: str
    resume_filename: str

    class Config:
        from_attributes = True


class ApplicationOut(BaseModel):
    id: str
    portal: str
    job_title: str
    company: str
    job_url: str
    match_score: float
    status: str
    applied_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class RunOut(BaseModel):
    id: str
    status: str
    portals: str
    started_at: datetime
    completed_at: Optional[datetime]
    total_found: int
    total_applied: int
    total_failed: int

    class Config:
        from_attributes = True


class LogOut(BaseModel):
    id: str
    level: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    total_applied: int
    total_today: int
    interview_calls: int
    hours_saved: float
    by_portal: dict
    by_status: dict


# ── Routes: Health ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "app": "ApplyPilot", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/test-tinyfish")
async def test_tinyfish():
    """Test TinyFish API connectivity. Visit /api/test-tinyfish in browser."""
    from agent.tinyfish import TinyFishClient
    tf = TinyFishClient()
    ok, msg = await tf.test_connection()
    return {"reachable": ok, "message": msg, "api_key_set": bool(tf.api_key)}


# ── Routes: Profile ────────────────────────────────────────────────────────────

@app.get("/api/profile", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.put("/api/profile", response_model=ProfileOut)
def update_profile(data: ProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        profile = UserProfile()
        db.add(profile)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@app.post("/api/profile/resume")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a resume PDF. Stores filename; text extraction happens in Phase 4."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()
    # Save to disk
    import os, aiofiles
    os.makedirs("uploads", exist_ok=True)
    path = f"uploads/{file.filename}"
    async with aiofiles.open(path, "wb") as f:
        await f.write(contents)

    profile = db.query(UserProfile).first()
    profile.resume_filename = file.filename

    # Extract text from PDF for LLM use (Phase 4)
    from agent.claude_ai import ClaudeClient
    resume_text = ClaudeClient.extract_resume_text(path)
    if resume_text:
        profile.resume_text = resume_text
        logger.info(f"Resume text extracted: {len(resume_text)} chars")

    db.commit()
    return {"filename": file.filename, "size": len(contents), "text_extracted": bool(resume_text)}


# ── Routes: Agent Runs ─────────────────────────────────────────────────────────

@app.post("/api/runs", response_model=RunOut)
async def start_run(body: RunRequest, db: Session = Depends(get_db)):
    """Create a new agent run and kick it off in the background."""
    # Validate portals
    valid = {p.value for p in Portal}
    for p in body.portals:
        if p not in valid:
            raise HTTPException(status_code=400, detail=f"Unknown portal: {p}")

    profile = db.query(UserProfile).first()
    if not profile or not profile.target_roles:
        raise HTTPException(
            status_code=400,
            detail="Set at least target_roles in your profile before running"
        )

    run = AgentRun(portals=",".join(body.portals))
    db.add(run)
    db.commit()
    db.refresh(run)

    # Phase 2: use real TinyFish orchestrator
    asyncio.create_task(
        _run_agent_real(run.id, body.portals, body.max_applications or settings.max_applications_per_run)
    )

    return run


@app.get("/api/runs", response_model=List[RunOut])
def list_runs(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(AgentRun).order_by(AgentRun.started_at.desc()).limit(limit).all()


@app.get("/api/runs/{run_id}", response_model=RunOut)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.post("/api/runs/{run_id}/stop")
async def stop_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run.status = RunStatus.stopped
    run.completed_at = datetime.utcnow()
    db.commit()
    await manager.broadcast({"type": "run_stopped", "run_id": run_id})
    return {"status": "stopped"}


@app.get("/api/runs/{run_id}/logs", response_model=List[LogOut])
def get_run_logs(run_id: str, db: Session = Depends(get_db)):
    return db.query(AgentLog).filter(AgentLog.run_id == run_id).order_by(AgentLog.created_at).all()


# ── Routes: Applications ───────────────────────────────────────────────────────

@app.get("/api/applications", response_model=List[ApplicationOut])
def list_applications(
    portal: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(Application)
    if portal:
        q = q.filter(Application.portal == portal)
    if status:
        q = q.filter(Application.status == status)
    return q.order_by(Application.created_at.desc()).limit(limit).all()


@app.get("/api/applications/{app_id}", response_model=ApplicationOut)
def get_application(app_id: str, db: Session = Depends(get_db)):
    app_obj = db.query(Application).filter(Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_obj


# ── Routes: Stats ──────────────────────────────────────────────────────────────

@app.get("/api/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func as sqlfunc

    all_apps = db.query(Application).all()
    today = datetime.utcnow().date()

    total_applied = sum(1 for a in all_apps if a.status == AppStatus.applied)
    total_today = sum(
        1 for a in all_apps
        if a.status == AppStatus.applied and a.applied_at and a.applied_at.date() == today
    )

    by_portal: dict = {}
    for portal in Portal:
        by_portal[portal.value] = sum(
            1 for a in all_apps
            if a.portal == portal and a.status == AppStatus.applied
        )

    by_status: dict = {}
    for s in AppStatus:
        by_status[s.value] = sum(1 for a in all_apps if a.status == s)

    # Estimate: avg 30 min saved per application
    hours_saved = round(total_applied * 0.5, 1)

    # Placeholder: in Phase 4, this will query a responses table
    interview_calls = 0

    return StatsOut(
        total_applied=total_applied,
        total_today=total_today,
        interview_calls=interview_calls,
        hours_saved=hours_saved,
        by_portal=by_portal,
        by_status=by_status,
    )


# ── WebSocket ──────────────────────────────────────────────────────────────────

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; all messages are server-pushed
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── Agent Background Task (demo stub — Phase 2 replaces this) ─────────────────

DEMO_JOBS = [
    ("SDE Intern – Backend",        "Razorpay",      "internshala", "https://internshala.com", 87.0),
    ("Full Stack Developer Intern",  "Zepto",         "linkedin",    "https://linkedin.com",    79.0),
    ("ML Engineer Intern",           "Sarvam AI",     "internshala", "https://internshala.com", 72.0),
    ("React Developer Intern",       "CoinDCX",       "naukri",      "https://naukri.com",      68.0),
    ("Backend Engineer Intern",      "CRED",          "linkedin",    "https://linkedin.com",    91.0),
    ("Data Science Intern",          "PhonePe",       "internshala", "https://internshala.com", 65.0),
    ("Software Engineer Intern",     "Swiggy",        "naukri",      "https://naukri.com",      83.0),
    ("Frontend Developer Intern",    "Meesho",        "linkedin",    "https://linkedin.com",    76.0),
]

async def _run_agent(run_id: str, portals: List[str], max_applications: int):
    """
    Demo orchestrator — emits realistic step-by-step logs and seeds
    fake applications so the dashboard feels alive.
    Phase 2 will replace this entire body with real TinyFish calls.
    """
    from models import SessionLocal
    db = SessionLocal()

    # Small initial delay so the frontend WS is connected before first log
    await asyncio.sleep(1.5)

    try:
        run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if not run:
            return

        # ── Step 0: Login ──────────────────────────────────────────────────
        for portal in portals:
            await emit_log(run_id, "info", f"Opening browser session for {portal}…", db)
            await asyncio.sleep(0.8)
            await emit_log(run_id, "success", f"Logged into {portal} successfully", db)
            await asyncio.sleep(0.5)

        # ── Step 1: Search & filter ────────────────────────────────────────
        await emit_log(run_id, "info", "Searching for matching internships…", db)
        await asyncio.sleep(1.0)
        total_found = len([j for j in DEMO_JOBS if j[2] in portals])
        await emit_log(run_id, "info", f"Found {total_found * 6} listings · filtering by skills and stipend…", db)
        await asyncio.sleep(0.8)
        await emit_log(run_id, "success", f"Ranked {total_found} high-match jobs · starting applications", db)
        await asyncio.sleep(0.5)

        run.total_found = total_found
        db.commit()

        # ── Step 2 & 3: Apply to each job ─────────────────────────────────
        applied = 0
        for (title, company, portal, url, score) in DEMO_JOBS:
            if portal not in portals:
                continue

            check = db.query(AgentRun).filter(AgentRun.id == run_id).first()
            if check and check.status == RunStatus.stopped:
                break

            await emit_log(run_id, "info", f"Filling form: {title} at {company} ({portal})", db)
            await asyncio.sleep(0.7)
            await emit_log(run_id, "info", f"  ↳ Uploading resume · match score {score:.0f}%", db)
            await asyncio.sleep(0.6)
            await emit_log(run_id, "info", f"  ↳ Generating cover letter for {company}…", db)
            await asyncio.sleep(0.8)

            # Save application to DB
            cover = (
                f"Dear Hiring Team at {company},\n\n"
                f"I am excited to apply for the {title} position. "
                f"With my background in full-stack development and ML, I believe I would be a strong fit. "
                f"I look forward to contributing to {company}'s mission.\n\n"
                f"Best regards"
            )
            app_obj = Application(
                run_id=run_id,
                portal=Portal(portal),
                job_title=title,
                company=company,
                job_url=url,
                match_score=score,
                cover_letter=cover,
                status=AppStatus.applied,
                applied_at=datetime.utcnow(),
            )
            db.add(app_obj)
            db.commit()

            applied += 1
            await emit_log(run_id, "success", f"Applied: {title} at {company}", db)
            await asyncio.sleep(0.4)

        # ── Step 4: Complete ───────────────────────────────────────────────
        run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if run and run.status == RunStatus.running:
            run.status = RunStatus.completed
            run.completed_at = datetime.utcnow()
            run.total_applied = applied
            db.commit()

        await emit_log(run_id, "success", f"Run complete · {applied} applications submitted", db)
        await manager.broadcast({"type": "run_complete", "run_id": run_id})

    except Exception as e:
        logger.exception(f"Agent run {run_id} failed: {e}")
        run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if run:
            run.status = RunStatus.failed
            run.completed_at = datetime.utcnow()
            db.commit()
        await emit_log(run_id, "error", f"Run failed: {str(e)}", db)
    finally:
        db.close()


# ── Real Agent Orchestrator (Phase 2) ─────────────────────────────────────────

async def _run_agent_real(run_id: str, portals: List[str], max_applications: int):
    """
    Real orchestrator using TinyFish browser automation.
    Replaces the demo stub above.
    """
    from models import SessionLocal
    from agent.tinyfish import TinyFishClient
    from agent.claude_ai import ClaudeClient
    from agent.portals.internshala import InternshalaAgent
    from agent.portals.linkedin import LinkedInAgent
    from agent.portals.naukri import NaukriAgent

    db = SessionLocal()
    tf = TinyFishClient()
    claude = ClaudeClient()

    await asyncio.sleep(1.5)  # let WS connect

    async def log(level: str, msg: str):
        await emit_log(run_id, level, msg, db)

    try:
        run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if not run:
            return

        profile = db.query(UserProfile).first()
        if not profile:
            await log("error", "No profile found — set up your profile first")
            return

        total_applied = 0
        per_portal = max(1, max_applications // len(portals))

        for portal in portals:
            check = db.query(AgentRun).filter(AgentRun.id == run_id).first()
            if check and check.status == RunStatus.stopped:
                break

            await log("info", f"Starting {portal} agent…")

            if portal == "internshala":
                agent = InternshalaAgent(tf, claude)
                results = await agent.run(
                    run_id=run_id,
                    profile=profile,
                    email=settings.internshala_email,
                    password=settings.internshala_password,
                    max_apps=per_portal,
                    emit_log=log,
                )
            elif portal == "linkedin":
                agent = LinkedInAgent(tf, claude)
                results = await agent.run(
                    run_id=run_id,
                    profile=profile,
                    email=settings.linkedin_email,
                    password=settings.linkedin_password,
                    max_apps=per_portal,
                    emit_log=log,
                )
            elif portal == "naukri":
                agent = NaukriAgent(tf, claude)
                results = await agent.run(
                    run_id=run_id,
                    profile=profile,
                    email=settings.naukri_email,
                    password=settings.naukri_password,
                    max_apps=per_portal,
                    emit_log=log,
                )
            else:
                await log("warning", f"Unknown portal: {portal} — skipping")
                results = []

            # Save results to DB
            for r in results:
                status = AppStatus.applied if r["status"] == "applied" else AppStatus.failed
                app_obj = Application(
                    run_id=run_id,
                    portal=Portal(portal),
                    job_title=r.get("job_title", ""),
                    company=r.get("company", ""),
                    job_url=r.get("job_url", ""),
                    match_score=r.get("match_score", 0.0),
                    cover_letter=r.get("cover_letter", ""),
                    status=status,
                    error_message=r.get("error", ""),
                    tinyfish_task_id=r.get("tinyfish_run_id", ""),
                    applied_at=datetime.utcnow() if status == AppStatus.applied else None,
                )
                db.add(app_obj)
                db.commit()

                if status == AppStatus.applied:
                    total_applied += 1

        # Mark run complete
        run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if run and run.status == RunStatus.running:
            run.status = RunStatus.completed
            run.completed_at = datetime.utcnow()
            run.total_applied = total_applied
            db.commit()

        await log("success", f"Run complete · {total_applied} real applications submitted")
        await manager.broadcast({"type": "run_complete", "run_id": run_id})

    except Exception as e:
        logger.exception(f"Real agent run {run_id} failed: {e}")
        run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if run:
            run.status = RunStatus.failed
            run.completed_at = datetime.utcnow()
            db.commit()
        await emit_log(run_id, "error", f"Run failed: {str(e)}", db)
    finally:
        db.close()