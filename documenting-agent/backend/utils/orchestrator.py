"""
utils/orchestrator.py
---------------------
Orchestrateur Multi-Agent 100% Stateless (RAM) connecté à PostgreSQL.

1. Extrait et décode à la volée les fichiers Base64 depuis PostgreSQL.
2. Génère un index FAISS ou des DataFrames Pandas directement en RAM.
3. Conserve les instances chaudes dans un cache global applicatif.
4. Classifie l'intention de la question via Llama-3.3-70B.
5. Route vers l'agent approprié (PDF RAG vs Excel Analyst).
"""

import logging
import os
import base64
import tempfile
import re  # ✅ Conservé pour le nettoyage Regex des Data URLs
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Literal, Optional, List, Any

import pandas as pd
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaEmbeddings

from utils.llm_factory import get_llm
from utils.loader_excel import load_dataframe, run_excel_agent

logger = logging.getLogger(__name__)
IntentType = Literal["pdf", "excel", "staffing", "general", "unknown"]

# ── REGISTRE GLOBAL EN RAM (CACHE DES PROJETS ACTIFS) ─────────────────────────
RAM_PROJECTS_CACHE: Dict[int, Dict] = {}
 
# ⚙️ Paramètres d'accès PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "Motuldb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


# ── 1. CLASSIFICATEUR D'INTENTION MODIFIÉ ─────────────────────────────────────

INTENT_PROMPT = ChatPromptTemplate.from_template(
    """Tu es un orchestrateur expert pour un système RAG multi-agent.
Ta mission est de router la question vers l'agent spécialisé le plus pertinent.

### CRITÈRES DE DÉCISION :
- **staffing** : questions sur des employés, TJM, jours travaillés, coûts RH,
                 rentabilité d'une ressource humaine, occupation, gain/perte employé,
                 ainsi que les listes d'employés/collaborateurs d'une année spécifique.
                 Exemples : "combien a travaillé Jean ?", "TJM de Marie",
                 "est-ce que cet employé est rentable ?", "occupation en mars",
                 "cite les employés de l'année 2026", "liste des collaborateurs en 2024".
- **excel** : données structurées, tableaux de chiffres, calculs financiers
                 NON liés aux ressources humaines.
- **pdf** : explications de concepts, procédures, résumés de textes longs, salutations, 
             questions de politesse ou de conversation générale.

Réponds UNIQUEMENT par le mot : `pdf`, `excel` ou `staffing`.
{history_context}
Question : {question}"""
)

def classify_intent(question: str, history: Optional[List[dict]] = None) -> IntentType:
    """Utilise l'LLM pour router la demande vers l'agent PDF, Excel ou Staffing."""
    logger.info(f"🧭 Classification de l'intention : '{question[:80]}'")
    
    lower_q = question.lower()
    
    # 1. Gestion des salutations directes pour éviter de déranger les agents de calculs
    if any(greet in lower_q for greet in ["bonjour", "salut", "hello", "hi", "bonsoir", "hey"]):
        logger.info("   → Salutation détectée. Routage par défaut vers PDF (Conversation générale).")
        return "pdf"
        
    # 2. Détection des requêtes générales sur le contenu du projet (plus flexible)
    general_keywords = [
        "contien", "contient", "document", "donnee", "donnée", "donne",
        "fichier", "qu'y a-t-il", "qu'il y a", "qu'est-ce qu'il y a",
        "contenu", "present dans", "présent dans", "existe dans"
    ]
    if any(kw in lower_q for kw in general_keywords) and any(kw2 in lower_q for kw2 in ["quel", "qu'est", "liste", "quoi", "exi", "y a"]):
        # Si la question porte sur des personnes, des employés ou des salaires, on ne route pas vers 'general'
        if not any(emp_kw in lower_q for emp_kw in ["employe", "employé", "employer", "collaborateur", "qui", "nom", "salaire", "tjm"]):
            logger.info("   → Intention identifiée comme requête générale de métadonnées.")
            return "general"

    history_context = ""
    if history:
        history_context = "Historique des échanges récents :\n"
        for h in history[-8:]:
            role = "Utilisateur" if h.get("role") == "user" else "Assistant"
            content = h.get("content", "")
            if len(content) > 200:
                content = content[:200] + "..."
            history_context += f"- {role} : {content}\n"
        history_context += "\n"

    llm = get_llm(temperature=0.0, max_tokens=10)
    chain = INTENT_PROMPT | llm | StrOutputParser()
    result = chain.invoke({"question": question, "history_context": history_context}).strip().lower()
    
    if "staffing" in result:
        intent = "staffing"
    elif "excel" in result:
        intent = "excel"
    else:
        intent = "pdf"
        
    logger.info(f"   → Intention retenue : {intent}")
    return intent


