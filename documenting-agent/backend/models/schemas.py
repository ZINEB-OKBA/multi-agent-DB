"""
models/schemas.py
-----------------
Tous les modèles Pydantic v2 utilisés dans l'API.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════════════
# PROJETS
# ══════════════════════════════════════════════════════════════════════════════

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100,
                      pattern=r"^[a-zA-Z0-9_\-]+$",
                      description="Nom du projet (sans espaces)")
    description: Optional[str] = Field(None, max_length=500)


class ProjectMeta(BaseModel):
    name:         str
    description:  Optional[str]    = None
    created_at:   str
    pdf_files:    list[str]         = []
    table_files:  list[str]         = []
    chunks:       int               = 0
    has_faiss:    bool              = False
    table_count:  int               = 0


class ProjectList(BaseModel):
    projects: list[ProjectMeta]
    total:    int


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════

class UploadResponse(BaseModel):
    project:       str
    file_name:     str
    file_type:     Literal["pdf", "excel"]
    size_bytes:    int
    message:       str


class IndexResponse(BaseModel):
    project:   str
    chunks:    int
    files:     list[str]
    message:   str


class DocumentList(BaseModel):
    project:     str
    pdf_files:   list[str]
    table_files: list[str]


# ══════════════════════════════════════════════════════════════════════════════
# CHAT
# ══════════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    project:     str  = Field(..., description="Nom du projet actif")
    question:    str  = Field(..., min_length=1, max_length=2000)
    force_agent: Optional[Literal["pdf", "excel"]] = None


class ChatMessage(BaseModel):
    """Message individuel dans l'historique."""
    role:       Literal["user", "assistant"]
    content:    str
    agent_used: Optional[str]  = None
    intent:     Optional[str]  = None
    timestamp:  str            = Field(default_factory=lambda: datetime.now().isoformat())


class ChatHistory(BaseModel):
    project:  str
    messages: list[ChatMessage] = []


# ══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET — événements streamés au client Angular
# ══════════════════════════════════════════════════════════════════════════════

class WSEvent(BaseModel):
    """Événement générique envoyé via WebSocket."""
    type:    str
    payload: Any = None


class WSTokenEvent(BaseModel):
    """Token streamé par le LLM."""
    type:  Literal["token"]   = "token"
    token: str


class WSIntentEvent(BaseModel):
    """Classification d'intention détectée."""
    type:   Literal["intent"] = "intent"
    intent: str               # "pdf" ou "excel"
    agent:  str


class WSDoneEvent(BaseModel):
    """Signal de fin de génération."""
    type:       Literal["done"]  = "done"
    full_text:  str
    agent_used: str
    intent:     str


class WSErrorEvent(BaseModel):
    """Erreur survenue pendant le traitement."""
    type:    Literal["error"] = "error"
    message: str


# ══════════════════════════════════════════════════════════════════════════════
# SYSTÈME
# ══════════════════════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    status:    str
    groq:      bool
    version:   str = "1.0.0"


class ErrorResponse(BaseModel):
    detail: str