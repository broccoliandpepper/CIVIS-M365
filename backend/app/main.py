"""
SIEM M365 - FastAPI Application
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from app.config import settings
from app.api import auth, ingest, alerts, query, export, dashboard, lifecycle, soc
from app.api.ingest_clear import router as ingest_clear_router
from app.api.ingest_audit import router as ingest_audit_router
from app.database import init_db_on_startup, engine_hot, engine_archive, engine_config
from app.middleware.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.models.signins import SignIn
    from app.models.risky_users import RiskyUser
    from app.models.incidents import Incident
    from app.models.truth_list import TruthListUser
    from app.models.ingestion_logs import IngestionLog
    from app.models.audit_logs_m365 import M365AuditLog
    from app.models.new_user_review import NewUserReview
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
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_INDEX = PROJECT_ROOT / "frontend" / "index.html"

app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "frontend")), name="static")

@app.get("/")
async def root():
    try:
        return FileResponse(str(FRONTEND_INDEX))
    except Exception as e:
        logger.warning(f"Failed to serve frontend index: {e}")
        return JSONResponse({"message": "SIEM M365 API", "version": "1.0.0"})




@app.get("/health")
async def health():
    """Health check endpoint that verifies all databases are accessible.
    
    Returns:
    - healthy: All databases responding (status 200)
    - degraded: One or more databases not responding (status 200 but degraded=true)
    - unhealthy: Critical database not responding (status 503)
    """
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "databases": {}
    }
    
    # Check each database with a short timeout
    db_checks = [
        ("hot", engine_hot, True),  # required
        ("archive", engine_archive, True),  # required
        ("config", engine_config, True),  # required
    ]
    
    all_healthy = True
    any_critical_down = False
    
    for db_name, engine, is_critical in db_checks:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                health_status["databases"][db_name] = {"status": "ok"}
        except Exception as e:
            logger.warning(f"Database {db_name} health check failed: {e}")
            health_status["databases"][db_name] = {"status": "error", "error": str(e)}
            all_healthy = False
            if is_critical:
                any_critical_down = True
    
    if any_critical_down:
        health_status["status"] = "unhealthy"
        return health_status, 503
    elif not all_healthy:
        health_status["status"] = "degraded"
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)