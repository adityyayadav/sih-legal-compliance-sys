from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Legal Metrology AI Service")

# Expose the API under /api/v1 as defined in Phase 9
app.include_router(router, prefix="/api/v1")