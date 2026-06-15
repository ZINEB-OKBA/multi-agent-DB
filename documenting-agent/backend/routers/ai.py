import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from utils.orchestrator import rebuild_resources_from_postgres

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI Core"])

# ── Schémas de communication avec Spring Boot ─────────────────────────────────

class IndexRequest(BaseModel) :
    projectId: int
    documentId: int  # Optionnel si vous voulez logguer l'ID

class IndexResponse(BaseModel) :
    status: str
    projectId: int
    chunks_count: int
    message: str

# ── Endpoint Synchrone : Bloque jusqu'à ce que le RAG soit prêt ───────────────

@router.post("/index", response_model=IndexResponse, status_code=status.HTTP_200_OK)
async def index_project_documents(req: IndexRequest):
    """
    Reçoit l'ordre d'indexation de Spring Boot.
    Télécharge, décode et génère l'index FAISS en RAM immédiatement.
    Ne répond que lorsque le système est prêt à répondre aux questions.
    """
    logger.info(f"🔄 Indexation synchrone demandée pour le projet ID: {req.projectId}")
    
    try:
        # On force la reconstruction et la vectorisation en RAM immédiatement
        vectorstore, dataframes = rebuild_resources_from_postgres(req.projectId)
        
        # Calcul du nombre de chunks pour le rapport de succès
        chunks_count = 0
        if vectorstore:
            # Récupère le nombre total de vecteurs stockés dans l'index FAISS éphémère
            chunks_count = vectorstore.index.ntotal
            
        logger.info(f"✅ Projet {req.projectId} prêt pour le Chat ({chunks_count} chunks en RAM).")
        
        return IndexResponse(
            status="SUCCESS",
            projectId=req.projectId,
            chunks_count=chunks_count,
            message="L'indexation est terminée. Le modèle est prêt à répondre."
        )
        
    except Exception as e:
        logger.error(f"❌ Échec de l'indexation immédiate pour le projet {req.projectId} : {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la préparation des ressources IA : {str(e)}"
        )