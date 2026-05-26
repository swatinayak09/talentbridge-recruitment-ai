# TalentBridge Recruitment AI

Capstone prototype for **TalentBridge Staffing Solutions** — an Agentic AI Recruitment Process Support System.

This repository implements two specialized agents:

| Agent | Responsibility |
|-------|----------------|
| **Pipeline Insights Agent** | Real-time pipeline summaries, bottleneck analysis, aging applications, role-wise status |
| **Escalation & Compliance Agent** | Routes sensitive/high-risk cases to human recruiters; fairness checks; policy enforcement |

Repository: [github.com/swatinayak09/talentbridge-recruitment-ai](https://github.com/swatinayak09/talentbridge-recruitment-ai)

---

## Prerequisites

- **Python 3.10 or newer** ([python.org/downloads](https://www.python.org/downloads/))
- A modern web browser (Chrome, Edge, Firefox)
- **No pip install required** — the app uses Python’s standard library only

To verify Python:

```powershell
python --version
```

---

## How to Run

### 1. Clone the repository

```powershell
git clone https://github.com/swatinayak09/talentbridge-recruitment-ai.git
cd talentbridge-recruitment-ai
```

### 2. Start the server

From the project root:

```powershell
python run.py
```

You should see:

```text
TalentBridge dashboard: http://127.0.0.1:8000
Press Ctrl+C to stop.
```

### 3. Open the dashboard

In your browser, go to:

**http://127.0.0.1:8000**

### 4. Use the dashboard

- **Pipeline Insights Agent** tab — bottlenecks, aging applications, role health, priority actions
- **Escalation & Compliance Agent** tab — human review queue, fairness checks, policy reminders
- **Filter** — use the requisition dropdown to scope results to one role
- **Refresh Agents** — reload agent output from sample data

### 5. Stop the server

Press `Ctrl+C` in the terminal.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `python` not found | Install Python and ensure “Add to PATH” was checked, or use `py run.py` on Windows |
| Port 8000 in use | Close the other app using port 8000, or change `PORT = 8000` in `run.py` |
| Blank dashboard / API errors | Confirm `python run.py` is running and you opened `http://127.0.0.1:8000` (not a `file://` path) |

---

## Project Structure

```text
talentbridge-recruitment-ai/
├── run.py                  # Start here — HTTP server (recommended)
├── main.py                 # Optional FastAPI variant (requires pip)
├── agents/
│   ├── pipeline_insights.py
│   └── escalation_compliance.py
├── data/
│   └── pipeline.json       # Sample requisitions & candidates
├── static/
│   ├── index.html          # Recruiter dashboard (orange / black / white UI)
│   ├── styles.css
│   └── app.js
└── docs/
    └── AGENTS.md           # Agent design & API reference
```

---

## API Endpoints

With the server running (`python run.py`):

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard UI |
| `GET /api/agents/pipeline-insights?requisition_id=` | Pipeline Insights report |
| `GET /api/agents/escalation-compliance?requisition_id=` | Escalation & Compliance report |
| `GET /api/agents/combined?requisition_id=` | Both agents in one response |
| `GET /api/requisitions` | List requisitions for the filter dropdown |

Example:

```text
http://127.0.0.1:8000/api/agents/combined
```

---

## Human-in-the-Loop

This prototype **does not** make autonomous hiring decisions. Escalations with `auto_hold: true` flag candidates that must not advance until a recruiter or compliance officer reviews the case.

---

## UI Theme

The dashboard uses **orange**, **black**, and **white** as the primary brand colors.

---

## Documentation

See [docs/AGENTS.md](docs/AGENTS.md) for agent responsibilities, escalation rules, and architecture notes for your capstone report.

---

## Team / Capstone Context

Part of the wider **Agentic AI Recruitment Process Support System** for TalentBridge Staffing Solutions. Other agents (job intake, screening, communication, etc.) may live in sibling repos or future branches.

---

## License

Academic capstone project — see course guidelines for use and attribution.
