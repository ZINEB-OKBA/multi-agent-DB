"""
utils/orchestrator.py
─────────────────────────────────────────────────────────────────────────────
Orchestrateur Multi-Agent connecté à PostgreSQL.
 Améliorations supplémentaires :
  ✅ Classificateur 2 passes : keywords → LLM avec contexte colonnes 
  ✅ hybrid_search FAISS + keyword boosting 
  ✅ Cache RAM avec validation par doc_ids
  ✅ Cache RAG réponses 
  ✅ MÉMOIRE par agent : PDF, Excel et Staffing ont chacun leur mémoire de session
  ✅ Retry 429 + from_cache flag 
  ✅ Diagnostic PDF scanné amélioré
  ✅ Mode Staffing global (sans project_id)
"""

import base64
import logging
import os
import re
import tempfile
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import pandas as pd
import psycopg2
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from psycopg2.extras import RealDictCursor

from utils.llm_factory import get_llm
from utils.loader_excel import load_dataframe, run_excel_agent, EXCEL_MEMORY

try:
    from utils.rag_cache import RAG_ANSWER_CACHE
    _HAS_RAG_CACHE = True
except ImportError:
    _HAS_RAG_CACHE = False
    logger_tmp = logging.getLogger(__name__)
    logger_tmp.warning("⚠️ utils.rag_cache introuvable — cache RAG désactivé.")

logger = logging.getLogger(__name__)

IntentType = Literal["pdf", "excel", "staffing", "general", "unknown"]
RAM_PROJECTS_CACHE: Dict[int, Dict] = {}

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_NAME     = os.getenv("DB_NAME", "Motuldb")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


# ══════════════════════════════════════════════════════════════════════════════
# MÉMOIRES PAR AGENT (par project_id)
# ══════════════════════════════════════════════════════════════════════════════

class AgentMemory:
    """
    Mémoire glissante générique — partagée entre PDF, Staffing et Général.
    Chaque agent a sa propre instance ; Excel utilise EXCEL_MEMORY (loader_excel.py).
    """
    _WINDOW   = 10
    _MAX_CHARS = 300

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._store: Dict[int, deque] = {}

    def _q(self, pid: int) -> deque:
        if pid not in self._store:
            self._store[pid] = deque(maxlen=self._WINDOW)
        return self._store[pid]

    def add(self, pid: int, question: str, answer: str):
        self._q(pid).append({
            "q": str(question)[:300],
            "a": str(answer)[:self._MAX_CHARS],
        })

    def get_context(self, pid: int) -> str:
        history = self._q(pid)
        if not history:
            return ""
        lines = [f"\n\n══════ MÉMOIRE {self.agent_name.upper()} ══════"]
        for i, t in enumerate(history, 1):
            lines.append(f"[{i}] Utilisateur : {t['q']}")
            lines.append(f"     Assistant  : {t['a']}")
        lines.append("══════════════════════════════════════════════\n")
        return "\n".join(lines)

    def get_turns(self, pid: int) -> list:
        """Retourne l'historique brut (liste de {'q':..., 'a':...}) pour ce projet."""
        return list(self._q(pid))

    def clear(self, pid: int):
        self._store.pop(pid, None)

PDF_MEMORY      = AgentMemory("PDF-RAG")
STAFFING_MEMORY = AgentMemory("Staffing")
GENERAL_MEMORY  = AgentMemory("Général")


# ══════════════════════════════════════════════════════════════════════════════
# LISTES DE MOTS-CLÉS (zineb — priorité sémantique)
# ══════════════════════════════════════════════════════════════════════════════

PDF_FORCE_KEYWORDS = [
    "décrire", "descrire", "décris", "description",
    "expliquer", "explication", "explique",
    "algorithme", "algo",
    "comment fonctionne", "comment est",
    "architecture", "contexte", "définition", "définir",
    "qu'est-ce que", "c'est quoi", "kesako",
    "procédure", "méthode", "méthodologie",
    "fonctionnement", "principe", "concept",
    "pourquoi", "objectif", "but", "utilité",
    "historique", "origine", "présentation",
    "sfd", "dossier", "documentation", "rapport",
    "qui est", "quel est le directeur", "quel est le responsable",
]

