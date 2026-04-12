"""
SIEM M365 - FastAPI Application
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.config import settings
from app.api import auth, ingest, alerts, query, export, dashboard, lifecycle, soc
from app.api.ingest_clear import router as ingest_clear_router
from app.api.ingest_audit import router as ingest_audit_router
from app.database import init_db_on_startup, engine_hot
from app.middleware.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.models.signins import SignIn
    from app.models.risky_users import RiskyUser
    from app.models.incidents import Incident
    from app.models.truth_list import TruthListUser
    from app.models.ingestion_logs import IngestionLog
    from app.models.audit_logs_m365 import M365AuditLog
    from app.models.soc_analysis import SOCAnomaly, SOCMetric

    init_db_on_startup()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ingest.router)
app.include_router(alerts.router)
app.include_router(query.router)
app.include_router(export.router)
app.include_router(dashboard.router)
app.include_router(lifecycle.router)
app.include_router(soc.router)
app.include_router(ingest_clear_router)
app.include_router(ingest_audit_router)


from fastapi.responses import FileResponse, JSONResponse


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_INDEX = PROJECT_ROOT / "frontend" / "index.html"

app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "frontend")), name="static")

@app.get("/")
async def root():
    try:
        return FileResponse(str(FRONTEND_INDEX))
    except:
        return JSONResponse({"message": "SIEM M365 API", "version": "1.0.0"})


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)