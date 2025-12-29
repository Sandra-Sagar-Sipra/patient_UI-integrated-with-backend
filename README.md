# 🐍 NeuroAssist v3 - Python Backend (FastAPI)

This is the refactored clinical backend migrated from Node.js to Python FastAPI, designed for secure, asynchronous processing of medical consultations. It integrates **active** Speech-to-Text (AssemblyAI) and supports LLM integration (Gemini - currently configured as disabled).

## 🌟 Key Features (Current State)

*   **Speech-to-Text (STT)**:
    *   **Engine**: AssemblyAI Python SDK (Asynchronous Polling).
    *   **Word Boost**: Optimized for neurological terminology (e.g., "Levetiracetam", "Donepezil") using custom vocabulary configurations.
    *   **Privacy**: Implementation includes PII Redaction and Speaker Diarization.
*   **LLM (Active)**: **Google Gemini 2.0 Flash** integrated for Context-Aware SOAP Note generation.
*   **Context Injection**: Automatically incorporates patient demographics (Age, Gender, History) into the prompt.
*   **Resilience**: Robust error handling for corrupt file uploads and network issues.
*   **Verification**: Comprehensive automated test suite for End-to-End validation.
*   **Smart Triage (New)**: AI-driven urgency scoring and patient prioritization.
*   **Clinical Safety (New)**: Automated drug-condition contraindication checks.

## 🚀 Quick Start (Docker - Recommended)

1.  **Configure Environment**:
    Edit the `environment` section in `docker-compose.yml` with your API keys:
    *   `ASSEMBLYAI_API_KEY` (Required)
    *   `GOOGLE_API_KEY` (Required for LLM Features - SOAP Notes)

2.  **Run with Docker Compose**:
    ```bash
    docker-compose up --build
    ```

The system will be accessible at:
*   **API Gateway**: `http://localhost/` (Nginx)
*   **Swagger Docs**: `http://localhost/docs` (FastAPI)
*   **Health Check**: `http://localhost/api/v1/health`

## 🛠️ Local Development (No Docker)

1.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Setup Environment**:
    Create a `.env` file based on `.env.example`.
    *   **SECURITY NOTE**: Never commit your `.env` file. It is gitignored.
    *   Fill in `ASSEMBLYAI_API_KEY` and `GOOGLE_API_KEY` with your actual secrets.
    *   `DATABASE_URL` defaults to PostgreSQL.

3.  **Run the Server**:
    ```bash
    uvicorn app.main:app --reload
    ```

## 🧪 Verification & Testing (New)

A comprehensive verification suite has been added to `tests/` to validate the entire workflow without relying on manual checks.

### Running the Live Validation Suite
To verify the system end-to-end (Auth -> Upload -> STT -> Database):
```bash
# This uses a temporary in-memory database and live STT calls
pytest tests/test_live_chain.py
```

### Available Tests
*   `tests/test_live_chain.py`: Full End-to-End Smoke Test & Resilience Test.
*   `tests/test_live_stt.py`: Targeted unit test for AssemblyAI accuracy and configuration.
*   `tests/verify_flow.py`: Mocked validation script for logic testing.
*   `tests/verify_resilience.py`: Verifies Retry logic and Manual Review queue.

### Offline Testing (Quota-Free)
To test Dashboard logic without consuming API credits:
```bash
python demo_offline.py
```
This runs a simulation using pre-generated SOAP notes.

## 🏗️ Architecture Summary

*   **API Framework**: FastAPI (Asynchronous, High Performance)
*   **ORM**: SQLModel (Pydantic + SQLAlchemy)
*   **Database**: PostgreSQL
*   **Security**: JWT (OAuth2) with Role-Based Access Control
*   **AI Layer**: 
    *   **STT**: Official AssemblyAI Python SDK (with Word Boost)
    *   **LLM**: Google Generative AI (Gemini 2.0 Flash) SDK (Active)
*   **Gateway**: Nginx (Reverse Proxy, Static File Serving)

## 🩺 Phase 2: Triage, Safety & Resilience

### 1. Smart Triage Algorithm
*   **Logic**: Analyzes SOAP notes for "Risk Flags" (e.g., Suicide, Chest Pain).
*   **Scoring**:
    *   **CRITICAL (90+)**: Immediate threats (Suicide, Stroke).
    *   **HIGH (70-89)**: Severe symptoms (High Fever, Severe Pain).
    *   **MODERATE (40-69)**: Acute but stable (Infection, Burn).
    *   **LOW (0-39)**: Routine checkups.