EXCEL_DATA_KEYWORDS = [
    "combien", "nombre", "total", "somme", "moyenne",
    "maximum", "minimum", "max", "min",
    "fréquence", "plus fréquent", "top", "classement",
    "heure de pointe", "peak", "taux",
    "liste des", "liste complète",
    "statistiques", "statistique",
    "calculer", "calcule", "calcul",
    "quel est le chiffre", "donnez-moi les chiffres",
    "analyse des données",
]

STAFFING_FORCE_KEYWORDS = [
    "tjm", "taux journalier", "jours travaillés", "jours travaillee",
    "rentabilité", "rentabilite", "profitabilité",
    "coût salarial", "cout salarial", "charge salariale",
    "occupation", "taux d'occupation",
    "gain", "perte", "bénéfice net",
    "freelancer", "prestataire",
    "employe", "employé", "employer", "collaborateur", "salaire", "staffing",
    "budget", "budget projet", "budget de projet", "chiffre d'affaires", "ca du projet",
    "jour travaillé", "jour travaille", "jours de travail",
    "graphique de", "graphe de", "génère un graphe", "genere un graphe",
    "affiche un graphique", "affiche le graphique", "montre le graphique",
    "montre un graphique", "graphique du", "graphe du",
    "gain net", "coût par", "cout par", "salaire de",
    "occupation de", "répartition des coûts", "repartition des couts",
    "pie chart", "radar de",
]

GREETING_KEYWORDS = ["bonjour", "salut", "hello", "hi", "bonsoir", "hey"]

GENERAL_KEYWORDS = [
    "contien", "contient", "document", "donnee", "donnée",
    "fichier", "qu'y a-t-il", "contenu", "present dans", "présent dans",
]


# ══════════════════════════════════════════════════════════════════════════════
# HELPER — résumé DataFrames pour le LLM classificateur
# ══════════════════════════════════════════════════════════════════════════════

def _summarize_dataframes(dataframes: Dict[str, pd.DataFrame]) -> str:
    if not dataframes:
        return "Aucun tableau Excel/CSV disponible pour ce projet."
    return "\n".join(
        f"  - Fichier '{name}' : {len(df)} lignes, colonnes : [{', '.join(df.columns.tolist()[:15])}]"
        for name, df in dataframes.items()
    )


# ══════════════════════════════════════════════════════════════════════════════
# CLASSIFICATEUR — passe 1 : keywords (zineb, priorité stricte)
# ══════════════════════════════════════════════════════════════════════════════

def _kw_in_question(kw: str, q: str, q_words: set) -> bool:
    """Vérifie la présence d'un mot-clé — mot entier si <= 4 chars."""
    if len(kw) <= 4:
        return kw in q_words
    return kw in q


