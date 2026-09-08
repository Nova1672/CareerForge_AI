"""
CareerForge AI — Backend Server
================================
FastAPI server that powers the CareerForge AI mock interview application.

Architecture:
  - Reads agent instructions from agents/careerforge_agent.yaml (IBM Bob ADK spec)
  - Calls Ollama local LLM (gemma4:latest) — no external API key required
  - Serves a REST API consumed by index.html (frontend)
  - All AI generation is dynamic — no hardcoded or fake responses

Run (from project root, with venv active):
  venv/Scripts/python server.py
  # or, if venv is already activated in your terminal:
  python server.py
"""

import json
import logging
import os
import re
import sys
import yaml
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("careerforge")

# ── Config ─────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "gemma4:latest")
AGENT_YAML_PATH = Path(__file__).parent / "agents" / "careerforge_agent.yaml"
TOTAL_QUESTIONS = 5

# ── Load agent instructions from IBM Bob agent spec ────────────────────────
def load_agent_instructions() -> str:
    """Load system instructions from the IBM Bob ADK agent YAML spec."""
    if not AGENT_YAML_PATH.exists():
        raise RuntimeError(f"Agent spec not found: {AGENT_YAML_PATH}")
    with open(AGENT_YAML_PATH, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    instructions = spec.get("spec", {}).get("instructions", "")
    if not instructions:
        raise RuntimeError("No instructions found in agent spec.")
    return instructions.strip()

AGENT_INSTRUCTIONS = load_agent_instructions()

# ── FastAPI app ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="CareerForge AI",
    description="Agentic AI Mock Interview — powered by IBM Bob ADK + Ollama/Gemma4",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
    )

# Serve index.html and static files from the project root
app.mount("/static", StaticFiles(directory="."), name="static")


@app.get("/")
def serve_index():
    return FileResponse("index.html")


# ── Pydantic models ─────────────────────────────────────────────────────────
class CandidateProfile(BaseModel):
    jobRole: str
    experienceLevel: str
    keySkills: str
    projectDetails: Optional[str] = ""
    candidateInfo: Optional[str] = ""


class GenerateQuestionRequest(BaseModel):
    profile: CandidateProfile
    questionNumber: int                # 1-indexed
    previousQuestions: List[str] = []


class EvaluateAnswerRequest(BaseModel):
    profile: CandidateProfile
    question: str
    answer: str
    questionNumber: int


class GenerateSummaryRequest(BaseModel):
    profile: CandidateProfile
    questions: List[str]
    answers: List[str]
    scores: List[int]