# ── 2. EXTRACTEUR STATELESS DIRECT DEPUIS POSTGRESQL MODIFIÉ ──────────────────

def rebuild_resources_from_postgres(project_id: int):
    """
    Se connecte à PostgreSQL, télécharge les chaînes Base64 du projet,
    nettoie les en-têtes Data URL (data:...;base64,), décode le flux en mémoire
    et initialise les structures de données volatiles (RAM), y compris docs_raw.
    """
    logger.info(f"🔄 [BDD ➔ RAM] Extraction et reconstruction de la base documentaire pour le projet ID: {project_id}")
    
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Récupération des documents indexés du projet
    cursor.execute(
        "SELECT id, file_name, content FROM documents WHERE project_id = %s AND is_indexed = TRUE;",
        (project_id,)
    )
    db_docs = cursor.fetchall()
    cursor.close()
    conn.close()

    if not db_docs:
        logger.warning(f"⚠️ Aucun document marqué 'is_indexed = TRUE' en BDD pour le projet ID {project_id}")
        RAM_PROJECTS_CACHE[project_id] = {
            "vectorstore": None,
            "dataframes": {},
            "docs_raw": [],
            "doc_ids": set(),
            "updated_at": datetime.now()
        }
        return None, {}, []

    all_chunks: List[Document] = []
    dataframes: Dict[str, pd.DataFrame] = {}
    docs_raw: List[Dict[str, Any]] = []

    for doc in db_docs:
        file_name = doc['file_name']
        base64_content = doc['content']
        suffix = os.path.splitext(file_name)[1].lower()

        if not base64_content:
            continue

        # Nettoyage des headers "data:...;base64," via Regex
        if ";base64," in base64_content:
            base64_content = re.sub(r'^data:.*?;base64,', '', base64_content)
        elif "," in base64_content:
            base64_content = base64_content.split(",")[1]

        # Nettoyage des espaces ou retours à la ligne parasites
        base64_content = base64_content.strip()

        # Création du fichier temporaire volatile
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            try:
                file_bytes_decoded = base64.b64decode(base64_content)
                tmp.write(file_bytes_decoded)
                temp_filepath = tmp.name
                
                # Enregistrement des bytes bruts pour le Staffing
                docs_raw.append({
                    "file_name": file_name,
                    "file_bytes": file_bytes_decoded,
                    "suffix": suffix,
                })
            except Exception as decode_err:
                logger.error(f"❌ Échec du décodage Base64 pour '{file_name}' : {decode_err}")
                continue

        try:
            if suffix in (".pdf", ".docx", ".doc"):
                from utils.loader_pdf import load_uploaded_files_from_paths
                chunks = load_uploaded_files_from_paths([temp_filepath])
                if chunks:
                    for chunk in chunks:
                        chunk.metadata["source"] = file_name
                    all_chunks.extend(chunks)
                    logger.info(f"✅ Chunks RAM extraits pour le document textuel : {file_name}")
                else:
                    logger.warning(f"⚠️ Le fichier {file_name} n'a généré aucun contenu exploitable.")
                
            elif suffix in (".csv", ".xlsx", ".xls", ".xlsm"):
                dataframes[os.path.splitext(file_name)[0]] = load_dataframe(temp_filepath)
                logger.info(f"✅ DataFrame RAM initialisé pour le tableau : {file_name}")
        except Exception as process_err:
            logger.error(f"❌ Erreur lors du traitement du fichier temporaire {file_name} : {process_err}")
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)  # 🗑️ Suppression immédiate du disque dur

    # Montage du VectorStore FAISS éphémère en RAM
    vectorstore = None
    if all_chunks:
        logger.info(f"🔢 Vectorisation en RAM de {len(all_chunks)} chunks via Ollama...")
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        vectorstore = FAISS.from_documents(all_chunks, embeddings)
        logger.info("✅ Index FAISS temporaire créé avec succès en RAM.")

    # 🎯 Mise en cache des structures prêtes à l'emploi
    RAM_PROJECTS_CACHE[project_id] = {
        "vectorstore": vectorstore,
        "dataframes": dataframes,
        "docs_raw": docs_raw,
        "doc_ids": {doc['id'] for doc in db_docs},
        "updated_at": datetime.now()
    }
    return vectorstore, dataframes, docs_raw


