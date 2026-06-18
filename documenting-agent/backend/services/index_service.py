"""
services/index_service.py
--------------------------
Gestion de l'extraction Stateless pour l'API et les tâches asynchrones.
Connexion directe avec le décodeur PostgreSQL en RAM.
"""

import logging
from typing import Dict, Optional
import pandas as pd
from langchain_community.vectorstores import FAISS
from utils.orchestrator import rebuild_resources_from_postgres

logger = logging.getLogger(__name__)

class IndexService:
    """
    Service d'accès aux ressources documentaires.
    Suppression totale des accès disques locaux au profit du chargement dynamique.
    """
    def __init__(self, data_dir: str = "data"):
        # Conservé uniquement pour éviter les erreurs d'initialisation ailleurs
        pass

    def get_stateless_resources(self, project_id: int):
        """
        Récupère l'index FAISS et les DataFrames d'un projet 
        directement reconstruits depuis PostgreSQL en RAM.
        """
        return rebuild_resources_from_postgres(project_id)

    def get_vectorstore(self, project_str: str) -> Optional[FAISS]:
        """FallBack rétrocompatible pour les anciens services."""
        try:
            project_id = int(''.join(filter(str.isdigit, project_str)))
            vectorstore, _, _ = rebuild_resources_from_postgres(project_id)
            return vectorstore
        except Exception:
            return None

    def get_dataframes(self, project_str: str) -> Dict[str, pd.DataFrame]:
        """FallBack rétrocompatible pour l'agent Excel."""
        try:
            project_id = int(''.join(filter(str.isdigit, project_str)))
            _, dataframes, _ = rebuild_resources_from_postgres(project_id)
            return dataframes
        except Exception:
            return {}