# ── Ollama helper ───────────────────────────────────────────────────────────
async def call_ollama(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """
    Call Ollama chat completions API.
    Uses the same model registered in models/ollama_gemma4.yaml.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 1024,
        },
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            resp.raise_for_status()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
                       "Please ensure Ollama is running: `ollama serve`"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Ollama error: {e.response.text}")

    data = resp.json()
    return data["message"]["content"].strip()


def clean_json_response(raw: str) -> dict:
    """
    Defensively parse JSON from LLM response.
    Strips markdown fences, extracts first JSON object found.
    """
    # Remove code fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    cleaned = cleaned.strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Extract first {...} block
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response:\n{raw[:500]}")


# ── Profile context helper ──────────────────────────────────────────────────
def format_profile(p: CandidateProfile) -> str:
    parts = [
        f"Target Role: {p.jobRole}",
        f"Experience Level: {p.experienceLevel}",
        f"Key Skills: {p.keySkills}",
    ]
    if p.projectDetails and p.projectDetails.strip():
        parts.append(f"Project Details: {p.projectDetails.strip()}")
    if p.candidateInfo and p.candidateInfo.strip():
        parts.append(f"Candidate Background: {p.candidateInfo.strip()}")
    return "\n".join(parts)


# ── Routes ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": OLLAMA_MODEL,
        "ollama": OLLAMA_BASE_URL,
        "agent": str(AGENT_YAML_PATH),
    }


@app.post("/api/generate-question")
async def generate_question(req: GenerateQuestionRequest):
    """
    Generate the next interview question.
    Question type varies by question number:
      1 → behavioral/intro
      2-3 → technical/skill-based
      4 → project-based (if project info provided, else situational)
      5 → HR/situational
    """
    profile_ctx = format_profile(req.profile)
    prev = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(req.previousQuestions)) if req.previousQuestions else "  None"

    # Determine question category
    q_types = {
        1: "behavioral or introductory (e.g. tell me about yourself, motivation, background)",
        2: "technical/conceptual — test understanding of core concepts from the stated skills",
        3: "technical/applied — a hands-on problem-solving or coding/approach question",
        4: "project-based — ask about a specific project, challenge, or technical decision the candidate made" if (req.profile.projectDetails or req.profile.candidateInfo) else "situational — describe a challenging scenario the candidate would face in this role",
        5: "HR/situational — about teamwork, communication, handling conflict, or career goals",
    }
    q_type = q_types.get(req.questionNumber, "technical")

    user_prompt = f"""
Candidate Profile:
{profile_ctx}

This is question {req.questionNumber} of {TOTAL_QUESTIONS}.
Question type for this turn: {q_type}

Previously asked questions (do NOT repeat these):
{prev}

Generate exactly ONE interview question of the specified type.
Calibrate difficulty to the candidate's experience level.
Return ONLY the question text — no numbering, no preamble, no quotes.
""".strip()

    question = await call_ollama(AGENT_INSTRUCTIONS, user_prompt, temperature=0.8)
    # Strip any accidental numbering or quotes
    question = re.sub(r"^[\"\']|[\"\']$", "", question.strip())
    question = re.sub(r"^\d+[\.\)]\s*", "", question)

    return {"question": question.strip()}


@app.post("/api/evaluate-answer")
async def evaluate_answer(req: EvaluateAnswerRequest):
    """
    Evaluate a candidate's answer and return structured feedback.
    Grounding rules enforced via system prompt to prevent hallucination.
    """
    profile_ctx = format_profile(req.profile)

    user_prompt = f"""
Candidate Profile:
{profile_ctx}

Interview Question (Q{req.questionNumber}):
{req.question}

Candidate's Answer:
{req.answer if req.answer.strip() else "[The candidate did not provide an answer]"}

Evaluate the answer and return feedback as a JSON object.
GROUNDING CHECK: Before finalising, verify you have NOT added any specific fact
(metric, number, tool, employer, project outcome) that the candidate did not mention.
If any fact is missing from the answer, note it in improvements using:
"This information was not provided."

Return ONLY this JSON structure, no other text:
{{
  "score": <integer 1-10>,
  "strengths": [<2-3 string points>],
  "improvements": [<2-3 string points>],
  "betterAnswer": "<improved answer — same facts as candidate gave, better structure. Use [Insert your verified result here] for any missing specifics>"
}}
""".strip()

    raw = await call_ollama(AGENT_INSTRUCTIONS, user_prompt, temperature=0.4)

    try:
        feedback = clean_json_response(raw)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Validate and normalise
    feedback["score"] = max(1, min(10, int(feedback.get("score", 5))))
    if not isinstance(feedback.get("strengths"), list):
        feedback["strengths"] = [str(feedback.get("strengths", ""))]
    if not isinstance(feedback.get("improvements"), list):
        feedback["improvements"] = [str(feedback.get("improvements", ""))]
    if not isinstance(feedback.get("betterAnswer"), str):
        feedback["betterAnswer"] = str(feedback.get("betterAnswer", ""))

    return feedback


@app.post("/api/generate-summary")
async def generate_summary(req: GenerateSummaryRequest):
    """
    Generate a final performance summary after all questions are answered.
    """
    profile_ctx = format_profile(req.profile)

    qa_lines = []
    for i, (q, a, s) in enumerate(zip(req.questions, req.answers, req.scores)):
        qa_lines.append(f"Q{i+1} (Score {s}/10): {q}\nAnswer: {a or '[Not answered]'}")
    qa_block = "\n\n".join(qa_lines)

    avg_score = round(sum(req.scores) / len(req.scores), 1) if req.scores else 0.0

    user_prompt = f"""
Candidate Profile:
{profile_ctx}

Full Interview Transcript:
{qa_block}

Average Score: {avg_score}/10

Generate a final performance summary as a JSON object.
Base observations ONLY on what the candidate actually said and the scores above.
Do NOT invent specific metrics, projects, or achievements not mentioned.

Return ONLY this JSON structure, no other text:
{{
  "overallScore": {avg_score},
  "overallStrengths": [<2-4 string points based on interview evidence>],
  "keyImprovements": [<2-4 string points based on interview evidence>],
  "preparationRoadmap": [<3-5 actionable steps tailored to this role and skills>]
}}
""".strip()

    raw = await call_ollama(AGENT_INSTRUCTIONS, user_prompt, temperature=0.4)

    try:
        summary = clean_json_response(raw)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Normalise
    summary["overallScore"] = avg_score
    for key in ("overallStrengths", "keyImprovements", "preparationRoadmap"):
        if not isinstance(summary.get(key), list):
            summary[key] = [str(summary.get(key, ""))]

    return summary


@app.get("/api/status")
async def model_status():
    """Check Ollama connectivity and model availability."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
        return {
            "ollama": "connected",
            "availableModels": models,
            "activeModel": OLLAMA_MODEL,
            "modelReady": any(OLLAMA_MODEL.split(":")[0] in m for m in models),
        }
    except Exception as e:
        return {
            "ollama": "unreachable",
            "error": str(e),
            "activeModel": OLLAMA_MODEL,
            "modelReady": False,
        }


# ── Entry point ──────────────────────────────────────────────────────────────
def _free_port(port: int):
    """Kill any process already listening on the given port (Windows + Unix)."""
    import subprocess, platform
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if f":{port} " in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    if pid.isdigit() and int(pid) > 0:
                        subprocess.run(["taskkill", "/F", "/PID", pid],
                                       capture_output=True)
                        logger.info("Freed port %d (killed PID %s)", port, pid)
        else:
            result = subprocess.run(
                ["lsof", "-ti", f"tcp:{port}"],
                capture_output=True, text=True
            )
            for pid in result.stdout.strip().splitlines():
                if pid.isdigit():
                    subprocess.run(["kill", "-9", pid], capture_output=True)
                    logger.info("Freed port %d (killed PID %s)", port, pid)
    except Exception as e:
        logger.warning("Could not free port %d: %s", port, e)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    _free_port(port)
    print("\n" + "="*60)
    print("  CareerForge AI — Backend Server")
    print("  IBM Bob ADK + Ollama/Gemma4 (local, no API key)")
    print("="*60)
    print(f"  Agent spec : {AGENT_YAML_PATH}")
    print(f"  Model      : {OLLAMA_MODEL}")
    print(f"  Ollama URL : {OLLAMA_BASE_URL}")
    print(f"  Open       : http://localhost:{port}")
    print("="*60 + "\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
