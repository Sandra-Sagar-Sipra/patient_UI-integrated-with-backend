# 🐍 NeuroAssist v3 - Python Backend (FastAPI)

This is the refactored clinical backend migrated from Node.js to Python FastAPI, designed for secure, asynchronous processing of medical consultations. It integrates **active** Speech-to-Text (AssemblyAI) and supports LLM integration (Gemini - currently configured as disabled).

## 🌟 Key Features (Current State)

*   **Speech-to-Text (STT)**:
    *   **Engine**: AssemblyAI Python SDK (Asynchronous Polling).
    *   **Word Boost**: Optimized for neurological terminology (e.g., "Levetiracetam", "Donepezil") using custom vocabulary configurations.
    *   **Privacy**: Implementation includes PII Redaction and Speaker Diarization.
*   **LLM Layout**: Architecture for Gemini 1.5 Flash integration is present but temporarily toggle-disabled for focus on transcription accuracy (STT-Only Mode).
*   **Resilience**: Robust error handling for corrupt file uploads and network issues.
*   **Verification**: Comprehensive automated test suite for End-to-End validation.

## 🚀 Quick Start (Docker - Recommended)

1.  **Configure Environment**:
    Edit the `environment` section in `docker-compose.yml` with your API keys:
    *   `ASSEMBLYAI_API_KEY` (Required)
    *   `GOOGLE_API_KEY` (Required for future LLM enablement)

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
    *   Ensure `ASSEMBLYAI_API_KEY` is set.
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

## 🏗️ Architecture Summary

*   **API Framework**: FastAPI (Asynchronous, High Performance)
*   **ORM**: SQLModel (Pydantic + SQLAlchemy)
*   **Database**: PostgreSQL
*   **Security**: JWT (OAuth2) with Role-Based Access Control
*   **AI Layer**: 
    *   **STT**: Official AssemblyAI Python SDK (with Word Boost)
    *   **LLM**: Google Generative AI (Gemini) SDK (Codebase prepared, Functionality Paused)
*   **Gateway**: Nginx (Reverse Proxy, Static File Serving)

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