def get_project_resources(project_id: int):
    """
    Fonction avec validation intelligente du cache par rapport à la base de données.
    Si de nouveaux fichiers sont indexés ou supprimés en BDD, recharge les ressources en RAM.
    """
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM documents WHERE project_id = %s AND is_indexed = TRUE;", (project_id,))
        db_doc_ids = {row[0] for row in cursor.fetchall()}
        cursor.close()
        conn.close()
    except Exception as db_err:
        logger.error(f"❌ Impossible de vérifier la BDD pour la validation de cache : {db_err}")
        db_doc_ids = set()

    if project_id in RAM_PROJECTS_CACHE:
        cached_doc_ids = RAM_PROJECTS_CACHE[project_id].get("doc_ids", set())
        if cached_doc_ids == db_doc_ids:
            logger.info(f"⚡ [CACHE RAM HIT] Récupération instantanée du contexte projet {project_id}")
            res = RAM_PROJECTS_CACHE[project_id]
            return res["vectorstore"], res["dataframes"], res.get("docs_raw", [])
        else:
            logger.info(f"🔄 [CACHE RAM INVALID] Les documents indexés en BDD ont changé. Rechargement...")
    
    logger.info(f"📡 [CACHE RAM MISS] Initialisation requise pour le projet {project_id}")
    return rebuild_resources_from_postgres(project_id)


# ── 3. AGENT PDF (RAG EN MÉMOIRE) ─────────────────────────────────────────────

RAG_PROMPT = ChatPromptTemplate.from_template(
    """Tu es un assistant expert en extraction et analyse documentaire.
Tu doit extraire les informations demandées avec une fidélité absolue, sans rien inventer ni généraliser.

⚠️ DIRECTIVES STRICTES DE MISE EN FORME :
1. Présente TOUJOURS tes réponses de manière aérée et hautement lisible.
2. Utilise des titres Markdown clairs (## pour les sections principales, ### pour les sous-sections).
3. Structure tes explications avec des listes à puces aérées ou des tableaux Markdown.
4. Intègre des émojis contextuels et pertinents au début des titres et des points clés pour guider l'œil.
5. Mets en gras (**Texte**) les concepts, règles de gestion et champs obligatoires critiques.

CONTEXTE DE SPÉCIFICATION :
{context}
{history_section}
QUESTION :
{question}

RÉPONSE FORMATEE EN MARKDOWN CORRETE :"""
)

# 🎯 FIXATION : run_pdf_agent accepte désormais directement la liste de 'docs' pré-extraits
def run_pdf_agent(question: str, docs: List[Document], history: Optional[List[dict]] = None) -> str:
    """Reçoit les documents pré-extraits par l'orchestrateur et génère la réponse finale via le LLM."""
    logger.info(f"📄 Agent PDF activé avec {len(docs)} documents sources.")
    
    context = "\n\n---\n\n".join(
        [f"📄 Source : {d.metadata.get('source', 'Inconnu')}\n{d.page_content}" for d in docs]
    )
    logger.info(f"   → Contexte assemblé : {len(context)} caractères")

    history_section = ""
    if history:
        history_section = "\n\n══════════════════════════════════════════════\nHISTORIQUE DES ÉCHANGES RÉCENTS :\n══════════════════════════════════════════════\n"
        for h in history[-8:]:
            role = "Utilisateur" if h.get("role") == "user" else "Assistant"
            content = h.get("content", "")
            if len(content) > 500:
                content = content[:500] + "..."
            history_section += f"- {role} : {content}\n"

    llm = get_llm(temperature=0.1, max_tokens=2048)
    chain = RAG_PROMPT | llm | StrOutputParser()
    answer = chain.invoke({"context": context, "question": question, "history_section": history_section})
    logger.info(f"✅ Réponse PDF générée ({len(answer)} caractères)")
    return answer