def _classify_by_keywords(
    question: str,
    dataframes: Dict[str, pd.DataFrame],
    history: Optional[List[dict]] = None,  # <-- Intégré proprement ici
) -> Optional[IntentType]:
    q       = question.lower()
    q_words = set(re.findall(r'\b\w+\b', q))
    
    # ── NOUVEAU : Suivi contextuel staffing ──
    calc_keywords = ["comment", "calcul", "calcule", "calculer", "détail", "detail",
                     "explique", "explication", "pourquoi", "formule"]
    if history and any(ck in q for ck in calc_keywords):
        for h in reversed(history[-6:]):
            if h.get("role") == "user":
                last_q = h.get("content", "").lower()
                if any(kw in last_q for kw in STAFFING_FORCE_KEYWORDS):
                    logger.info("👥 Staffing (suivi contextuel forcé)")
                    return "staffing"
                break

    # ── Reste du code initial inchangé ──
    if any(_kw_in_question(kw, q, q_words) for kw in GREETING_KEYWORDS):
        logger.info("💬 Salutation → pdf")
        return "pdf"

    for kw in PDF_FORCE_KEYWORDS:
        if _kw_in_question(kw, q, q_words):
            logger.info(f"📚 PDF forcé : '{kw}'")
            return "pdf"

    for kw in STAFFING_FORCE_KEYWORDS:
        if _kw_in_question(kw, q, q_words):
            logger.info(f"👥 Staffing forcé : '{kw}'")
            return "staffing"

    has_data_kw = any(kw in q for kw in EXCEL_DATA_KEYWORDS)
    col_match   = None
    if dataframes:
        all_cols: set = set()
        for df in dataframes.values():
            for col in df.columns:
                all_cols.add(col.lower().replace("_", " "))
                all_cols.add(col.lower())
        for col in all_cols:
            if len(col) > 3 and col in q:
                col_match = col
                break

    if has_data_kw and (col_match or dataframes):
        logger.info(f"📊 Excel (data_kw=True, col_match={col_match})")
        return "excel"

    if col_match and not has_data_kw:
        logger.info(f"⚠️ Colonne '{col_match}' ambiguë → LLM")
        return None

    has_general = any(kw in q for kw in GENERAL_KEYWORDS)
    has_q_word  = any(kw in q for kw in ["quel", "qu'est", "liste", "quoi", "y a"])
    has_person  = any(kw in q for kw in
                      ["employe", "employé", "collaborateur", "nom", "salaire", "tjm"])
    if has_general and has_q_word and not has_person:
        logger.info("📁 Intent 'general'")
        return "general"

    return None

# ══════════════════════════════════════════════════════════════════════════════
# CLASSIFICATEUR — passe 2 : LLM avec contexte colonnes + historique (ahmed)
# ══════════════════════════════════════════════════════════════════════════════
INTENT_PROMPT_LLM = ChatPromptTemplate.from_template(
    """Tu es l'orchestrateur d'un système IA multi-agent.
Ta mission : router la question vers le bon agent.

════════════════════════════════════════
DONNÉES EXCEL/CSV DISPONIBLES :
{dataframes_summary}
════════════════════════════════════════

RÈGLES (ordre de priorité strict) :

1. **staffing** : PRIORITÉ ABSOLUE si la question demande :
   - Un graphique, graphe, chart, pie chart, radar, diagramme SUR des données RH
   - Les jours travaillés, salaires, occupation, gain net, coût d'un employé
   - Toute visualisation liée à : employé, collaborateur, salaire, TJM, projet RH
   → Exemples : "graphique de jour de khalil", "pie chart des coûts", 
     "radar des employés", "graphe du gain net", "occupation de zineb"

2. **pdf** : Question conceptuelle, explicative, historique ou administrative.
"décrire", "expliquer", "algorithme", "comment fonctionne", "qui est",
     "procédure", "architecture", "qu'est-ce que", "présentation", "documentation"   → JAMAIS pour des demandes de graphiques sur des données chiffrées.
→ MÊME SI la question mentionne un mot du tableau → si elle demande une EXPLICATION → **pdf**.


3. **excel** : Question sur des données quantitatives NON-RH.
   → "combien", "total", "moyenne", "fréquence" sur des données non-staffing.

{history_context}
Question : {question}
Réponds UNIQUEMENT par : `pdf`, `excel` ou `staffing`.
Réponse :"""
)


def classify_intent(
    question:   str,
    dataframes: Optional[Dict[str, pd.DataFrame]] = None,
    history:    Optional[List[dict]] = None,
) -> IntentType:
    logger.info(f"🧭 Classification : '{question[:80]}'")

    intent = _classify_by_keywords(question, dataframes or {},history=history)
    if intent is not None:
        logger.info(f"   → Intent (keywords) : {intent}")
        return intent

    logger.info("   → Appel LLM classificateur...")
    history_context = ""
    if history:
        history_context = "Historique des échanges récents :\n"
        for h in history[-8:]:
            role    = "Utilisateur" if h.get("role") == "user" else "Assistant"
            content = str(h.get("content", ""))[:200]
            history_context += f"- {role} : {content}\n"
        history_context += "\n"

    try:
        llm   = get_llm(temperature=0.0, max_tokens=10)
        chain = INTENT_PROMPT_LLM | llm | StrOutputParser()
        res   = chain.invoke({
            "question":           question,
            "dataframes_summary": _summarize_dataframes(dataframes or {}),
            "history_context":    history_context,
        }).strip().lower()

        if "staffing" in res:
            intent = "staffing"
        elif "excel" in res:
            intent = "excel"
        else:
            intent = "pdf"
    except Exception as e:
        logger.error(f"❌ LLM classificateur échoué → pdf : {e}")
        intent = "pdf"

    logger.info(f"   → Intent (LLM) : {intent}")
    return intent