### 2. Drug Safety Net
*   **Mechanism**: Cross-references Prescriptions (Plan) vs. Patient History.
*   **Example**: Prescribing *Aspirin* to a patient with *Ulcers* triggers a `WARNING`.

### 3. Resilience & Fail-Safe
*   **Zero-Loss Guarantee**: If AI processing fails (e.g., API Quota Exceeded), patients are **not lost**.
*   **Retry Logic**: Exponential Backoff (up to 60s) handles traffic bursts.
*   **Manual Review**: Persistent failures land in a dedicated "Requires Review" queue.

## Verification & Accuracy 📊
This project includes a robust suite for validating AI performance.

### 1. Batch Verification (`batch_verify.py`)
Processes a folder of audio files to ensure end-to-end stability.
```bash
python batch_verify.py
```

### 2. Accuracy Calibration (`calculate_accuracy.py`)
Compares generated transcripts against Ground Truth (`.TextGrid`) to compute **Word Error Rate (WER)**.
*   **Current Performance**: ~15.8% WER (Above Average for conversational medical audio).
*   **Metric**: Weighted WER (ignoring punctuation/case).

### 3. SOAP Quality (`test_soap_generation.py`)
Verifies that the LLM generates valid JSON SOAP notes with **Strict Grounding** (no hallucinations).

## Security & Compliance 🛡️
*   **API Key Safety**: `.env` is gitignored.
*   **History Scrubbing**: This repository's history has been scrubbed using `git-filter-repo` to remove historical API key leaks.
*   **PII Redaction**: Enabled by default in `stt_service.py` (via AssemblyAI).

## Supported File Formats
The system utilizes AssemblyAI for transcription and supports the following audio/video formats:
*   **Audio**: `.mp3`, `.wav`, `.aac`, `.m4a`, `.ogg`, `.flac`, `.alac`, `.wma`, `.aiff`, `.au`
*   **Video**: `.mp4`, `.m4v`, `.mov`, `.wmv`

*Note: Project files (e.g., `.flp`, `.logicx`) or MIDI files are NOT supported.*

## ⚠️ Known Limits & Future Scaling
While robust for pilot usage, the current architecture has known limits to be addressed in the Enterprise Phase:

| Limit Category | Risk Description | Planned Mitigation |
| :--- | :--- | :--- |
| **Server Restarts** | In-memory tasks (`BackgroundTasks`) die if the server crashes/restarts. | Migrate to **Celery + Redis** for durable job queues. |
| **Local Storage** | Audio saved to disk (`/uploads`) limits horizontal scaling. | Migrate to **AWS S3 / GCS** for cloud storage. |
| **Concurrency** | Heavy load (1000+ users) may exhaust DB connections. | Implement **PgBouncer** connection pooling. |

## 📡 Key Endpoints

### Auth
*   `POST /api/v1/auth/signup`: **User Registration** (Creates User & Patient/Doctor Profile)
*   `POST /api/v1/auth/login`: **Authentication** (Returns JWT Bearer Token)
*   `GET /api/v1/auth/me`: **Context** (Retrieves current authenticated user details)

### Clinical Sessions & AI Integration
*   `POST /api/v1/consultations/{id}/upload`: **Audio Ingestion**
    *   *Internal Function*: Securely stores file and creates `AudioFile` record.
    *   *External Service*: Triggers **AssemblyAI Upload** & **Transcription** (`v2/transcript`).
    *   *AI Features Used*: Speaker Diarization, PII Redaction, Medical Word Boost.
*   `GET /api/v1/consultations/{id}`: **Status Polling**
    *   *Function*: Returns current state (`IN_PROGRESS`, `COMPLETED`).
    *   *Result*: Delivers the final transcript and confidence scores once AI processing is finished.

### Dashboard & Operations
*   `GET /api/v1/dashboard/queue`: **Smart Queue**
    *   Returns list of completed patients sorted by **Urgency** (Critical first).
*   `GET /api/v1/dashboard/queue/failed`: **Review Queue**
    *   Returns patients where AI failed (Quota/Error) and require manual triage.
