"""
routers/staffing.py
────────────────────────────────────────────────────────────────────
Endpoints dédiés à l'agent Staffing.

POST /api/staffing/chat
  → Reçoit question + project (nom ou ID) depuis Spring Boot
  → Résout le project_id via PostgreSQL si nécessaire
  → Lance orchestrate() en lui passant le mode "staffing"
  → Retourne answer + charts + sources
"""
import logging
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.orchestrator import orchestrate

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Staffing"])

# ⚙️ Paramètres d'accès PostgreSQL (alignés sur l'orchestrateur)
DB_HOST = "localhost"
DB_NAME = "Motuldb"
DB_USER = "postgres"
DB_PASSWORD = "postgres"


# ══════════════════════════════════════════════════════════════════
# DTO MODELS (PYDANTIC)
# ══════════════════════════════════════════════════════════════════

class StaffingChatRequest(BaseModel):
    question:    str
    project:     str                  # Nom du projet ou ID sous forme de chaîne
    force_agent: Optional[str] = "staffing"
    theme_mode:  Optional[str] = "light"


class SourceRef(BaseModel):
    fileName:     str
    pages:        Optional[str] = None
    extractCount: int


class ChartData(BaseModel):
    title:   str
    type:    str                      # "bar" | "line" | "pie"
    base64:  Optional[str] = None     # Image PNG encodée base64
    chartjs: Optional[dict] = None    # Données Chart.js pour Angular


class StaffingChatResponse(BaseModel):
    project:    str
    question:   str
    answer:     str
    agent_used: str
    intent:     str
    sources:    List[SourceRef] = []
    charts:     List[ChartData] = []


# ══════════════════════════════════════════════════════════════════
# UTILITAIRE DE RÉSOLUTION DE L'ID PROJET
# ══════════════════════════════════════════════════════════════════

def _resolve_project_id(project_str: str) -> int:
    """
    Tente de convertir directement en int si c'est un ID numérique.
    Sinon, interroge la base de données pour trouver l'ID correspondant au nom du projet.
    """
    project_str = project_str.strip()
    
    # Cas 1 : C'est déjà un ID purement numérique
    if project_str.isdigit():
        return int(project_str)
        
    # Cas 2 : C'est un nom de projet, on cherche en BDD
    logger.info(f"🔍 Résolution de l'ID pour le projet nommé : '{project_str}'")
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Ajustez le nom de la table ou de la colonne si nécessaire (ex: projects, project_name, etc.)
        cursor.execute("SELECT id FROM projects WHERE name = %s LIMIT 1;", (project_str,))
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            return int(row['id'])
            
    except Exception as db_err:
        logger.error(f"❌ Erreur lors de la requête de résolution de projet : {db_err}")
        # On ne bloque pas si la table 'projects' n'existe pas encore, on tente un fallback regex

    # Cas 3 : Fallback si le nom contient un chiffre (ex: "Projet 12")
    match = re.search(r'\d+', project_str)
    if match:
        return int(match.group())
        
    raise HTTPException(
        status_code=404, 
        detail=f"Impossible de trouver ou de résoudre l'identifiant du projet : '{project_str}'"
    )


# ══════════════════════════════════════════════════════════════════
# ENDPOINT PRINCIPAL
# ══════════════════════════════════════════════════════════════════

@router.post("/staffing/chat", response_model=StaffingChatResponse)
async def staffing_chat(body: StaffingChatRequest):
    """
    **Agent Staffing** — Analyse RH depuis fichiers base64 PostgreSQL.

    - Lit les fichiers staffing depuis `staffing_documents` (base64 → bytes RAM)
    - Extrait les données via OCR (PDF) ou Pandas (Excel/CSV)
    - Calcule TJM, coût mensuel, taux d'occupation, rentabilité
    - Génère des graphiques matplotlib (base64 PNG + Chart.js JSON)
    - Retourne la réponse narrative + graphiques + sources
    """
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")

    # 1. Résolution propre du project_id (retire l'ancien import défectueux)
    try:
        project_id = _resolve_project_id(body.project)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Structure de projet invalide : {e}")

    # 2. Exécution de la chaîne d'orchestration
    try:
        result = orchestrate(
            question    = question,
            project_id  = project_id,
            force_agent = "staffing",
            theme_mode  = body.theme_mode,
        )

        # Si l'orchestrateur ou l'agent a renvoyé un message d'erreur métier
        if result.get("error"):
            return StaffingChatResponse(
                project    = body.project,
                question   = question,
                answer     = result.get("answer") or result["error"],
                agent_used = result.get("agent_used") or "Agent Staffing (Alerte)",
                intent     = "staffing",
                sources    = [],
                charts     = [],
            )

        # 3. Formater et renvoyer le DTO complet attendu par Angular/Spring Boot
        return StaffingChatResponse(
            project    = body.project,
            question   = question,
            answer     = result.get("answer", ""),
            agent_used = result.get("agent_used", "Agent Staffing (OCR + Calculs + Graphiques)"),
            intent     = "staffing",
            sources    = [SourceRef(**s) for s in result.get("sources", [])],
            charts     = [ChartData(**c) for c in result.get("charts",  [])],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Erreur critique dans l'endpoint staffing_chat : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur interne de l'agent staffing : {str(e)}")