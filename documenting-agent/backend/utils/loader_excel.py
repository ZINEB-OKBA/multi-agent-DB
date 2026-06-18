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
import matplotlib
matplotlib.use("Agg")
from langchain_experimental.agents import create_pandas_dataframe_agent
from utils.llm_factory import get_llm
from typing import Dict, Any, Optional
import plotly.io as pio
import base64
from plotly.io._base_renderers import ExternalRenderer

class Base64ImageRenderer(ExternalRenderer):
    def __init__(self):
        self.figures = []
    def render(self, fig, **kwargs):
        self.figures.append(fig)

plotly_capture_renderer = Base64ImageRenderer()
pio.renderers["base64_capture"] = plotly_capture_renderer
pio.renderers.default = "base64_capture"

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
        agent_executor_kwargs={"handle_parsing_errors": True, "return_intermediate_steps": True},
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


def _capture_matplotlib_figures() -> list:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import io
    import base64

    charts = []
    fignums = plt.get_fignums()
    logger.info(f"📊 Capture des figures matplotlib : {len(fignums)} figures détectées.")
    for num in fignums:
        try:
            fig = plt.figure(num)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode("utf-8")
            
            # Tenter de deviner ou extraire le titre du graphique
            title = "Analyse graphique"
            if fig.axes:
                ax = fig.axes[0]
                if ax.get_title():
                    title = ax.get_title()
            
            charts.append({
                "title": title,
                "type": "bar",
                "base64": f"data:image/png;base64,{b64}",
                "chartjs": None
            })
        except Exception as e:
            logger.error(f"Erreur de capture de la figure matplotlib {num}: {e}")
    
    # Nettoyer toutes les figures en mémoire
    plt.close("all")
    return charts


def _capture_plotly_figures(theme_mode: str = "light") -> list:
    charts = []
    logger.info(f"📊 Capture des figures Plotly : {len(plotly_capture_renderer.figures)} figures détectées.")
    for i, fig in enumerate(plotly_capture_renderer.figures):
        try:
            # Détecter le type de graphique dynamiquement
            chart_type = "bar"
            if fig.data:
                p_type = fig.data[0].type
                if p_type == "pie":
                    chart_type = "pie"
                elif p_type in ["scatter", "scattergl"]:
                    chart_type = "line"
            
            # Appliquer le layout Premium et le thème dynamique
            from utils.staffing_charts import apply_premium_layout, decode_plotly_bdata
            apply_premium_layout(fig, theme_mode, chart_type)

            # Convertir la figure Plotly en image PNG statique
            img_bytes = fig.to_image(format="png", width=800, height=500, scale=1.5)
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            
            # Récupérer le titre
            title = "Analyse graphique"
            if hasattr(fig, "layout") and fig.layout.title and fig.layout.title.text:
                title = fig.layout.title.text
                
            charts.append({
                "title": title,
                "type": chart_type,
                "base64": f"data:image/png;base64,{b64}",
                "plotly": decode_plotly_bdata(json.loads(pio.to_json(fig))),
                "chartjs": None
            })
        except Exception as e:
            logger.error(f"Erreur de capture de la figure Plotly {i}: {e}")
            
    # Réinitialiser la liste
    plotly_capture_renderer.figures = []
    return charts


