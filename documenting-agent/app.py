"""
main.py
-------
Point d'entrée FastAPI.

Démarrage :
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Endpoints :
    GET  /              → health check
    GET  /health        → statut Groq + API
    ---
    REST /projects      → CRUD projets
    REST /documents     → upload + indexation direct PostgreSQL
    WS   /chat/{project_id} → streaming WebSocket Stateless en RAM
    ---
    GET  /docs          → Swagger UI
    GET  /redoc         → ReDoc UI
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import des modèles et utilitaires
from models.schemas import HealthResponse
from utils.llm_factory import test_groq_connection

# Import des Routers
from routers.chat import router as chat_router
from routers.documents import router as documents_router
from routers.projects import router as projects_router
from routers.ai import router as ai_router

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s : %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Démarrage du Backend Multi-Agent RAG (Mode Stateless RAM)...")
    ok, msg = test_groq_connection()
    if ok:
        logger.info(msg)
    else:
        logger.warning(f"⚠️  {msg}")
    yield
    logger.info("🛑 Arrêt de l'API Multi-Agent.")


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Multi-Agent RAG API",
    description="Backend FastAPI éphémère (RAM) branché directement sur le stockage PostgreSQL.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS — Autorise Angular sur localhost:4200 et Spring Boot ──────────────────
load_dotenv()

origins = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(projects_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(ai_router)  # Le préfixe /api/ai est géré en interne dans ai.py
app.include_router(chat_router) # WebSocket ou Route Chat (sans préfixe /api)


# ── Routes système ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Système"])
async def root():
    return {"message": "Multi-Agent RAG API - Connecteur PostgreSQL Actif", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Système"])
async def health():
    """Vérifie l'état de l'API et la connexion Groq."""
    ok, _ = test_groq_connection()
    return HealthResponse(status="ok", groq=ok)