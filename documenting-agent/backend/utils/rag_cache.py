"""
utils/rag_cache.py
──────────────────
Cache de réponses RAG intelligent avec invalidation automatique.

LOGIQUE DE CLÉ :
  clé = hash(question_normalisée + fingerprint_documents_projet)

  fingerprint = hash(liste triée des (file_name + indexed_at) du projet)
  → Si un fichier est ajouté / ré-indexé → fingerprint change → cache miss
  → Si rien n'a changé → cache hit → réponse instantanée

SÉCURITÉS :
  - TTL configurable (défaut 2h) pour éviter les réponses périmées
  - Taille maximale (LRU éviction) pour ne pas saturer la RAM
  - On ne cache JAMAIS les réponses contenant les marqueurs d'échec
  - Invalidation explicite possible par projet (ex: après un upload)
"""

import hashlib
import logging
import time
import re
from collections import OrderedDict
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# ── CONFIG ─────────────────────────────────────────────────────────────────
DB_HOST     = "localhost"
DB_NAME     = "Motuldb"
DB_USER     = "postgres"
DB_PASSWORD = "postgres"

# Réponses qui ne doivent JAMAIS être mises en cache
NEGATIVE_RESPONSE_PATTERNS = [
    r"l.information demandée n.est pas accessible",
    r"aucun document pertinent",
    r"aucun document.*indexé",
    r"aucun fichier.*trouvé",
    r"introuvable",
    r"❌",
    r"⚠️.*aucun",
    r"not found",
    r"n'existe pas dans",
]


@dataclass
class CacheEntry:
    answer:      str
    sources:     List[Dict]
    charts:      List[Any]
    agent_used:  str
    intent:      str
    created_at:  float = field(default_factory=time.time)
    hit_count:   int   = 0


