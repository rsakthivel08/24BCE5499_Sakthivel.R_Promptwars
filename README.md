# AI Multi-Agent Candidate Evaluation System

An AI-powered pipeline that evaluates job candidates using **4 independent AI personas**, a **structured multi-agent debate**, and an **evidence-based Judge agent**.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI |
| Orchestration | LangGraph |
| LLM | Groq API (`llama-3.3-70b-versatile`) |
| Schema | Pydantic v2 |
| Document Extraction | PyMuPDF + python-docx |
| Database | SQLite + SQLAlchemy |
| Frontend | Vanilla HTML / CSS / JS |
| Voice (Bonus) | Sarvam AI TTS (Bulbul V3) |

## Quick Start

### 1. Create & activate conda environment

```bash
conda env create -f environment.yml
conda activate candidate-eval
```

### 2. Configure API keys

```bash
# Edit .env and fill in your keys:
GROQ_API_KEY=your_groq_api_key_here
SARVAM_API_KEY=your_sarvam_api_key_here   # optional — for voice debate
```

### 3. Run the server

```bash
cd candidate_eval
uvicorn app.main:app --reload --port 8000
```

### 4. Open the UI

Visit **http://localhost:8000** in your browser.

### 5. Run tests

```bash
pytest tests/ -v
```

## Pipeline

```
Resume + Transcript
        │
        ▼
Candidate Profile Builder (LLM extraction)
        │
  ┌─────┼──────┬───────┐
  ▼     ▼      ▼       ▼
Tech   HR   HiringMgr  Skeptic
Agent  Agent  Agent   Agent
  (Independent — no cross-contamination)
  └─────┼──────┴───────┘
        ▼
  Structured Debate (2 rounds)
  Round 1: Challenges
  Round 2: Responses + Opinion Updates
        ▼
  Judge Agent (evidence-based, NOT score averaging)
        ▼
  Final Report + Optional Voice Debate
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/upload` | Upload resume + transcript |
| POST | `/api/evaluate/{id}` | Start evaluation pipeline |
| GET | `/api/status/{id}` | Poll pipeline status |
| GET | `/api/results/{id}` | Get full results |
| GET | `/api/report/{id}` | Get final report only |
| POST | `/api/voice/{id}` | Generate voice debate audio |
| GET | `/api/audio/{filename}` | Serve audio file |
| GET | `/docs` | Swagger UI |

## Project Structure

```
candidate_eval/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Settings (pydantic-settings)
│   ├── agents/                    # 4 independent AI agents
│   │   ├── base_agent.py
│   │   ├── technical_agent.py
│   │   ├── hr_agent.py
│   │   ├── hiring_manager_agent.py
│   │   ├── skeptic_agent.py
│   │   ├── schema.py
│   │   └── prompts/
│   ├── profile_builder/           # Candidate profile extraction
│   ├── debate/                    # 2-round structured debate
│   ├── judge/                     # Final decision agent
│   ├── graph/                     # LangGraph pipeline
│   ├── extraction/                # PDF/DOCX text extraction
│   ├── voice/                     # Sarvam AI TTS
│   ├── db/                        # SQLite + SQLAlchemy
│   ├── routes/                    # FastAPI routers
│   └── utils/                     # LLM client, logging
├── static/                        # Frontend (HTML/CSS/JS)
├── tests/                         # pytest test suite
├── data/                          # SQLite DB + uploads (gitignored)
├── .env                           # API keys (gitignored)
├── requirements.txt
└── environment.yml
```

## Key Design Decisions

- **True Independence**: Each agent has its own LLM call with only the Candidate Profile — no agent sees another's evaluation before the debate begins.
- **Evidence Required**: Every strength/concern must include a direct quote or factual reference from the documents.
- **Real Debate**: Agents respond directly to each other's arguments with stances (`agree | disagree | partially_agree | challenge | update_opinion`).
- **No Score Averaging**: The Judge agent explicitly considers evidence strength, agent confidence, concern severity, and unresolved disagreements — not a mathematical average.
- **Transparent Report**: The final report shows reasoning, unresolved disagreements, and suggested interview questions.
