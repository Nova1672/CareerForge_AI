# CareerForge AI — Agentic AI Interview Preparation & Evaluation System

> **AICTE / IBM SkillsBuild / Edunet Foundation Internship Project**

---

## Problem Statement

Job seekers — especially students and early-career professionals — lack access to realistic, personalised mock interview practice. Existing tools either use expensive cloud APIs (requiring user API keys), provide static pre-written questions, or lack structured feedback grounded in the candidate's actual answers.

CareerForge AI solves this by providing a fully agentic, locally-running mock interview system that:
- Generates personalised questions based on the candidate's actual profile
- Evaluates answers dynamically
- Provides structured, grounded feedback without fabricating candidate-specific facts
- Runs entirely locally — no external API key required

---

## Features

- 🎯 **Personalised Questions** — generated based on job role, experience level, skills, projects, and background
- 🤖 **Agentic AI** — powered by IBM Bob ADK agent spec + Ollama local LLM (Gemma 4)
- 🔒 **No API Key Required** — fully local inference via Ollama
- 📊 **Structured Feedback** — score (1–10), strengths, improvements, better example answer per question
- 🧭 **Final Performance Summary** — overall score, strengths, key improvements, preparation roadmap
- 🚫 **Anti-Hallucination Rules** — AI is instructed never to invent candidate-specific facts
- ⚡ **Question Type Mix** — behavioral, technical, applied, project-based, HR/situational
- 📱 **Responsive UI** — works on desktop and mobile

---

## IBM Bob Usage

This project is built using the **IBM watsonx Orchestrate ADK (IBM Bob)**:

| IBM Bob Component | File | Purpose |
|---|---|---|
| Agent Spec | `agents/careerforge_agent.yaml` | Defines the interviewer agent, model binding, and system instructions |
| Model Spec | `models/ollama_gemma4.yaml` | Registers Ollama/Gemma4 as an IBM Bob model provider |
| Workspace Config | `workspace_config.yaml` | Standard IBM Bob folder structure |
| ADK SDK | `venv/` | `ibm-watsonx-orchestrate` 2.16.1 installed in project venv |
| MCP Config | `.bob/mcp.json` | watsonx-orchestrate MCP server configuration |

The backend (`server.py`) loads the agent's system instructions directly from the IBM Bob agent YAML spec at runtime using `ibm_watsonx_orchestrate.agent_builder` conventions.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Browser (index.html)            │
│  Setup Form → Interview → Feedback → Summary    │
│  Fetches: /api/generate-question                │
│           /api/evaluate-answer                  │
│           /api/generate-summary                 │
│           /api/status                           │
└─────────────────┬───────────────────────────────┘
                  │ HTTP (same origin, port 8000)
┌─────────────────▼───────────────────────────────┐
│          FastAPI Backend (server.py)             │
│                                                  │
│  ① Loads agent instructions from               │
│     agents/careerforge_agent.yaml               │
│     (IBM Bob ADK agent spec)                    │
│                                                  │
│  ② Constructs structured prompts                │
│     with anti-hallucination rules               │
│                                                  │
│  ③ Calls Ollama API                            │
│     (registered as IBM Bob model:               │
│      models/ollama_gemma4.yaml)                 │
└─────────────────┬───────────────────────────────┘
                  │ HTTP (localhost:11434)
┌─────────────────▼───────────────────────────────┐
│         Ollama (gemma4:latest, 8B, local)        │
│  No external API key — runs on local hardware   │
└─────────────────────────────────────────────────┘
```

---

## Project Structure

```
CareerForge-AI/
├── index.html                 # Frontend — single-page interview UI
├── server.py                  # Backend — FastAPI server
├── workspace_config.yaml      # IBM Bob ADK workspace configuration
├── README.md                  # This file
│
├── agents/
│   └── careerforge_agent.yaml # IBM Bob agent definition (interviewer agent)
│
├── models/
│   └── ollama_gemma4.yaml     # IBM Bob model registration (Ollama/Gemma4)
│
├── .bob/
│   └── mcp.json               # IBM Bob MCP server config
│
├── venv/                      # Python virtual env (ibm-watsonx-orchestrate SDK)
├── connections/               # IBM Bob connections folder (reserved)
├── tools/                     # IBM Bob tools folder (reserved)
├── toolkits/                  # IBM Bob toolkits folder (reserved)
└── knowledge-bases/           # IBM Bob knowledge bases folder (reserved)
```

---

## How to Run

### Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.10+ | `python --version` |
| Ollama | Any | `ollama --version` |
| Gemma4 model | 8B or e2b | `ollama list` |

### Step 1 — Ensure Ollama is running with the Gemma 4 model

```bash
# Start Ollama (if not already running as a service)
ollama serve

# Pull the model (if not already downloaded)
ollama pull gemma4:latest
```

### Step 2 — Install Python dependencies into the project venv

The project venv (`venv/`) already has `ibm-watsonx-orchestrate`. Run this once to add the server dependencies:

```powershell
# Windows (PowerShell)
.\venv\Scripts\pip.exe install fastapi uvicorn httpx pyyaml

# macOS / Linux
./venv/bin/pip install fastapi uvicorn httpx pyyaml
```

### Step 3 — Start the backend server

```powershell
# Windows — activate venv first, then run
.\venv\Scripts\Activate.ps1
python server.py

