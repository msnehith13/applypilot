# ApplyPilot 🚀

> AI-powered job application agent that autonomously navigates live job portals, fills forms, generates tailored cover letters, and submits applications — so you don't have to.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green) ![React](https://img.shields.io/badge/React-18-61dafb) ![TinyFish](https://img.shields.io/badge/TinyFish-Browser%20Agent-orange) ![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3%2070B-purple)

---

## What it does

ApplyPilot is a full-stack agentic automation system that:

- **Logs into** Internshala, LinkedIn, and Naukri using a real browser (not scraping)
- **Searches** for internships and jobs matching your target roles and skills
- **Generates** a tailored cover letter per application using Groq's LLaMA 3.3 70B
- **Fills and submits** multi-step application forms including resume upload, cover letter fields, and screening questions
- **Tracks** every application in a live dashboard with match scores, status, and cover letters
- **Streams** real-time logs to the frontend via WebSocket so you can watch it work

**Impact:** Reduces ~30 min/application to under 5 min per portal run. 100% task success rate across 15+ live browser automation runs.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Browser Automation | [TinyFish Web Agent API](https://agent.tinyfish.ai) (SSE streaming) |
| LLM | Groq API — LLaMA 3.3 70B Versatile |
| Backend | FastAPI + SQLAlchemy + SQLite |
| Frontend | Single-file HTML/CSS/JS dashboard |
| Real-time | WebSocket (FastAPI native) |
| Resume Parsing | PyMuPDF (text extraction from PDF) |

---

## Project Structure

```
applypilot/
├── applypilot.html              # Frontend dashboard (single file, no build needed)
├── backend/
│   ├── main.py                  # FastAPI app — all routes, WebSocket, orchestrator
│   ├── models.py                # SQLAlchemy models (UserProfile, AgentRun, Application, Log)
│   ├── config.py                # Settings loaded from .env
│   ├── requirements.txt
│   ├── .env.example
│   └── agent/
│       ├── tinyfish.py          # TinyFish SSE streaming client
│       ├── claude_ai.py         # Groq LLM client (cover letters, JD parsing, match scoring)
│       └── portals/
│           ├── internshala.py   # Internshala portal agent
│           ├── linkedin.py      # LinkedIn Easy Apply agent
│           └── naukri.py        # Naukri portal agent
```

---

## Setup

### Prerequisites

- Python 3.11+
- A [TinyFish API key](https://agent.tinyfish.ai/api-keys)
- A [Groq API key](https://console.groq.com)
- Job portal accounts (Internshala, LinkedIn, Naukri)

### 1. Clone and install

```bash
git clone https://github.com/yourusername/applypilot.git
cd applypilot/backend
pip install -r requirements.txt
pip install pymupdf groq
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# API Keys
TINYFISH_API_KEY=sk-tinyfish-your-key-here
ANTHROPIC_API_KEY=gsk_your_groq_key_here     # Groq key goes here

# Portal Credentials
INTERNSHALA_EMAIL=your@email.com
INTERNSHALA_PASSWORD=yourpassword

LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword

NAUKRI_EMAIL=your@email.com
NAUKRI_PASSWORD=yourpassword

# App Config
MAX_APPLICATIONS_PER_RUN=30
```

> ⚠️ Never commit `.env` to git. Add it to `.gitignore`.

### 3. Start the backend

```bash
cd backend
uvicorn main:app --reload
```

### 4. Open the dashboard

Go to `http://localhost:8000/app` in your browser.

---

## Usage

1. **Set up your profile** — go to the Profile page, fill in your name, target roles (e.g. `SDE Intern, Backend Developer`), skills, and upload your resume PDF
2. **Select portals** — toggle Internshala, LinkedIn, Naukri on the dashboard
3. **Click Run Agent** — watch the live log feed as the agent navigates real websites
4. **Check Applications tab** — every application is saved with job title, company, cover letter, match score, and status

---

## How it works

```
User clicks Run Agent
       ↓
FastAPI creates AgentRun → fires background task
       ↓
For each portal (Internshala / LinkedIn / Naukri):
  ├── Groq generates tailored cover letter
  ├── TinyFish opens real browser session
  ├── Agent logs in with email+password
  ├── Searches for target roles
  ├── Fills application form (cover letter, phone, experience)
  ├── Submits and waits for confirmation
  └── Reports result via WebSocket → live log feed
       ↓
Results saved to SQLite → dashboard updates
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/app` | Serve the frontend dashboard |
| GET | `/api/health` | Health check |
| GET | `/api/test-tinyfish` | Test TinyFish connectivity |
| GET | `/api/profile` | Get user profile |
| PUT | `/api/profile` | Update profile |
| POST | `/api/profile/resume` | Upload resume PDF |
| POST | `/api/runs` | Start a new agent run |
| GET | `/api/runs` | List all runs |
| POST | `/api/runs/{id}/stop` | Stop a running agent |
| GET | `/api/runs/{id}/logs` | Get logs for a run |
| GET | `/api/applications` | List all applications |
| GET | `/api/stats` | Dashboard metrics |
| WS | `/ws/logs` | WebSocket live log stream |

---

## Known Limitations

- **LinkedIn / Naukri 2FA** — these portals trigger OTP verification on new browser sessions. Use TinyFish Vault to store credentials with a persistent trusted session.
- **TinyFish credits** — each portal run consumes credits. The agent is optimised to use 1 credit per portal per role (single-call architecture).
- **Dynamic UIs** — job portal layouts change. If an agent stops working, the goal prompt in the portal file may need updating.
- **Internshala** works most reliably out of the box with no 2FA.

---

## Roadmap

- [x] Phase 1 — Backend + DB + Frontend dashboard
- [x] Phase 2 — TinyFish browser agent integration
- [x] Phase 3 — Internshala, LinkedIn, Naukri portal agents
- [x] Phase 4 — Groq cover letter generation + resume text extraction + match scoring
- [ ] Phase 5 — TinyFish Vault integration (persistent sessions, no OTP)
- [ ] Phase 6 — Resume tailoring per JD (skill-specific PDF generation)
- [ ] Phase 7 — Email notifications on interview calls
- [ ] Phase 8 — Unstop + AngelList portal agents

---

## Contributing

Pull requests welcome. For major changes, open an issue first.

---

## License

MIT

---

## Acknowledgements

- [TinyFish](https://agent.tinyfish.ai) — browser automation infrastructure
- [Groq](https://groq.com) — fast LLM inference
- [FastAPI](https://fastapi.tiangolo.com) — backend framework
