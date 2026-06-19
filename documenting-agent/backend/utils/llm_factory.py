"""
utils/llm_factory.py
---------------------
Factory multi-provider : Groq, Ollama, Anthropic (Claude).
Supporte le streaming (callbacks).
"""

import os
import logging
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()
logger     = logging.getLogger(__name__)
MODEL_NAME = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# ── Liste des modèles Anthropic connus ────────────────────────────────────────
ANTHROPIC_MODELS = [
    "claude-3-5-haiku",
    "claude-3-5-sonnet",
    "claude-3-haiku",
    "claude-3-sonnet",
    "claude-3-opus",
    "claude-sonnet-4",
    "claude-opus-4",
    "claude-opus-4-5",
]


def _is_anthropic_model(name: str) -> bool:
    """Détecte si le modèle est un modèle Anthropic Claude."""
    return name.startswith("claude-")


def _is_ollama_model(name: str) -> bool:
    """Détecte si le modèle est un modèle local Ollama."""
    return ":" in name or any(
        name.startswith(prefix)
        for prefix in ["llama3.3", "phi4", "qwen", "llama3.2"]
    )


def get_llm(
    temperature: float = 0.0,
    max_tokens:  int   = 2048,
    streaming:   bool  = False,
    callbacks:   Optional[List] = None,
):
    """
    Retourne une instance LLM selon le provider détecté automatiquement :
      - Anthropic Claude (si MODEL_NAME commence par "claude-")
      - Ollama local     (si MODEL_NAME contient ":" ou préfixe connu)
      - Groq Cloud       (par défaut)
    """

    # ── 1. Anthropic Claude ───────────────────────────────────────────────────
    if _is_anthropic_model(MODEL_NAME):
        from langchain_anthropic import ChatAnthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "❌ ANTHROPIC_API_KEY introuvable.\n"
                "Ajoute dans ton .env : ANTHROPIC_API_KEY=sk-ant-xxx\n"
                "Clé sur https://console.anthropic.com"
            )

        logger.info(f"🔧 LLM : Anthropic {MODEL_NAME} | streaming={streaming}")
        return ChatAnthropic(
            model       = MODEL_NAME,
            api_key     = api_key,
            temperature = temperature,
            max_tokens  = max_tokens,
            streaming   = streaming,
            callbacks   = callbacks or [],
        )

    # ── 2. Ollama local ───────────────────────────────────────────────────────
    if _is_ollama_model(MODEL_NAME):
        from langchain_ollama import ChatOllama

        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        logger.info(f"🔧 LLM : Ollama local ({MODEL_NAME}) | URL: {ollama_url} | streaming={streaming}")
        return ChatOllama(
            model       = MODEL_NAME,
            base_url    = ollama_url,
            temperature = temperature,
            streaming   = streaming,
            callbacks   = callbacks or [],
        )

    # ── 3. Groq Cloud (défaut) ────────────────────────────────────────────────
    from langchain_groq import ChatGroq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "❌ GROQ_API_KEY introuvable.\n"
            "Crée un fichier .env : GROQ_API_KEY=gsk_xxx\n"
            "Clé gratuite sur https://console.groq.com"
        )

    logger.info(f"🔧 LLM : Groq {MODEL_NAME} | streaming={streaming}")

    return ChatGroq(
        model       = MODEL_NAME,
        api_key     = api_key,
        temperature = temperature,
        max_tokens  = max_tokens,
        streaming   = streaming,
        callbacks   = callbacks or [],
    )


def test_groq_connection() -> tuple[bool, str]:
    """Teste la connexion au provider LLM. Retourne (succès, message)."""
    try:
        llm = get_llm(max_tokens=5)
        llm.invoke("ok")
        return True, f"✅ Connexion {MODEL_NAME} OK"
    except EnvironmentError as e:
        return False, str(e)
    except Exception as e:
        err = str(e)
        if "Connection error" in err or "APIConnectionError" in err:
            return False, "❌ Erreur réseau. Vérifie ta connexion / VPN."
        if "401" in err or "invalid_api_key" in err.lower():
            return False, "❌ Clé API invalide."
        if "429" in err:
            return False, "❌ Rate limit atteint."
        return False, f"❌ Erreur LLM : {err}"
