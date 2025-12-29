from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, appointments, consultations, dashboard
from app.core.config import settings
from app.core.db import init_db

app = FastAPI(
    title="NeuroAssist v3 API (Python)",
    description="Refactored Clinical Backend with FastAPI, SQLModel, AssemblyAI, and Gemini",
    version="2.0.0"
)

# Set all CORS enabled origins
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(appointments.router, prefix="/api/v1/appointments", tags=["Appointments"])
app.include_router(consultations.router, prefix="/api/v1/consultations", tags=["Consultations"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/api/v1/health")
def health_check():
    from app.core.db import test_connection
    try:
        test_connection()
        return {"status": "healthy", "service": "NeuroAssist v3 Python Backend", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "service": "NeuroAssist v3 Python Backend", "database": f"disconnected: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