# Or run directly without activating
.\venv\Scripts\python.exe server.py
```

```bash
# macOS / Linux
source venv/bin/activate
python server.py
```

You should see:
```
============================================================
  CareerForge AI — Backend Server
  IBM Bob ADK + Ollama/Gemma4 (local, no API key)
============================================================
  Agent spec : agents/careerforge_agent.yaml
  Model      : gemma4:latest
  Ollama URL : http://localhost:11434
  Open       : http://localhost:8000
============================================================
```

### Step 4 — Open the application

Visit **[http://localhost:8000](http://localhost:8000)** in your browser.

The status bar on the setup page shows whether the AI model is ready.

---

## Interview Flow

```
1. User fills setup form
   (job role, experience level, skills, optional projects/resume)
         ↓
2. Backend generates Q1 (Behavioral/Introductory)
   using agent system instructions from careerforge_agent.yaml
         ↓
3. User types and submits answer
         ↓
4. Backend evaluates answer via Ollama/Gemma4
   Returns: score, strengths, improvements, better example answer
         ↓
5. UI shows feedback card
         ↓
6. User clicks "Next Question"
         ↓
7. Repeat steps 2–6 for Q2 (Technical), Q3 (Applied),
   Q4 (Project), Q5 (HR/Situational)
         ↓
8. After Q5, backend generates final summary:
   overall score, strengths, key improvements, preparation roadmap
         ↓
9. User can start a new interview
```

### Question Type Sequence

| Question | Type | Focus |
|---|---|---|
| Q1 | Behavioral / Introductory | Self-introduction, motivation, background |
| Q2 | Technical / Conceptual | Core knowledge from stated skills |
| Q3 | Technical / Applied | Problem-solving, hands-on approach |
| Q4 | Project-Based | Specific project, decision, or challenge |
| Q5 | HR / Situational | Teamwork, communication, career goals |

---

## Grounding / Hallucination-Control Rules

The AI is explicitly instructed (via agent spec) to:

1. **Never invent** candidate-specific facts not mentioned by the candidate:
   - Accuracy, ROC-AUC, F1, precision, recall scores
   - Dataset sizes, columns, or features
   - Project results or business impact
   - Employers, certifications, grades, achievements
   - Tools, models, or technologies not mentioned

2. **Always use** `"This information was not provided."` when specific data is missing

3. **Use placeholders** `[Insert your verified result here]` in example answers where candidate-specific data would normally appear

4. **Perform a self-check** before every feedback response:
   > "Did I add any candidate-specific fact that the candidate never provided? If yes, remove it."

---

## Sample Test Case

**Target Role:** Data Scientist Intern  
**Experience:** Student / Entry Level (0–1 years)  
**Skills:** Python, Pandas, NumPy, SQL, Scikit-learn, Machine Learning

**Sample Q2 (Technical):**
> "How do you handle missing values in a dataset, and what factors influence your choice of imputation strategy?"

**Sample Candidate Answer:**
> "I usually handle missing values by checking how much data is missing first. For numerical data, I may use mean or median imputation depending on the distribution."

**Expected Evaluation:**
- Score: 5–7/10
- Strengths: mentions checking missing data ratio; understands mean vs median
- Improvements: does not mention MCAR/MAR/MNAR; no mention of dropping rows/columns threshold; no mention of model-based imputation
- Better Answer: improves structure without inventing accuracy figures or dataset names

---

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `gemma4:latest` | Model to use for inference |

To use the smaller model:
```bash
OLLAMA_MODEL=gemma4:e2b python server.py
```

---

## Screenshots

> *(Add screenshots here after running the application)*

| Screen | Description |
|---|---|
| Setup Form | ![Setup](screenshots/setup.png) |
| Interview Question | ![Question](screenshots/question.png) |
| Feedback | ![Feedback](screenshots/feedback.png) |
| Final Summary | ![Summary](screenshots/summary.png) |

---

## Limitations

- Requires Ollama running locally (not a cloud deployment)
- Gemma 4 (8B) may occasionally produce JSON that needs repair — the backend handles this defensively
- Interview is fixed at 5 questions
- No persistence — session data is in-memory only
- No authentication or user management

---

## Future Scope

- [ ] Add resume PDF upload and parsing
- [ ] Support additional local models (Llama 3, Mistral, Phi-3)
- [ ] Persist sessions to a local database (SQLite)
- [ ] IBM watsonx.ai cloud model integration (when credentials are available)
- [ ] Voice input/output support
- [ ] Difficulty adjustment based on answer quality
- [ ] Export interview report as PDF

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | IBM watsonx Orchestrate ADK (IBM Bob) 2.16.1 |
| LLM | Ollama + Gemma 4 (8B, local) |
| Backend | Python 3 + FastAPI + uvicorn |
| HTTP Client | httpx (async) |
| Frontend | Vanilla HTML + CSS + JavaScript |
| Agent Spec | IBM Bob ADK YAML (kind: agent, kind: model) |

---

*Built for AICTE / IBM SkillsBuild / Edunet Foundation Internship Evaluation*  
*Demonstrates genuine IBM Bob ADK agent development with local LLM inference*