# ══════════════════════════════════════════════════════════════════════════════
# CONNEXION POSTGRESQL
# ══════════════════════════════════════════════════════════════════════════════

def _pg_connect():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def _decode_base64_content(content: str) -> bytes:
    """Nettoie le préfixe data-URL et décode en bytes."""
    if ";base64," in content:
        content = re.sub(r"^data:.*?;base64,", "", content)
    elif "," in content:
        content = content.split(",")[1]
    content = content.strip().replace(" ", "").replace("\n", "")
    return base64.b64decode(content)


# ══════════════════════════════════════════════════════════════════════════════
# CACHE RAM + RECONSTRUCTION DEPUIS POSTGRESQL
# ══════════════════════════════════════════════════════════════════════════════

def rebuild_resources_from_postgres(project_id: int):
    logger.info(f"🔄 [BDD ➔ RAM] Projet {project_id}")

    conn   = _pg_connect()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT id, file_name, content FROM documents "
        "WHERE project_id = %s AND is_indexed = TRUE;",
        (project_id,),
    )
    db_docs = cursor.fetchall()
    cursor.close()
    conn.close()

    if not db_docs:
        logger.warning(f"⚠️ Aucun document indexé pour le projet {project_id}")
        RAM_PROJECTS_CACHE[project_id] = {
            "vectorstore": None, "dataframes": {}, "docs_raw": [],
            "doc_ids": set(), "updated_at": datetime.now(),
        }
        return None, {}, []

    all_chunks: List[Document]           = []
    dataframes: Dict[str, pd.DataFrame] = {}
    docs_raw:   List[Dict[str, Any]]    = []

    for doc in db_docs:
        file_name      = doc["file_name"]
        base64_content = doc["content"]
        suffix         = os.path.splitext(file_name)[1].lower()

        if not base64_content:
            continue

        try:
            file_bytes = _decode_base64_content(base64_content)
        except Exception as e:
            logger.error(f"❌ Décodage Base64 '{file_name}' : {e}")
            continue

        docs_raw.append({"file_name": file_name, "file_bytes": file_bytes, "suffix": suffix})

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            temp_filepath = tmp.name

        try:
            if suffix in (".pdf", ".docx", ".doc"):
                from utils.loader_pdf import load_uploaded_files_from_paths
                chunks = load_uploaded_files_from_paths([temp_filepath])
                if chunks:
                    for chunk in chunks:
                        chunk.metadata["source"] = file_name
                    all_chunks.extend(chunks)
                    logger.info(f"✅ Chunks PDF/Word : {file_name} ({len(chunks)} chunks)")
                else:
                    logger.warning(f"⚠️ Aucun contenu extrait de {file_name}")

            elif suffix in (".csv", ".xlsx", ".xls", ".xlsm"):
                dataframes[os.path.splitext(file_name)[0]] = load_dataframe(temp_filepath)
                logger.info(f"✅ DataFrame : {file_name}")

        except Exception as e:
            logger.error(f"❌ Traitement {file_name} : {e}")
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    vectorstore = None
    if all_chunks:
        logger.info(f"🔢 Vectorisation {len(all_chunks)} chunks...")
        embeddings  = FastEmbedEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        vectorstore = FAISS.from_documents(all_chunks, embeddings)
        logger.info("✅ Index FAISS créé en RAM.")

    RAM_PROJECTS_CACHE[project_id] = {
        "vectorstore": vectorstore,
        "dataframes":  dataframes,
        "docs_raw":    docs_raw,
        "doc_ids":     {doc.get("id") or doc.get("file_name", str(i)) for i, doc in enumerate(db_docs)},
        "updated_at":  datetime.now(),
    }
    return vectorstore, dataframes, docs_raw