def get_staffing_docs_raw_from_postgres(project_id: int) -> list:
    """
    Lit les fichiers staffing depuis la table staffing_documents si elle existe,
    sinon se rabat sur la table documents (qui contient tous les fichiers du projet).
    Décode le base64 en bytes directement en RAM — rien sur le disque.
    """
    logger.info(f"📂 [Staffing BDD→RAM] Lecture des fichiers staffing projet {project_id}")
    
    conn   = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Vérification de l'existence de la table staffing_documents
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'staffing_documents'
        );
    """)
    has_staffing_table = cursor.fetchone()["exists"]
    
    if has_staffing_table:
        logger.info("   → Utilisation de la table dédiée 'staffing_documents'")
        cursor.execute(
            """SELECT file_name, content, extension
               FROM staffing_documents
               WHERE project_id = %s
               ORDER BY uploaded_at DESC;""",
            (project_id,)
        )
    else:
        logger.info("   → Table 'staffing_documents' inexistante. Utilisation de la table 'documents'")
        cursor.execute(
            """SELECT file_name, content, NULL as extension
               FROM documents
               WHERE project_id = %s
               ORDER BY uploaded_at DESC;""",
            (project_id,)
        )
        
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    docs_raw = []
    for row in rows:
        file_name = row["file_name"]
        content   = row["content"] or ""
        ext       = row.get("extension")
        suffix    = ext or os.path.splitext(file_name)[1].lower()
        if not suffix.startswith("."): suffix = f".{suffix}"

        # Nettoyer le préfixe data-URL
        if ";base64," in content:
            pure = re.sub(r'^data:.*?;base64,', '', content)
        elif "," in content:
            pure = content.split(",")[1]
        else:
            pure = content

        pure = pure.strip().replace(" ", "").replace("\n", "")

        try:
            file_bytes = base64.b64decode(pure)
            docs_raw.append({
                "file_name":  file_name,
                "file_bytes": file_bytes,   # bytes en RAM, jamais écrits sur disque
                "suffix":     suffix,
            })
            logger.info(f"✅ Décodé en RAM : {file_name} ({len(file_bytes):,} bytes)")
        except Exception as e:
            logger.error(f"❌ Erreur décodage '{file_name}': {e}")

    logger.info(f"📊 {len(docs_raw)} fichier(s) staffing chargés en RAM")
    return docs_raw


# ── 4. ORCHESTRATEUR PRINCIPAL UNIFIÉ AVEC LE ROUTAGE STAFFING ────────────────

def orchestrate(
    question: str,
    project_id: int,
    force_agent: Optional[str] = None,
    history: Optional[List[dict]] = None,
    theme_mode: Optional[str] = "light",
) -> Dict[str, Any]:
    """
    Point d'entrée de l'orchestrateur. Consomme les structures en RAM, route
    vers le bon agent (PDF, Excel, Staffing) et extrait les sources et graphiques nécessaires.
    """
    result = {
        "agent_used": None,
        "intent": None,
        "answer": "",
        "error": None,
        "docs": [],
        "charts": [],   # Initialisation pour accueillir les graphiques de l'agent staffing
        "sources": []   # Initialisation pour accueillir les métadonnées de sources du staffing
    }

    try:
        # 1. Récupération immédiate depuis le registre RAM ou reconstruction automatique
        vectorstore, dataframes, docs_raw = get_project_resources(project_id)

        # 2. Routage intelligent ou forcé
        intent = force_agent if force_agent in ("pdf", "excel", "staffing") else classify_intent(question, history=history)
        result["intent"] = intent

        # 3. Traitement selon l'intention identifiée
        if intent == "pdf":
            if vectorstore is None:
                # Vérifions si des documents de type texte existent bien en base de données pour ce projet
                pdf_files_in_db = []
                try:
                    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(
                        "SELECT file_name FROM documents WHERE project_id = %s AND is_indexed = TRUE;",
                        (project_id,)
                    )
                    db_docs = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    for doc in db_docs:
                        fname = doc["file_name"]
                        ext = os.path.splitext(fname)[1].lower()
                        if ext in (".pdf", ".docx", ".doc"):
                            pdf_files_in_db.append(fname)
                except Exception as db_err:
                    logger.error(f"Erreur de lecture BDD pour détection PDF : {db_err}")

                if pdf_files_in_db:
                    result["agent_used"] = "Orchestrateur (Alerte RAG)"
                    result["answer"] = (
                        f"Le fichier PDF **{', '.join(pdf_files_in_db)}** est bien présent dans le projet, "
                        "mais il semble être **scanné (image)** ou ne pas contenir de texte sélectionnable.\n\n"
                        "⚠️ **Solution** : Veuillez importer un document PDF contenant du texte sélectionnable "
                        "ou un fichier Word (.docx) pour que le chatbot puisse l'analyser."
                    )
                    return result

                if dataframes:
                    logger.info("ℹ️ Aucun index PDF disponible mais des tables Excel existent. Utilisation du LLM général pour répondre.")
                    llm = get_llm(temperature=0.7, max_tokens=1024)
                    prompt = ChatPromptTemplate.from_template(
                        "Tu es un assistant expert. Le projet contient uniquement les fichiers Excel suivants : {excel_files}.\n"
                        "Il n'y a pas de documents PDF/Word importés.\n"
                        "Réponds poliment à la salutation ou à la question de l'utilisateur, et indique-lui les fichiers Excel disponibles s'il souhaite faire des analyses de données.\n"
                        "Question : {question}\n"
                        "Réponse :"
                    )
                    chain = prompt | llm | StrOutputParser()
                    result["agent_used"] = "LLM Général (Pas de PDF indexé)"
                    result["answer"] = chain.invoke({"excel_files": ", ".join(dataframes.keys()), "question": question})
                    return result
                else:
                    result["error"] = "⚠️ Aucun document indexé trouvé en base de données pour ce projet. Veuillez d'abord charger un document."
                    return result
            
            result["agent_used"] = "Agent PDF (RAG Stateless en RAM)"
            
            # 🎯 FIXATION : Appel de la méthode native .similarity_search() sur l'instance vectorstore
            docs = vectorstore.similarity_search(question, k=5)
            result["docs"] = docs  # ← On injecte les documents trouvés dans le dictionnaire de résultat pour le DTO
            
            if not docs:
                result["answer"] = "Aucun document pertinent trouvé dans l'index FAISS éphémère."
            else:
                # Exécution de l'agent PDF RAG en lui passant directement les documents isolés
                result["answer"] = run_pdf_agent(question, docs, history=history)

        elif intent == "excel":
            if not dataframes:
                result["error"] = "⚠️ Aucun tableau de données (Excel/CSV) indexé trouvé en BDD pour ce projet."
                return result
            
            result["agent_used"] = "Agent Excel (Pandas en RAM)"
            excel_res = run_excel_agent(question, dataframes, history=history, theme_mode=theme_mode)
            result["answer"] = excel_res.get("answer", "")
            result["charts"] = excel_res.get("charts", [])
            
            # Met à disposition les clés des DataFrames chargés en mémoire comme références de sources
            result["docs"] = list(dataframes.keys()) 

        # ── 4. BLOC DE ROUTAGE POUR L'AGENT STAFFING ───────────────────────────
        elif intent == "staffing":
            from agents.staffing_agent import run_staffing_agent

            # Lire depuis staffing_documents (pas documents) — tout en RAM depuis PostgreSQL
            docs_raw = get_staffing_docs_raw_from_postgres(project_id)

            if not docs_raw:
                result["error"] = "⚠️ Aucun fichier dans staffing_documents pour ce projet."
                result["answer"] = result["error"]
                return result

            staffing_result = run_staffing_agent(
                question=question,
                docs_raw=docs_raw,
                history=history,
                theme_mode=theme_mode,
            )

            if staffing_result.get("error"):
                result["error"] = staffing_result["error"]
                result["answer"] = staffing_result["error"]
            else:
                result["agent_used"] = "Agent Staffing (Base64 PostgreSQL → RAM → Calculs → Graphiques)"
                result["answer"] = staffing_result["answer"]
                result["docs"] = []
                result["charts"] = staffing_result.get("charts", [])
                result["sources"] = staffing_result.get("sources", [])

        elif intent == "general":
            pdf_names = []
            excel_names = []
            try:
                conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(
                    "SELECT file_name FROM documents WHERE project_id = %s AND is_indexed = TRUE;",
                    (project_id,)
                )
                db_docs = cursor.fetchall()
                cursor.close()
                conn.close()
                for doc in db_docs:
                    fname = doc["file_name"]
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in (".pdf", ".docx", ".doc"):
                        pdf_names.append(fname)
                    elif ext in (".csv", ".xlsx", ".xls", ".xlsm"):
                        excel_names.append(fname)
            except Exception as db_err:
                logger.error(f"❌ Erreur lecture BDD pour l'intention générale : {db_err}")

            # Construire la réponse textuelle
            answer_parts = ["Le projet contient les ressources suivantes dans la base de données :"]
            if pdf_names:
                answer_parts.append(f"- **Documents PDF & Word** : " + ", ".join(f"`{n}`" for n in pdf_names))
            if excel_names:
                answer_parts.append(f"- **Données Excel & CSV** : " + ", ".join(f"`{n}`" for n in excel_names))
            if not pdf_names and not excel_names:
                answer_parts.append("- Aucun document indexé actuellement.")

            result["agent_used"] = "Orchestrateur (Métadonnées)"
            result["answer"] = "\n".join(answer_parts)
            result["docs"] = []

        else:
            result["error"] = "❌ Intention non reconnue."

    except Exception as e:
        logger.error(f"❌ Erreur critique dans l'orchestrateur : {e}", exc_info=True)
        result["error"] = f"❌ Erreur interne : {str(e)}"

    return result