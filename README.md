# MTEAS — Multi-Trigger Emergency Assistance System

A layered-verification emergency assistance prototype that connects three actors via voice, web, and real-time alerts.

| Actor | Interface | Technology |
|---|---|---|
| Household User | Desktop GUI (always-on mic) | Python + PyQt6 |
| Emergency Responder | Web browser — CAD terminal | React + FastAPI WebSocket |
| System Administrator | Web browser — admin dashboard | React + FastAPI REST |

---

## Architecture

```
[PyQt6 Desktop App]  →  POST /api/dispatch  →  [FastAPI Backend]  →  WebSocket push
       ↑                                              ↓
  Mic / TTS                                    PostgreSQL DB
  Keyword → Claps                                    ↓
  → Modifier → Countdown                   [React SPA — Vercel]
                                        /responder  /admin
```

The household device is always listening. When the user speaks a keyword, claps the required number of times, and optionally says a modifier word (fire / health / danger), a countdown starts before the alert fires. The backend saves the event and instantly pushes it over WebSocket to every logged-in responder of the matching role.

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| PostgreSQL | 14+ | Running locally or remote |
| Git | any | To clone the repo |

Windows users: install [PyAudio](https://pypi.org/project/PyAudio/) via a pre-built wheel if `pip install pyaudio` fails — see [this guide](https://stackoverflow.com/questions/52283840).

---

## Local Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd VoiceClapTriggerSystem
```

### 2. PostgreSQL — create the database

```sql
-- Run in psql or pgAdmin
CREATE DATABASE mteas;
```

### 3. Python environment

```bash
# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install everything — backend + desktop app
pip install -r requirements-gui.txt
```

### 4. Backend — environment variables

Create a `.env` file in the **project root** (next to `requirements.txt`):

```env
DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost/mteas
MTEAS_JWT_SECRET=any-long-random-string-you-choose
```

Replace `<user>` and `<password>` with your local PostgreSQL credentials.

### 5. Start the backend

```bash
# From the project root, with the .venv active
uvicorn backend.main:app --reload
```

The backend starts on **http://localhost:8000**.  
On first run it automatically creates all tables and seeds the default accounts (see [Test Accounts](#test-accounts)).

Swagger UI (interactive API docs): http://localhost:8000/docs

### 6. Frontend — React SPA

```bash
cd frontend
npm install
npm run dev
```

The React SPA starts on **http://localhost:5173**.

- Admin dashboard: http://localhost:5173/admin
- Responder CAD terminal: http://localhost:5173/responder

> The `frontend/.env` file is already set to point at `http://localhost:8000`, so no extra config is needed for local dev.

### 7. PyQt6 Desktop App (Household User)

```bash
# From the project root, with the .venv active
python -m gui.app
```

On first launch:

1. Go to the **Settings** tab.
2. Set **Dispatch channel** to `backend`.
3. Set **Backend API URL** to `http://localhost:8000` (default) — or your deployed Render URL for the live system.
4. Paste a **Device Token** generated from the Household Signup page (`http://localhost:5173/signup/household`).
5. Click **Save profile**.
6. Switch to the **Dashboard** tab and click **Start Listening**.

---

## Test Accounts

These are seeded automatically on the first backend startup:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | System Administrator |
| `responder_health` | `health123` | Health / Medical Responder |
| `responder_fire` | `fire123` | Fire Responder |
| `responder_police` | `police123` | Police / Security Responder |

A seed household is also created: **"Test Home (Rwanda)"** — device token `dev_kigali_123` — pre-loaded into `mteas_config.json` if you want to skip the signup flow.

---

## Demo Flow

1. **Start** the backend (`uvicorn`) and frontend (`npm run dev`).
2. Open http://localhost:5173 in a browser, log in as **`responder_fire`** / `fire123`.
3. The Responder CAD terminal shows a live WebSocket badge (green dot).
4. In a second tab, log in as **`admin`** / `admin123` — see the overview map.
5. Launch `python -m gui.app`.
6. On the Dashboard, click **Start Listening** — the mic starts monitoring.
7. Say the keyword (default: *"jesus"*), clap twice, say *"fire"* — then let the countdown complete.
   - Or use the **Developer / Test** panel to inject steps without a mic.
8. Watch the Responder console receive the alert with an audible alarm, map pin, and address.
9. Acknowledge → complete the SOP checklist (En Route → On Scene → Scene Secured) → Resolve.
10. The Admin Overview map updates and the event moves to history.

---

## Environment Variables Reference

### Backend (root `.env`)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `MTEAS_JWT_SECRET` | Yes | Secret key for signing JWT tokens |
| `ENV` | No | `development` (default) or `production` |

### Frontend (`frontend/.env` or Vercel dashboard)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Base URL for all REST API calls |
| `VITE_WS_URL` | `ws://localhost:8000` | Base URL for WebSocket connection |

---

## Project Structure

```
VoiceClapTriggerSystem/
├── backend/                  FastAPI backend
│   ├── main.py               Entry point — routes, CORS, lifespan
│   ├── auth.py               JWT helpers
│   ├── database.py           SQLAlchemy models + seed data
│   └── routes/
│       ├── auth.py           Login, signup (responder + household)
│       ├── dispatch.py       POST /api/dispatch — receives PyQt events
│       ├── events.py         Event log + stats + status updates
│       ├── admin.py          Admin-only user/household/config routes
│       └── ws.py             WebSocket hub
├── frontend/                 React + Vite SPA
│   ├── src/
│   │   ├── App.jsx           Router + auth context
│   │   ├── pages/
│   │   │   ├── admin/        Admin dashboard pages
│   │   │   └── responder/    Responder CAD terminal pages
│   │   └── components/
│   │       └── BaseMap.jsx   Leaflet map with pins, triangulation, heatmap
│   ├── .env                  Local dev env vars
│   └── vercel.json           SPA routing config for Vercel
├── gui/
│   └── app.py                PyQt6 desktop app (Household User)
├── mteas/                    Core engine (keyword, claps, dispatch, state machine)
├── tests/                    Unit + integration tests
├── docs/
│   ├── SRS_ADDENDUM.md       Multi-actor SRS extension (FR 7–9)
│   └── DESIGN_DECISIONS.md   Logged architecture decisions
├── render.yaml               Render deployment blueprint
├── requirements.txt          Backend-only deps (what Render installs)
├── requirements-gui.txt      Full local deps — backend + desktop app
└── .env                      Local backend secrets (not committed)
```

---

## Running Tests

```bash
# Python unit tests
python -m unittest discover -s tests -p "test_*.py"

# Headless engine demo (no mic required)
python -m mteas.sim_demo
```