def get_project_resources(project_id: int):
    """Cache RAM avec validation par doc_ids — recharge si BDD a changé."""
    try:
        conn   = _pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM documents WHERE project_id = %s AND is_indexed = TRUE;",
            (project_id,),
        )
        db_doc_ids = {row[0] for row in cursor.fetchall()}
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"❌ Vérification BDD cache : {e}")
        db_doc_ids = set()

    if project_id in RAM_PROJECTS_CACHE:
        if RAM_PROJECTS_CACHE[project_id].get("doc_ids", set()) == db_doc_ids:
            logger.info(f"⚡ [RAM HIT] Projet {project_id}")
            res = RAM_PROJECTS_CACHE[project_id]
            return res["vectorstore"], res["dataframes"], res.get("docs_raw", [])
        logger.info("🔄 [RAM INVALID] Documents BDD changés → rechargement")

    logger.info(f"📡 [RAM MISS] Init projet {project_id}")
    return rebuild_resources_from_postgres(project_id)


# ══════════════════════════════════════════════════════════════════════════════
# AGENT PDF — hybrid search + mémoire
# ══════════════════════════════════════════════════════════════════════════════

RAG_PROMPT = ChatPromptTemplate.from_template(
    """Tu es un assistant expert en extraction documentaire factuelle.

⚠️ RÈGLES STRICTES :
1. Si la question demande un NOM DE PERSONNE (directeur, responsable, fondateur...),
   cherche EXPLICITEMENT dans le contexte et cite-le EXACTEMENT.
2. Si l'information est présente dans le contexte, tu DOIS la fournir.
3. Si l'information est ABSENTE, réponds :
   "❌ L'information demandée n'est pas accessible dans les extraits actuels du document."
4. Ne fabrique jamais de nom ou d'information.
5. Si c'est une salutation, réponds amicalement sans extraire de données.

Présente tes réponses avec des titres Markdown, des listes aérées et des émojis contextuels.

{memory_section}

CONTEXTE DOCUMENTAIRE :
{context}

{history_section}

QUESTION : {question}

RÉPONSE :"""
)


def hybrid_search(vectorstore, question: str, k: int = 20) -> List[Document]:
    """Recherche sémantique + boosting keyword (zineb)."""
    semantic_docs = vectorstore.similarity_search(question, k=k)
    keywords = re.findall(r"\b[A-ZÀ-Ÿ][a-zà-ÿ]{2,}\b|\b[A-ZÀ-Ÿ]{2,}\b", question)
    role_kws = re.findall(
        r"\b(directeur|gérant|président|fondateur|PDG|DG|responsable|chef|directrice)\b",
        question, re.IGNORECASE,
    )
    keywords = list(set(keywords + role_kws))
    if not keywords:
        return semantic_docs
    pattern  = "|".join(re.escape(kw) for kw in keywords)
    boosted, others = [], []
    for doc in semantic_docs:
        (boosted if re.search(pattern, doc.page_content, re.IGNORECASE) else others).append(doc)
    logger.info(f"🔍 Hybrid search : {len(boosted)} boostés / {len(others)} autres")
    return boosted + others


def run_pdf_agent(
    question:   str,
    docs:       List[Document],
    history:    Optional[List[dict]] = None,
    project_id: int = 0,
) -> str:
    logger.info(f"📄 Agent PDF : {len(docs)} docs (projet {project_id})")

    context = "\n\n---\n\n".join(
        f"📄 Source : {d.metadata.get('source', 'Inconnu')}\n{d.page_content}"
        for d in docs
    )

    memory_section = PDF_MEMORY.get_context(project_id)

    history_section = ""
    if history:
        history_section = "\n\n══════ HISTORIQUE SESSION ══════\n"
        for h in history[-8:]:
            role    = "Utilisateur" if h.get("role") == "user" else "Assistant"
            content = str(h.get("content", ""))[:500]
            history_section += f"- {role} : {content}\n"

    llm   = get_llm(temperature=0.1, max_tokens=2048)
    chain = RAG_PROMPT | llm | StrOutputParser()
    answer = chain.invoke({
        "context":         context,
        "question":        question,
        "history_section": history_section,
        "memory_section":  memory_section,
    })
    logger.info(f"✅ Réponse PDF ({len(answer)} chars)")

    PDF_MEMORY.add(project_id, question, answer)
    return answer


