import os
import logging
import base64
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import psycopg2

# Importation directe de l'orchestrateur stateless configuré avec le cache RAM
from utils.orchestrator import rebuild_resources_from_postgres

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents (Stateless IA)"])

# ⚙️ Configuration de la Base de Données PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "Motuldb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


# ══════════════════════════════════════════════════════════════════════════════
# SCHÉMAS DE DONNÉES INTEROPÉRABLES
# ══════════════════════════════════════════════════════════════════════════════

class SpringBootUploadPayload(BaseModel):
    """Structure du JSON envoyé par le FileIndexerExecutor de Spring Boot."""
    documentId: int
    fileName: str
    content: str  # Chaîne Base64 complète (avec ou sans header Data URL)
    projectId: int


class IndexSyncResponse(BaseModel):
    """Réponse unifiée confirmant la préparation totale du contexte IA."""
    status: str
    projectId: int
    documentId: int
    fileName: str
    fileType: str
    chunks_count: int
    message: str


# ══════════════════════════════════════════════════════════════════════════════
# SYNCHRONISATION POSTGRESQL DIRECTE
# ══════════════════════════════════════════════════════════════════════════════

def _update_postgres_status(doc_id: int, is_indexed: bool, indexing: bool, error_msg: Optional[str] = None):
    """Met à jour physiquement l'état du document dans PostgreSQL."""
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        conn.autocommit = True
        cursor = conn.cursor()
        
        query = """
            UPDATE documents 
            SET is_indexed = %s, indexing = %s, index_error = %s, indexed_at = %s 
            WHERE id = %s;
        """
        indexed_at = datetime.now() if is_indexed else None
        cursor.execute(query, (is_indexed, indexing, error_msg, indexed_at, doc_id))
        cursor.close()
        conn.close()
        logger.info(f"💾 [PostgreSQL] ID {doc_id} synchronisé (is_indexed={is_indexed}, indexing={indexing})")
    except Exception as db_err:
        logger.error(f"❌ Erreur critique lors de l'écriture directe PostgreSQL : {db_err}")


# ══════════════════════════════════════════════════════════════════════════════
# ENPOINT UNIQUE D'INGESTION ET D'INDEXATION SYNCHRONE
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/backoffice/receive-and-index", response_model=IndexSyncResponse, status_code=status.HTTP_200_OK)
async def receive_and_index_synchronous(payload: SpringBootUploadPayload):
    """
    Endpoint synchrone appelé par Spring Boot.
    1. Intercepte le flux Base64 et met à jour l'état BDD à 'indexing=True'.
    2. Déclenche immédiatement la reconstruction des ressources en RAM (FAISS/Pandas).
    3. Bloque la réponse tant que l'IA n'est pas prête à 100% à répondre au Front.
    """
    filename = payload.fileName
    project_id = payload.projectId
    doc_id = payload.documentId
    
    logger.info(f"⚡ [Signal Reçu] Traitement synchrone IA demandé pour le fichier : {filename} (Projet ID: {project_id})")
    
    # Détermination du type de fichier via son extension
    if filename.lower().endswith(('.pdf', '.docx', '.doc')):
        file_type = "pdf"
    elif filename.lower().endswith(('.csv', '.xlsx', '.xls', '.xlsm')):
        file_type = "excel"
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Extension du fichier '{filename}' rejetée par l'orchestrateur."
        )

    # Étape 1 : Passage immédiat à l'état d'indexation en cours dans votre PostgreSQL
    _update_postgres_status(doc_id=doc_id, is_indexed=False, indexing=True)

    try:
        # Étape 2 : Appel synchrone de l'orchestrateur
        # Cette fonction va lire PostgreSQL, décoder les fichiers en RAM, calculer les embeddings via Ollama,
        # puis monter et stocker les structures de données chaudes dans le RAM_PROJECTS_CACHE global.
        vectorstore, dataframes, _ = rebuild_resources_from_postgres(project_id)
        
        # Étape 3 : Évaluation du volume indexé
        chunks_count = 0
        if file_type == "pdf" and vectorstore:
            chunks_count = vectorstore.index.ntotal
        elif file_type == "excel" and dataframes:
            # Pour un tableau Pandas, le nombre de structures montées fait foi
            chunks_count = len(dataframes)

        # Étape 4 : Enregistrement du succès définitif en base de données
        _update_postgres_status(doc_id=doc_id, is_indexed=True, indexing=False, error_msg=None)
        
        logger.info(f"✅ Document ID {doc_id} traité avec succès. Prêt pour le chat.")

        return IndexSyncResponse(
            status="READY",
            projectId=project_id,
            documentId=doc_id,
            fileName=filename,
            fileType=file_type,
            chunks_count=chunks_count,
            message=f"Le document '{filename}' a été injecté avec succès en RAM. Le pipeline RAG est actif."
        )

    except Exception as e:
        # Gestion des pannes : Nettoyage immédiat de l'état en BDD et notification d'erreur
        error_msg = str(e)
        logger.error(f"❌ Échec critique du traitement synchrone pour {filename} : {error_msg}", exc_info=True)
        
        _update_postgres_status(doc_id=doc_id, is_indexed=False, indexing=False, error_msg=error_msg)
        
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne de traitement IA (RAG/FAISS/Pandas RAM) : {error_msg}"
        )