# 🐍 NeuroAssist v3 - Python Backend (FastAPI)

This is the refactored clinical backend migrated from Node.js to Python FastAPI, matching the architectural blueprint with Nginx as the gateway and AI integration (AssemblyAI + Gemini).

## 🚀 Quick Start (Docker - Recommended)

1.  **Configure Environment**:
    Edit the `environment` section in `docker-compose.yml` with your API keys:
    *   `ASSEMBLYAI_API_KEY`
    *   `GEMINI_API_KEY`

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

3.  **Run the Server**:
    ```bash
    python -m app.main
    # OR
    uvicorn app.main:app --reload
    ```

## 🏗️ Architecture Summary

*   **API Framework**: FastAPI (Asynchronous, High Performance)
*   **ORM**: SQLModel (Pydantic + SQLAlchemy)
*   **Database**: PostgreSQL
*   **Security**: JWT (OAuth2) with Role-Based Access Control
*   **AI Layer**: 
    *   **STT**: Official AssemblyAI Python SDK
    *   **LLM**: Google Generative AI (Gemini) SDK
*   **Gateway**: Nginx (Reverse Proxy, Static File Serving)

## 📡 Key Endpoints

### Auth
*   `POST /api/v1/auth/signup`: Create user and profile
*   `POST /api/v1/auth/login`: Get JWT Bearer token

### Clinical Sessions
*   `POST /api/v1/consultations/{id}/process`: Upload audio -> Transcribe -> Generate SOAP Note