def run_excel_agent(question: str, dataframes: Dict[str, pd.DataFrame], history: Optional[list] = None, theme_mode: str = "light") -> Dict[str, Any]:
    """Exécute l'agent Pandas sur la question posée."""
    logger.info(f"❓ Question Excel : {question}")
    
    # Réinitialiser les figures Plotly
    plotly_capture_renderer.figures = []
    
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    
    # Tout nettoyer avant l'exécution
    plt.close("all")

    agent = get_pandas_agent(dataframes)
    
    history_context = ""
    if history:
        history_context = "\n\n══════════════════════════════════════════════\nHISTORIQUE DES ÉCHANGES RÉCENTS :\n══════════════════════════════════════════════\n"
        for h in history[-8:]:
            role = "Utilisateur" if h.get("role") == "user" else "Assistant"
            content = h.get("content", "")
            if len(content) > 300:
                content = content[:300] + "..."
            history_context += f"- {role} : {content}\n"

    # Si l'utilisateur veut un graphe, on force explicitement le prompt à utiliser Plotly Express
    lower_q = question.lower()
    if any(kw in lower_q for kw in ["graphe", "graphique", "chart", "plot", "barre", "courbe", "diagramme", "barchart", "piechart"]):
        question_extended = (
            question + history_context +
            "\n\nIMPORTANT : Puisque l'utilisateur demande explicitement un graphique, "
            "tu DOIS impérativement écrire du code Python pour tracer ce graphique (ex: bar, pie ou line chart) "
            "à l'aide de la bibliothèque Plotly Express (import plotly.express as px) et appeler fig.show() à la fin de ton code. "
            "Ne te contente pas d'écrire des tableaux ou du texte."
        )
    else:
        question_extended = question + history_context

    try:
        result = agent.invoke({"input": question_extended})
        
        if isinstance(result, dict):
            answer = result.get("output", "")
        else:
            answer = str(result)
            
        logger.info(f"✅ Réponse Excel ({len(answer)} caractères)")
        
        # Capture des graphiques dessinés (Plotly et Matplotlib)
        charts_plotly = _capture_plotly_figures(theme_mode)
        charts_matplotlib = _capture_matplotlib_figures()
        charts = charts_plotly + charts_matplotlib
        
        # Fallback: si aucun graphique n'a été détecté mais que la réponse ou la trajectoire contient du code python
        if not charts and any(kw in lower_q for kw in ["graphe", "graphique", "chart", "plot", "barre", "courbe", "diagramme", "barchart", "piechart"]):
            import re
            
            # Construire la trajectoire complète pour chercher du code
            full_trajectory = answer
            if isinstance(result, dict) and "intermediate_steps" in result:
                for action, obs in result["intermediate_steps"]:
                    full_trajectory += f"\n{getattr(action, 'tool_input', '')}\n{getattr(action, 'log', '')}\n{obs}"
            
            code_blocks = re.findall(r"```python\s*(.*?)\s*```", full_trajectory, re.DOTALL)
            if code_blocks:
                logger.info(f"🔍 Aucun graphique détecté mais {len(code_blocks)} bloc(s) de code Python trouvé(s) dans la trajectoire. Exécution en fallback...")
                for code in code_blocks:
                    try:
                        # Nettoyer le code des chargements de fichiers locaux fictifs
                        clean_lines = []
                        for line in code.splitlines():
                            if ("read_csv" in line or "read_excel" in line) and "df =" in line:
                                clean_lines.append("# " + line)
                            else:
                                clean_lines.append(line)
                        cleaned_code = "\n".join(clean_lines)

                        # Exécuter le code en injectant les dataframes dans le namespace
                        local_ns = {}
                        df_list = list(dataframes.values())
                        if len(df_list) == 1:
                            local_ns["df"] = df_list[0]
                        for name, df in dataframes.items():
                            local_ns[name] = df
                        
                        # Exécuter le code
                        exec(cleaned_code, globals(), local_ns)
                    except Exception as exec_err:
                        logger.warning(f"⚠️ Échec de l'exécution du code en fallback : {exec_err}")
                
                # Recapturer après exécution en fallback
                charts_plotly = _capture_plotly_figures(theme_mode)
                charts_matplotlib = _capture_matplotlib_figures()
                charts = charts_plotly + charts_matplotlib

        # Filtrer si non demandé
        if not any(kw in lower_q for kw in ["graphe", "graphique", "chart", "plot", "barre", "courbe", "diagramme", "barchart", "piechart"]):
            charts = []
            
        return {"answer": answer, "charts": charts}
    except Exception as e:
        logger.error(f"❌ Erreur agent Excel : {e}")
        plt.close("all")
        return {"answer": f"❌ Erreur lors de l'analyse Excel : {str(e)}", "charts": []}
