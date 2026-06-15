"""
services/chat_service.py — VERSION AVEC SOURCES
─────────────────────────────────────────────────────────────────────────────
Ajouts par rapport à la version précédente :
  1. stream_response retourne maintenant les sources dans le message "done"
  2. Le prompt force un rendu Markdown structuré ET cite les sources
"""

import json
import logging
import asyncio
from typing import Optional, Dict, List
import pandas as pd

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.llm_factory import get_llm
from utils.orchestrator import classify_intent

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# STREAMING CALLBACK
# ══════════════════════════════════════════════════════════════════════════════

class WebSocketStreamHandler(AsyncCallbackHandler):
    def __init__(self, send_fn):
        self.send_fn = send_fn
        self.tokens: list[str] = []

    async def on_llm_new_token(self, token: str, **kwargs):
        self.tokens.append(token)
        await self.send_fn(json.dumps({"type": "token", "token": token}))


# ══════════════════════════════════════════════════════════════════════════════
# NOUVEAU PROMPT — structure la réponse ET cite les fichiers sources
# ══════════════════════════════════════════════════════════════════════════════

RAG_PROMPT = ChatPromptTemplate.from_template(
    """Tu es un assistant expert en analyse documentaire. Tu travailles EXCLUSIVEMENT
à partir des documents fournis dans le contexte ci-dessous.

══════════════════════════════════════════════
RÈGLES ABSOLUES :
══════════════════════════════════════════════
1. Ne fabrique JAMAIS d'information absente du contexte.
2. Cite les valeurs exactes (chiffres, dates, noms, règles).
3. Si la réponse est incomplète, dis-le clairement.

══════════════════════════════════════════════
MISE EN FORME OBLIGATOIRE :
══════════════════════════════════════════════
- Commence par un résumé direct en 1-2 phrases.
- Utilise ## pour les sections principales.
- Utilise des listes à tirets (- item) pour les énumérations.
- Mets en **gras** les mots-clés, règles et valeurs importantes.
- Pour les tableaux de données, utilise le format Markdown :
  | Colonne 1 | Colonne 2 |
  |-----------|-----------|
  | valeur    | valeur    |
- Termine TOUJOURS par une section ## Sources consultées
  listant chaque fichier utilisé sous la forme :
  - 📄 **NomDuFichier** (page X) : [phrase résumant ce qui y a été trouvé]

══════════════════════════════════════════════
CONTEXTE DOCUMENTAIRE :
══════════════════════════════════════════════
{context}

══════════════════════════════════════════════
QUESTION :
══════════════════════════════════════════════
{question}

Réponds en français. Sois précis, structuré et lisible.

RÉPONSE :"""
)


# ══════════════════════════════════════════════════════════════════════════════
# HELPER — construit la liste des sources depuis les docs FAISS
# ══════════════════════════════════════════════════════════════════════════════

def _build_sources(docs: list) -> list:
    """
    Regroupe les chunks FAISS par fichier source.
    Retourne une liste de dicts sérialisables en JSON.
    """
    from collections import defaultdict
    groups = defaultdict(lambda: {"pages": set(), "count": 0})

    for doc in docs:
        if hasattr(doc, "metadata"):
            src  = doc.metadata.get("source", "Document inconnu")
            page = doc.metadata.get("page")
            groups[src]["count"] += 1
            if page is not None:
                groups[src]["pages"].add(int(page) + 1)
        else:
            src = str(doc)
            groups[src]["count"] += 1

    result = []
    for file_name, info in groups.items():
        pages = sorted(info["pages"])
        if len(pages) >= 2:
            pages_str = f"{pages[0]}–{pages[-1]}"
        elif len(pages) == 1:
            pages_str = str(pages[0])
        else:
            pages_str = None

        result.append({
            "fileName":     file_name,
            "pages":        pages_str,
            "extractCount": info["count"],
        })

    # Source la plus utilisée en premier
    return sorted(result, key=lambda s: s["extractCount"], reverse=True)


# ══════════════════════════════════════════════════════════════════════════════
# SERVICE CHAT
# ══════════════════════════════════════════════════════════════════════════════

class ChatService:

    async def stream_response(
        self,
        question:    str,
        project:     str,
        vectorstore: Optional[FAISS],
        dataframes:  Optional[Dict[str, pd.DataFrame]],
        send_fn,
        force_agent: Optional[str] = None,
    ):
        full_text  = ""
        agent_used = ""
        sources    = []         # ← NOUVEAU

        try:
            intent = force_agent if force_agent in ("pdf", "excel") \
                     else classify_intent(question)
            agent_label = "Agent PDF (RAG)" if intent == "pdf" else "Agent Excel (Pandas)"
            agent_used  = agent_label

            await send_fn(json.dumps({
                "type":   "intent",
                "intent": intent,
                "agent":  agent_label,
            }))

            if intent == "pdf":
                full_text, sources = await self._stream_pdf(question, vectorstore, send_fn)
            elif intent == "excel":
                full_text = await self._run_excel(question, dataframes, send_fn)

            # Signal "done" — inclut maintenant les sources
            await send_fn(json.dumps({
                "type":       "done",
                "full_text":  full_text,
                "agent_used": agent_used,
                "intent":     intent,
                "sources":    sources,      # ← envoyé à Angular
            }))

        except Exception as e:
            logger.error(f"Erreur ChatService: {e}", exc_info=True)
            await send_fn(json.dumps({"type": "error", "message": str(e)}))


    async def _stream_pdf(self, question: str, vectorstore, send_fn):
        """Retourne (full_text, sources)."""
        if vectorstore is None:
            msg = "⚠️ Aucun document indexé pour ce projet."
            await send_fn(json.dumps({"type": "token", "token": msg}))
            return msg, []

        docs = vectorstore.similarity_search(question, k=5)
        if not docs:
            msg = "❌ Aucun document pertinent trouvé."
            await send_fn(json.dumps({"type": "token", "token": msg}))
            return msg, []

        # Construire les sources AVANT d'appeler le LLM
        sources = _build_sources(docs)

        context = "\n\n---\n\n".join(
            f"📄 Source : {d.metadata.get('source', 'Inconnu')}\n{d.page_content}"
            for d in docs
        )

        handler = WebSocketStreamHandler(send_fn)
        llm     = get_llm(temperature=0.1, max_tokens=2048, streaming=True, callbacks=[handler])
        chain   = RAG_PROMPT | llm | StrOutputParser()
        result  = await chain.ainvoke({"context": context, "question": question})

        return result or "".join(handler.tokens), sources


    async def _run_excel(self, question: str, dataframes, send_fn) -> str:
        if not dataframes:
            msg = "⚠️ Aucun tableau chargé pour ce projet."
            await send_fn(json.dumps({"type": "token", "token": msg}))
            return msg

        from utils.loader_excel import run_excel_agent
        loop   = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_excel_agent, question, dataframes)

        words = result.split(" ")
        chunk = []
        for w in words:
            chunk.append(w)
            if len(chunk) == 4:
                await send_fn(json.dumps({"type": "token", "token": " ".join(chunk) + " "}))
                chunk = []
                await asyncio.sleep(0.02)
        if chunk:
            await send_fn(json.dumps({"type": "token", "token": " ".join(chunk)}))

        return result