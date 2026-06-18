import logging
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Modèles et utilitaires restants
from models.schemas import HealthResponse
from utils.llm_factory import test_groq_connection

# Routers épurés (uniquement la gestion Stateless : Documents & Chat)
from routers.chat import router as chat_router
from routers.documents import router as documents_router
from routers.staffing import router as staffing_router

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s : %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")


# ── Lifespan (Startup / Shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Démarrage du Microservice IA Stateless...")
    ok, msg = test_groq_connection()
    if ok:
        logger.info(msg)
    else:
        logger.warning(f"⚠️ {msg}")
    yield
    logger.info("🛑 Arrêt de l'API.")


# ── Configuration de l'Application FastAPI ─────────────────────────────────────
app = FastAPI(
    title="Stateless Multi-Agent RAG API",
    description="Moteur d'indexation RAM et orchestrateur de chat (Groq + FAISS éphémère + Pandas)",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Configuration CORS (Angular & Spring Boot) ─────────────────────────────────
load_dotenv()
origins = os.getenv("CORS_ORIGINS", "http://localhost:4200,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Inclusions des Routers Actifs ──────────────────────────────────────────────
# L'indexation synchrone répond maintenant sur : POST /api/documents/backoffice/receive-and-index
app.include_router(documents_router, prefix="/api")

# Le chat REST répond sur : POST /api/chat/message (et WebSocket sur /ws/chat)
app.include_router(chat_router, prefix="/api")

# Agent Staffing
app.include_router(staffing_router, prefix="/api")


# ── Routes Système de Base ─────────────────────────────────────────────────────
@app.get("/", tags=["Système"])
async def root():
    return {"message": "Stateless Multi-Agent RAG API fonctionnelle", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Système"])
async def health():
    """Vérifie l'état du microservice et la connectivité Groq cloud."""
    ok, _ = test_groq_connection()
    return HealthResponse(status="ok", groq=ok)