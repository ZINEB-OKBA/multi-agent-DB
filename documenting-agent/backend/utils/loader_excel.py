"""
loader_excel.py
---------------
Charge les fichiers CSV et Excel dans des DataFrames Pandas.

CORRECTIONS :
  - Lecture xlsx avec fallback multi-engine (openpyxl → xlrd → calamine)
  - Installation automatique d'openpyxl dans le venv si absent
  - Avertissement clair si le package est manquant
"""

import os
import sys
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict

import pandas as pd
from langchain_experimental.agents import create_pandas_dataframe_agent
from utils.llm_factory import get_llm

logger = logging.getLogger(__name__)


# ── Auto-install openpyxl dans le venv si absent ───────────────────────────────

def _ensure_openpyxl():
    """Installe openpyxl dans le venv courant si non disponible."""
    try:
        import openpyxl  # noqa
        return True
    except ImportError:
        logger.warning("⚠️  openpyxl absent — tentative d'installation automatique...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "openpyxl", "tabulate", "--quiet"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            import openpyxl  # noqa
            logger.info("✅ openpyxl installé avec succès.")
            return True
        except Exception as e:
            logger.error(f"❌ Impossible d'installer openpyxl : {e}")
            return False


def _ensure_tabulate():
    """Installe tabulate dans le venv courant si non disponible."""
    try:
        import tabulate  # noqa
        return True
    except ImportError:
        logger.warning("⚠️  tabulate absent — tentative d'installation automatique...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "tabulate", "--quiet"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            import tabulate  # noqa
            logger.info("✅ tabulate installé avec succès.")
            return True
        except Exception as e:
            logger.error(f"❌ Impossible d'installer tabulate : {e}")
            return False


# ── Chargement ─────────────────────────────────────────────────────────────────

def load_dataframe(file_path: str) -> pd.DataFrame:
    """
    Charge un CSV ou Excel en DataFrame.
    Pour xlsx/xls : essaie plusieurs engines dans l'ordre jusqu'à succès.
    """
    suffix = Path(file_path).suffix.lower()
    logger.info(f"📊 Chargement : {file_path}")

    if suffix == ".csv":
        # Essaie plusieurs encodages courants
        for enc in ("utf-8", "latin-1", "cp1252", "utf-8-sig"):
            try:
                df = pd.read_csv(file_path, encoding=enc)
                logger.info(f"   → {df.shape[0]} lignes × {df.shape[1]} colonnes (encoding={enc})")
                return df
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Impossible de lire le CSV {file_path} avec les encodages connus.")

    elif suffix in (".xlsx", ".xlsm", ".xltx", ".xltm"):
        # Essaie openpyxl en premier
        _ensure_openpyxl()
        engines = ["openpyxl", "calamine"]
        last_err = None
        for engine in engines:
            try:
                df = pd.read_excel(file_path, engine=engine)
                logger.info(f"   → {df.shape[0]} lignes × {df.shape[1]} colonnes (engine={engine})")
                return df
            except Exception as e:
                last_err = e
                logger.warning(f"   ⚠️  Engine '{engine}' échoué : {e}")
        raise ImportError(
            f"Impossible de lire le fichier xlsx.\n"
            f"Ouvre PowerShell en ADMINISTRATEUR et tape :\n"
            f"  {sys.executable} -m pip install openpyxl tabulate --force-reinstall\n"
            f"Erreur : {last_err}"
        )

    elif suffix == ".xls":
        try:
            df = pd.read_excel(file_path, engine="xlrd")
            logger.info(f"   → {df.shape[0]} lignes × {df.shape[1]} colonnes (engine=xlrd)")
            return df
        except Exception as e:
            raise ImportError(
                f"Impossible de lire le .xls. Installe xlrd :\n"
                f"  {sys.executable} -m pip install xlrd\n"
                f"Erreur : {e}"
            )

    else:
        raise ValueError(f"Format non supporté : {suffix}")


def load_all_tables(tables_folder: str) -> Dict[str, pd.DataFrame]:
    """Charge tous les CSV/Excel d'un dossier."""
    folder = Path(tables_folder)
    if not folder.exists():
        raise FileNotFoundError(f"Dossier introuvable : {tables_folder}")

    dataframes: Dict[str, pd.DataFrame] = {}
    for f in folder.iterdir():
        if f.suffix.lower() in (".csv", ".xlsx", ".xls", ".xlsm"):
            try:
                dataframes[f.stem] = load_dataframe(str(f))
            except Exception as e:
                logger.error(f"❌ {f.name} ignoré : {e}")

    if not dataframes:
        raise ValueError(f"Aucun CSV/Excel chargé dans : {tables_folder}")
    return dataframes


def load_uploaded_tables(uploaded_files) -> Dict[str, pd.DataFrame]:
    """
    Charge des fichiers uploadés via Streamlit dans des DataFrames.
    Affiche une erreur claire si openpyxl est manquant.
    """
    # S'assurer que les dépendances sont présentes au moment du chargement
    _ensure_openpyxl()
    _ensure_tabulate()

    dataframes: Dict[str, pd.DataFrame] = {}

    for uf in uploaded_files:
        suffix = Path(uf.name).suffix.lower()
        if suffix not in (".csv", ".xlsx", ".xls", ".xlsm"):
            logger.warning(f"⚠️  Fichier ignoré (format non supporté) : {uf.name}")
            continue

        logger.info(f"📥 Réception : {uf.name} ({getattr(uf, 'size', '?')} octets)")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = uf.read()
            tmp.write(content)
            tmp_path = tmp.name

        logger.info(f"   → Fichier tmp : {tmp_path} ({len(content)} octets)")

        try:
            df = load_dataframe(tmp_path)
            dataframes[Path(uf.name).stem] = df
            logger.info(f"   ✅ {uf.name} chargé : {df.shape[0]}L × {df.shape[1]}C")
        except ImportError as e:
            # Erreur d'installation de dépendance → message très clair
            logger.error(f"❌ Dépendance manquante pour {uf.name} : {e}")
            raise  # remonter pour affichage dans Streamlit
        except Exception as e:
            logger.error(f"❌ Erreur chargement {uf.name} : {e}")
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    logger.info(f"✅ {len(dataframes)} tableau(x) chargé(s) : {list(dataframes.keys())}")
    return dataframes


# ── Agent Pandas ───────────────────────────────────────────────────────────────

def get_pandas_agent(dataframes: Dict[str, pd.DataFrame], verbose: bool = True):
    """Crée un agent LangChain Pandas branché sur Groq."""
    _ensure_tabulate()  # tabulate requis par to_markdown() dans le prompt

    llm = get_llm(temperature=0.0)
    df_list = list(dataframes.values())
    df_input = df_list[0] if len(df_list) == 1 else df_list

    logger.info(f"🤖 Création agent Pandas ({len(df_list)} DataFrame(s))")

    agent = create_pandas_dataframe_agent(
        llm=llm,
        df=df_input,
        agent_type="zero-shot-react-description",
        verbose=verbose,
        allow_dangerous_code=True,
        max_iterations=10,
        handle_parsing_errors=True, # <--- AJOUTE CETTE LIGNE
       prefix = (
    "Tu es un Expert Data Analyst multi-domaines. Tu travailles sur des projets variés "
    "(Finance, Ingénierie, RH, etc.) et tu dois fournir des analyses de haute précision.\n\n"
    
    "CONSIGNES DE RÉPONSE :\n"
    "1. **Exploration Exhaustive** : Ne donne pas juste une valeur. Si l'utilisateur pose une question, "
    "regarde toutes les colonnes liées pour fournir un tableau détaillé (ex: si on parle d'un OPCVM, "
    "donne aussi son ISIN, sa Société de Gestion et sa performance si disponibles).\n"
    "2. **Formatage Professionnel** : Utilise TOUJOURS des tableaux Markdown pour présenter des listes ou des comparaisons.\n"
    "3. **Identification du Projet** : Commence par identifier brièvement de quel contexte il s'agit "
    "(ex: 'Analyse du fichier des performances OPCVM...').\n"
    "4. **Calculs & Logique** : Si tu fais un calcul, explique ta formule (ex: Moyenne = Somme / Nombre).\n"
    "5. **Langue** : Réponds exclusivement en français, avec un ton expert.\n"
    "6. **Rigueur** : Si une information est manquante, liste les colonnes réellement disponibles pour aider l'utilisateur."
    "\n\nIMPORTANT : Ta réponse finale DOIT impérativement commencer par le mot-clé 'Final Answer:' "
    "suivi de ton analyse détaillée. Ne t'arrête pas avant d'avoir utilisé ce mot-clé."
)
)
    
    return agent


def run_excel_agent(question: str, dataframes: Dict[str, pd.DataFrame]) -> str:
    """Exécute l'agent Pandas sur la question posée."""
    logger.info(f"❓ Question Excel : {question}")
    agent = get_pandas_agent(dataframes)
    try:
        result = agent.invoke({"input": question})
        answer = result.get("output", str(result))
        logger.info(f"✅ Réponse Excel ({len(answer)} caractères)")
        return answer
    except Exception as e:
        logger.error(f"❌ Erreur agent Excel : {e}")
        return f"❌ Erreur lors de l'analyse Excel : {str(e)}"