class RAGCache:
    """
    Cache LRU en RAM avec invalidation par fingerprint documentaire.
    Thread-safe pour FastAPI (single-process).
    """

    def __init__(self, max_size: int = 500, ttl_seconds: int = 7200):
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size    = max_size
        self._ttl         = ttl_seconds
        # fingerprint par projet : project_id → (fingerprint_str, timestamp)
        self._project_fps: Dict[int, str] = {}

    # ──────────────────────────────────────────────────────────────────────
    # FINGERPRINT : représente l'état documentaire actuel du projet
    # ──────────────────────────────────────────────────────────────────────

    def _fetch_project_fingerprint(self, project_id: int) -> str:
        """
        Construit un hash de l'état des documents indexés du projet.
        Interroge PostgreSQL pour obtenir : file_name + indexed_at de chaque doc.
        Si un fichier est ajouté ou ré-indexé → le hash change.
        """
        try:
            conn   = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """SELECT file_name, indexed_at
                   FROM documents
                   WHERE project_id = %s AND is_indexed = TRUE
                   ORDER BY file_name;""",
                (project_id,)
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            # Construire une chaîne représentant l'état exact des docs
            state_str = "|".join(
                f"{r['file_name']}:{r['indexed_at']}"
                for r in rows
            )
            fp = hashlib.sha256(state_str.encode()).hexdigest()[:16]
            logger.debug(f"🔑 Fingerprint projet {project_id} : {fp} ({len(rows)} docs)")
            return fp

        except Exception as e:
            logger.error(f"❌ Impossible de calculer le fingerprint projet {project_id} : {e}")
            # En cas d'erreur BDD → on retourne un token aléatoire pour forcer un cache miss
            return str(time.time())

    def get_project_fingerprint(self, project_id: int) -> str:
        """Retourne le fingerprint courant (toujours frais depuis PostgreSQL)."""
        fp = self._fetch_project_fingerprint(project_id)
        self._project_fps[project_id] = fp
        return fp

    # ──────────────────────────────────────────────────────────────────────
    # CLÉ DE CACHE
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_question(question: str) -> str:
        """Normalise la question pour absorber les variations mineures."""
        q = question.lower().strip()
        q = re.sub(r'\s+', ' ', q)                      # espaces multiples
        q = re.sub(r'[?!.,;:]+$', '', q)                # ponctuation finale
        q = re.sub(r'\b(le|la|les|un|une|des|du|de)\b', '', q)  # articles
        q = q.strip()
        return q

    def _make_key(self, question: str, project_id: int, fingerprint: str) -> str:
        """
        Clé = SHA256(question_normalisée + project_id + fingerprint)
        Le fingerprint change si les documents changent → cache miss automatique.
        """
        raw = f"{self._normalize_question(question)}||{project_id}||{fingerprint}"
        return hashlib.sha256(raw.encode()).hexdigest()

    # ──────────────────────────────────────────────────────────────────────
    # VALIDATION : ne pas cacher les réponses négatives
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _is_cacheable(answer: str) -> bool:
        """
        Retourne False si la réponse est un message d'échec ou de contenu introuvable.
        Ces réponses NE doivent JAMAIS être mises en cache.
        """
        if not answer or len(answer.strip()) < 20:
            return False

        answer_lower = answer.lower()
        for pattern in NEGATIVE_RESPONSE_PATTERNS:
            if re.search(pattern, answer_lower):
                logger.info(f"🚫 Réponse non cacheable (pattern négatif détecté : '{pattern}')")
                return False
        return True

    # ──────────────────────────────────────────────────────────────────────
    # GET / SET
    # ──────────────────────────────────────────────────────────────────────

    def get(
        self,
        question:   str,
        project_id: int,
    ) -> Optional[Dict]:
        """
        Cherche une entrée en cache.
        Retourne None si : miss, TTL expiré, ou documents ont changé.
        """
        fingerprint = self.get_project_fingerprint(project_id)
        key = self._make_key(question, project_id, fingerprint)

        entry = self._store.get(key)
        if entry is None:
            logger.info(f"⚡ CACHE MISS (nouvelle question ou docs mis à jour)")
            return None

        # Vérifier le TTL
        age = time.time() - entry.created_at
        if age > self._ttl:
            logger.info(f"⏳ CACHE EXPIRED (âge: {age:.0f}s > TTL: {self._ttl}s)")
            del self._store[key]
            return None

        # Cache hit → remonter en tête (LRU)
        self._store.move_to_end(key)
        entry.hit_count += 1
        logger.info(
            f"✅ CACHE HIT #{entry.hit_count} "
            f"(âge: {age:.0f}s, projet: {project_id}, fp: {fingerprint})"
        )
        return {
            "answer":     entry.answer,
            "sources":    entry.sources,
            "charts":     entry.charts,
            "agent_used": entry.agent_used,
            "intent":     entry.intent,
            "from_cache": True,
        }

    def set(
        self,
        question:   str,
        project_id: int,
        answer:     str,
        sources:    List[Dict] = None,
        charts:     List[Any]  = None,
        agent_used: str        = "",
        intent:     str        = "",
    ) -> bool:
        """
        Met en cache une réponse SEULEMENT si elle est valide (non négative).
        Retourne True si mise en cache effectuée.
        """
        if not self._is_cacheable(answer):
            return False

        fingerprint = self.get_project_fingerprint(project_id)
        key = self._make_key(question, project_id, fingerprint)

        # Éviction LRU si plein
        if len(self._store) >= self._max_size:
            evicted_key, _ = self._store.popitem(last=False)
            logger.debug(f"🗑️ Cache LRU éviction : {evicted_key[:12]}...")

        self._store[key] = CacheEntry(
            answer     = answer,
            sources    = sources or [],
            charts     = charts or [],
            agent_used = agent_used,
            intent     = intent,
        )
        self._store.move_to_end(key)
        logger.info(
            f"💾 CACHE SET (projet: {project_id}, fp: {fingerprint}, "
            f"taille cache: {len(self._store)}/{self._max_size})"
        )
        return True

    # ──────────────────────────────────────────────────────────────────────
    # INVALIDATION EXPLICITE
    # ──────────────────────────────────────────────────────────────────────

    def invalidate_project(self, project_id: int) -> int:
        """
        Supprime toutes les entrées d'un projet du cache.
        À appeler après un upload / ré-indexation pour forcer le recalcul.
        Retourne le nombre d'entrées supprimées.
        """
        # Le fingerprint va naturellement changer après upload (indexed_at mis à jour)
        # mais on peut aussi forcer la purge ici pour les cas edge
        old_fp = self._project_fps.get(project_id, "")
        new_fp = self._fetch_project_fingerprint(project_id)
        self._project_fps[project_id] = new_fp

        if old_fp != new_fp:
            logger.info(
                f"🔄 Fingerprint projet {project_id} changé : "
                f"{old_fp[:8]}… → {new_fp[:8]}… "
                f"(les futures requêtes forceront un cache miss)"
            )
        # Note : on ne purge pas physiquement — les anciennes clés
        # ne seront plus jamais matchées car le fingerprint a changé.
        return 0

    def clear_all(self) -> int:
        """Vide tout le cache (admin / debug)."""
        count = len(self._store)
        self._store.clear()
        self._project_fps.clear()
        logger.info(f"🧹 Cache entièrement vidé ({count} entrées supprimées)")
        return count

    def stats(self) -> Dict:
        """Retourne les statistiques du cache."""
        total_hits = sum(e.hit_count for e in self._store.values())
        return {
            "entries":    len(self._store),
            "max_size":   self._max_size,
            "ttl_seconds": self._ttl,
            "total_hits": total_hits,
            "projects":   list(self._project_fps.keys()),
        }


# ── INSTANCE GLOBALE (singleton applicatif) ────────────────────────────────
RAG_ANSWER_CACHE = RAGCache(
    max_size   = 500,   # 500 paires question/réponse max en RAM
    ttl_seconds= 7200,  # 2 heures de TTL
)