# ══════════════════════════════════════════════════════════════════════════════
# STAFFING — fallback fichiers (legacy, conservé pour compat éventuelle)
# ══════════════════════════════════════════════════════════════════════════════

def get_staffing_docs_raw_from_postgres(project_id: int) -> List[Dict[str, Any]]:
    """
    Conservé pour compatibilité — N'EST PLUS APPELÉ depuis orchestrate().
    L'agent staffing lit désormais directement Postgres via NL-SQL
    (table imputation/collaborateurs/projects), sans fichiers Excel/CSV.
    """
    logger.info(f"📂 [Staffing legacy] Projet {project_id}")

    conn   = _pg_connect()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'staffing_documents'
        );
    """)
    has_staffing_table = cursor.fetchone()["exists"]

    if has_staffing_table:
        cursor.execute(
            "SELECT file_name, content, extension FROM staffing_documents "
            "WHERE project_id = %s ORDER BY uploaded_at DESC;",
            (project_id,),
        )
    else:
        cursor.execute(
        """SELECT file_name, content, NULL as extension FROM documents
           WHERE project_id = %s
           AND (file_name ILIKE '%%staffing%%'
                OR file_name ILIKE '%%freelancer%%'
                OR file_name ILIKE '%%infos%%'
                OR file_name ILIKE '%%employe%%'
                OR file_name ILIKE '%%work%%'
                OR file_name LIKE '%%.csv'
                OR file_name LIKE '%%.xlsx');""",
        (project_id,),
    )

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    docs_raw: List[Dict[str, Any]] = []
    for row in rows:
        file_name = row["file_name"]
        content   = row["content"] or ""
        ext       = row.get("extension")
        suffix    = ext or os.path.splitext(file_name)[1].lower()
        if not suffix.startswith("."):
            suffix = f".{suffix}"
        try:
            file_bytes = _decode_base64_content(content)
            docs_raw.append({"file_name": file_name, "file_bytes": file_bytes, "suffix": suffix})
        except Exception as e:
            logger.error(f"❌ Décodage '{file_name}': {e}")

    return docs_raw


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATEUR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def orchestrate(
    question:    str,
    project_id:  int,
    force_agent: Optional[str] = None,
    history:     Optional[List[dict]] = None,
    theme_mode:  Optional[str] = "light",
) -> Dict[str, Any]:
    """
    Point d'entrée unique de l'orchestrateur.
    Retourne un dict avec : agent_used, intent, answer, error, docs, charts,
                            sources, from_cache.

    project_id = 0 (ou None) déclenche le mode Staffing global :
      pas de chargement RAM, pas de vectorstore/dataframes, l'agent
      staffing interroge directement PostgreSQL via NL-SQL.
    """
    result: Dict[str, Any] = {
        "agent_used": None,
        "intent":     None,
        "answer":     "",
        "error":      None,
        "docs":       [],
        "charts":     [],
        "sources":    [],
        "from_cache": False,
    }

    # 1. Cache RAG ───────────────────────────────────────────────────────────
    if _HAS_RAG_CACHE:
        cached = RAG_ANSWER_CACHE.get(question=question, project_id=project_id)
        if cached:
            logger.info(f"⚡ Cache RAG hit (projet {project_id})")
            result.update(cached)
            result["from_cache"] = True
            return result

    try:
        # 2/3. Routage d'abord — on ne charge les ressources RAM que si nécessaire ──
        forced = (force_agent or "").strip().lower()
        is_staffing_global = (project_id is None or project_id == 0)

        if forced in ("pdf", "excel", "staffing"):
            intent = forced
            logger.info(f"🎯 Agent forcé : {intent}")
            vectorstore, dataframes, docs_raw = (
                (None, {}, []) if intent == "staffing" and is_staffing_global
                else get_project_resources(project_id)
            )
        else:
            if is_staffing_global:
                intent = "staffing"
                vectorstore, dataframes, docs_raw = None, {}, []
            else:
                vectorstore, dataframes, docs_raw = get_project_resources(project_id)
                intent = classify_intent(question, dataframes, history=history)

        result["intent"] = intent
        logger.info(f"🚦 Routage → Agent : {intent.upper()}")

        # ── 4a. Agent PDF ──────────────────────────────────────────────────────
        if intent == "pdf":
            if vectorstore is None:
                pdf_files_in_db = _get_pdf_files_in_db(project_id)

                if pdf_files_in_db:
                    result["agent_used"] = "Orchestrateur (Alerte RAG)"
                    result["answer"] = (
                        f"Le fichier **{', '.join(pdf_files_in_db)}** est présent "
                        "mais semble être **scanné (image)** ou sans texte sélectionnable.\n\n"
                        "⚠️ Importez un PDF avec texte sélectionnable ou un fichier Word (.docx)."
                    )
                    return result

                if dataframes:
                    llm = get_llm(temperature=0.7, max_tokens=1024)
                    prompt = ChatPromptTemplate.from_template(
                        "Le projet contient uniquement des fichiers Excel : {excel_files}.\n"
                        "Réponds à la question et indique les fichiers disponibles.\n"
                        "Question : {question}\nRéponse :"
                    )
                    result["agent_used"] = "LLM Général (pas de PDF)"
                    result["answer"] = (prompt | llm | StrOutputParser()).invoke(
                        {"excel_files": ", ".join(dataframes.keys()), "question": question}
                    )
                    return result

                result["error"] = "⚠️ Aucun document indexé pour ce projet. Chargez d'abord un document."
                return result

            result["agent_used"] = "Agent PDF (RAG FAISS + hybrid search)"
            docs = hybrid_search(vectorstore, question, k=20)
            result["docs"]   = docs
            result["answer"] = (
                run_pdf_agent(question, docs, history=history, project_id=project_id)
                if docs else "Aucun document pertinent trouvé dans l'index."
            )

        # ── 4b. Agent Excel ────────────────────────────────────────────────────
        elif intent == "excel":
            if not dataframes:
                result["error"] = "⚠️ Aucun fichier Excel/CSV indexé pour ce projet."
                return result

            result["agent_used"] = "Agent Excel (Pandas en RAM)"

            excel_res = run_excel_agent(
                question=question,
                dataframes=dataframes,
                history=history,
                theme_mode=theme_mode or "light",
                project_id=project_id,
                enable_charts=False,
            )

            result["answer"] = (
                excel_res.get("answer", "")
                if isinstance(excel_res, dict)
                else str(excel_res)
            )

            result["charts"] = (
                excel_res.get("charts", [])
                if isinstance(excel_res, dict)
                else []
            )

            result["docs"] = list(dataframes.keys())

        # ── 4c. Agent Staffing ─────────────────────────────────────────────────
       # ── 4c. Agent Staffing ─────────────────────────────────────────────────
        elif intent == "staffing":
            from agents.staffing_agent import run_staffing_agent

            # ✅ Mémoire staffing injectée via 'history' (format {role, content})
            # plutôt que concaténée dans 'question' — évite de polluer le NL-to-SQL
            # et les regex d'extraction (employé/année/projet) qui travaillent sur 'question'.
            staffing_turns = STAFFING_MEMORY.get_turns(project_id)
            memory_as_history = []
            for turn in staffing_turns:
                memory_as_history.append({"role": "user", "content": turn["q"]})
                memory_as_history.append({"role": "assistant", "content": turn["a"]})
            combined_history = memory_as_history + (history or [])

            staffing_result = run_staffing_agent(
                question=question,   # ← question propre, non polluée
                docs_raw=None,       # plus utilisé — l'agent lit Postgres via NL-SQL
                history=combined_history,
                theme_mode=theme_mode or "light",
            )

            if staffing_result.get("error"):
                result["error"]  = staffing_result["error"]
                result["answer"] = staffing_result["answer"]
            else:
                result["agent_used"] = "Agent Staffing (PostgreSQL NL-SQL)"
                result["answer"]     = staffing_result["answer"]
                result["charts"]     = staffing_result.get("charts", [])
                result["sources"]    = staffing_result.get("sources", [])
                STAFFING_MEMORY.add(project_id, question, result["answer"])

        # ── 4d. Intent général — métadonnées projet ────────────────────────────
        elif intent == "general":
            pdf_names, excel_names = [], []
            try:
                conn   = _pg_connect()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(
                    "SELECT file_name FROM documents "
                    "WHERE project_id = %s AND is_indexed = TRUE;",
                    (project_id,),
                )
                for doc in cursor.fetchall():
                    ext = os.path.splitext(doc["file_name"])[1].lower()
                    (pdf_names if ext in (".pdf", ".docx", ".doc")
                     else excel_names).append(doc["file_name"])
                cursor.close()
                conn.close()
            except Exception as e:
                logger.error(f"❌ Lecture BDD général : {e}")

            parts = ["Le projet contient les ressources suivantes :"]
            if pdf_names:
                parts.append(
                    "- **Documents PDF & Word** : "
                    + ", ".join(f"`{n}`" for n in pdf_names)
                )
            if excel_names:
                parts.append(
                    "- **Données Excel & CSV** : "
                    + ", ".join(f"`{n}`" for n in excel_names)
                )
            if not pdf_names and not excel_names:
                parts.append("- Aucun document indexé actuellement.")

            answer = "\n".join(parts)
            GENERAL_MEMORY.add(project_id, question, answer)
            result["agent_used"] = "Orchestrateur (Métadonnées)"
            result["answer"]     = answer

        else:
            result["error"] = "❌ Intention non reconnue."

        # 5. Mise en cache RAG ──────────────────────────────────────────────────
        if _HAS_RAG_CACHE and result["answer"] and not result.get("error"):
            RAG_ANSWER_CACHE.set(
                question=question, project_id=project_id,
                answer=result["answer"],
                sources=result.get("sources", []),
                charts=result.get("charts", []),
                agent_used=result.get("agent_used", ""),
                intent=intent,
            )

    except Exception as e:
        logger.error(f"❌ Erreur orchestrateur : {e}", exc_info=True)
        result["error"] = f"❌ Erreur interne : {str(e)}"

    return result


# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRE — lister les PDF indexés d'un projet
# ══════════════════════════════════════════════════════════════════════════════

def _get_pdf_files_in_db(project_id: int) -> List[str]:
    pdf_files: List[str] = []
    try:
        conn   = _pg_connect()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT file_name FROM documents WHERE project_id = %s AND is_indexed = TRUE;",
            (project_id,),
        )
        for doc in cursor.fetchall():
            if os.path.splitext(doc["file_name"])[1].lower() in (".pdf", ".docx", ".doc"):
                pdf_files.append(doc["file_name"])
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Erreur lecture BDD PDF : {e}")
    return pdf_files


# ══════════════════════════════════════════════════════════════════════════════
# API PUBLIQUE — gestion des mémoires depuis l'extérieur
# ══════════════════════════════════════════════════════════════════════════════

def clear_all_memories(project_id: int):
    """Efface la mémoire de tous les agents pour un projet donné."""
    PDF_MEMORY.clear(project_id)
    STAFFING_MEMORY.clear(project_id)
    GENERAL_MEMORY.clear(project_id)
    EXCEL_MEMORY.clear(project_id)
    logger.info(f"🧹 Mémoires effacées pour le projet {project_id}")


def get_memory_summary(project_id: int) -> Dict[str, int]:
    """Retourne le nombre d'échanges mémorisés par agent pour un projet."""
    return {
        "pdf":      len(PDF_MEMORY._q(project_id)),
        "excel":    len(EXCEL_MEMORY._key(project_id)),
        "staffing": len(STAFFING_MEMORY._q(project_id)),
        "general":  len(GENERAL_MEMORY._q(project_id)),
    }