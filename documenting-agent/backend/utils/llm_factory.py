"""
utils/llm_factory.py
---------------------
Factory Groq — Llama-3.3-70B-Versatile.
Supporte maintenant le streaming (callbacks).
"""

import os
import logging
from typing import Optional, List
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
logger     = logging.getLogger(__name__)
MODEL_NAME = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")


def get_llm(
    temperature: float = 0.0,
    max_tokens:  int   = 2048,
    streaming:   bool  = False,
    callbacks:   Optional[List] = None,
) -> ChatGroq:
    """
    Retourne une instance ChatGroq.

    Args:
        temperature : Créativité (0.0 = déterministe).
        max_tokens  : Longueur max de la réponse.
        streaming   : Active le streaming token par token.
        callbacks   : Liste de callbacks LangChain (ex: WebSocketStreamHandler).
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "❌ GROQ_API_KEY introuvable.\n"
            "Crée un fichier .env : GROQ_API_KEY=gsk_xxx\n"
            "Clé gratuite sur https://console.groq.com"
        )

    logger.info(f"🔧 LLM : {MODEL_NAME} | streaming={streaming}")

    return ChatGroq(
        model       = MODEL_NAME,
        api_key     = api_key,
        temperature = temperature,
        max_tokens  = max_tokens,
        streaming   = streaming,
        callbacks   = callbacks or [],
    )


def test_groq_connection() -> tuple[bool, str]:
    """Teste la connexion Groq. Retourne (succès, message)."""
    try:
        llm = get_llm(max_tokens=5)
        llm.invoke("ok")
        return True, "✅ Connexion Groq OK"
    except EnvironmentError as e:
        return False, str(e)
    except Exception as e:
        err = str(e)
        if "Connection error" in err or "APIConnectionError" in err:
            return False, "❌ Erreur réseau vers Groq. Vérifie ta connexion / VPN."
        if "401" in err or "invalid_api_key" in err.lower():
            return False, "❌ Clé API Groq invalide."
        if "429" in err:
            return False, "❌ Rate limit Groq atteint."
        return False, f"❌ Erreur Groq : {err}"
