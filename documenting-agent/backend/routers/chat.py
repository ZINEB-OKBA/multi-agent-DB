"""
routers/chat.py
----------------
Chat multi-agent 100 % Stateless.
Résolution dynamique des projets par Nom ou ID depuis PostgreSQL.
Extraction et décodage à la volée des Base64 depuis la RAM (Cache).
"""

import os
import json
import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional

from utils.orchestrator import orchestrate, get_project_resources

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])

# ⚙️ Configuration de la Base de Données PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "Motuldb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


# ══════════════════════════════════════════════════════════════════════════════
# SCHÉMAS DE REQUÊTES & RÉPONSES
# ══════════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    question:    str
    project:     str  # Reçoit le nom en clair du dropdown (ex: "Outils RH", "3iyadaty")
    force_agent: Optional[str] = None
    history:     Optional[List[dict]] = None
    theme_mode:  Optional[str] = "light"

class SourceReference(BaseModel):
    fileName:     str
    pages:        Optional[str] = None
    extractCount: int

class ChartReference(BaseModel):
    title:   str
    type:    str
    base64:  Optional[str] = None
    chartjs: Optional[dict] = None
    plotly:  Optional[dict] = None

class ChatResponse(BaseModel):
    project:    str
    question:   str
    answer:     str
    agent_used: str
    intent:     str
    sources:    List[SourceReference] = []  # Liste des sources citées dans la réponse
    charts:     List[ChartReference] = []
# ══════════════════════════════════════════════════════════════════════════════
# FONCTION POLYMOPHE DE RÉSOLUTION D'ID PAR LE NOM
# ══════════════════════════════════════════════════════════════════════════════

def _extract_project_id(project_str: str) -> int:
    """
    Résout l'ID d'un projet de manière ultra-souple.
    Gère les ID bruts, les noms partiels, la casse et les tirets.
    """
    if not project_str:
        raise HTTPException(status_code=400, detail="Le nom du projet ne peut pas être vide.")
        
    project_str = project_str.strip()
    
    # Cas 1 : C'est déjà un ID brut (ex: "2" ou 2)
    if project_str.isdigit():
        return int(project_str)
        
    # Cas 2 : Nettoyage et recherche adaptative en BDD
    try:
        # On remplace les tirets/underscores par des jokers SQL '%' pour ignorer les séparateurs
        search_pattern = f"%{project_str.replace('-', '%').replace('_', '%')}%"
        
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        
        # ILIKE + % permettent de trouver "outils-rh" même s'il y a un décalage en BDD
        query = "SELECT id FROM projects WHERE name ILIKE %s LIMIT 1;"
        cursor.execute(query, (search_pattern,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            logger.info(f"🎯 [Match BDD OK] '{project_str}' résolu en ID : {result[0]}")
            return result[0]
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la résolution flexible du projet '{project_str}' : {e}")

    # Cas 3 (Fallback ultime) : Si la BDD ne répond pas, on extrait le premier chiffre trouvé
    import re
    match = re.search(r'\d+', project_str)
    if match:
        return int(match.group())
        
    raise HTTPException(
        status_code=404, 
        detail=f"Le projet '{project_str}' est introuvable dans la base de données PostgreSQL."
    )
# ══════════════════════════════════════════════════════════════════════════════
# MODE REST POST (Appelé par ton Spring Boot ou Swagger)
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/chat/message", response_model=ChatResponse)
async def chat_rest(body: ChatRequest):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")

    project_id = _extract_project_id(body.project)

    try:
        from utils.orchestrator import get_project_resources
        from services.chat_service import _build_sources

        result = orchestrate(
            question=question,
            project_id=project_id,
            force_agent=body.force_agent,
            history=body.history,
            theme_mode=body.theme_mode,
        )

        if result.get("error"):
            return ChatResponse(
                project    = body.project,
                question   = question,
                answer     = result.get("answer") or result["error"],
                agent_used = result.get("agent_used") or "Orchestrateur (Alerte)",
                intent     = result.get("intent") or "error",
                sources    = [],
                charts     = [],
            )

        # ── Construire les sources si l'orchestrateur retourne les docs ────
        sources = []
        if result.get("docs"):                          # si orchestrate() expose les docs
            sources = _build_sources(result["docs"])

        return ChatResponse(
            project    = body.project,
            question   = question,
            answer     = result["answer"],
            agent_used = result["agent_used"],
            intent     = result["intent"],
            sources    = sources,
            charts     = [ChartReference(**c) for c in result.get("charts", [])],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur chat [{project_id}]: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
# ══════════════════════════════════════════════════════════════════════════════
# MODE WEBSOCKET (Streaming en RAM pour Angular)
# ══════════════════════════════════════════════════════════════════════════════

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("🔌 WS connecté (Mode Hybride Nom/ID PostgreSQL)")

    async def send(msg: str):
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_text(msg)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            project_str = data.get("project", "").strip()
            question = data.get("question", "").strip()

            if not question or not project_str:
                continue

            # Résolution dynamique du nom pour le flux WebSocket
            try:
                project_id = _extract_project_id(project_str)
            except HTTPException as e:
                # Alerte le front en cas de problème sans casser le tunnel WS
                await send(json.dumps({"type": "error", "message": e.detail}))
                continue
            
            # Récupération instantanée du VectorStore et des DataFrames depuis la RAM
            vectorstore, dataframes = get_project_resources(project_id)

            from services.chat_service import ChatService
            chat_svc = ChatService()
            
            await chat_svc.stream_response(
                question=question,
                project=project_str,
                vectorstore=vectorstore,
                dataframes=dataframes,
                send_fn=send,
                force_agent=data.get("force_agent"),
            )

    except WebSocketDisconnect:
        logger.info("🔌 WS déconnecté")