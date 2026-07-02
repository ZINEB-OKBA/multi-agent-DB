"""
utils/loader_excel.py
─────────────────────────────────────────────────────────────────────────────
Charge les fichiers CSV/Excel dans des DataFrames Pandas.

Améliorations supplémentaires :
  ✅ tool-calling agent 
  ✅ prefix riche + schéma colonnes 
  ✅ Retry 429 avec backoff intelligent 
  ✅ Nettoyage code Python + tableaux Markdown 
  ✅ Capture Plotly + Matplotlib 
  ✅ MÉMOIRE par session : l'agent Excel se souvient des échanges passés
  ✅ 4 nouveaux graphiques automatiques (distribution, corrélation, tendance, heatmap)
  ✅ Détection intelligente du type de chart selon les données
"""

import io
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional

import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.io._base_renderers import ExternalRenderer

from langchain_experimental.agents import create_pandas_dataframe_agent
from utils.llm_factory import get_llm

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# CAPTURE PLOTLY
# ══════════════════════════════════════════════════════════════════════════════

class Base64ImageRenderer(ExternalRenderer):
    def __init__(self):
        self.figures: List = []

    def render(self, fig, **kwargs):
        self.figures.append(fig)


plotly_capture_renderer = Base64ImageRenderer()
pio.renderers["base64_capture"] = plotly_capture_renderer
pio.renderers.default = "base64_capture"


# ══════════════════════════════════════════════════════════════════════════════
# MÉMOIRE DE L'AGENT EXCEL (par project_id)
# ══════════════════════════════════════════════════════════════════════════════

class ExcelAgentMemory:
    """
    Mémoire glissante de l'agent Excel.
    Stocke les N derniers échanges (question + réponse courte) par project_id.
    Injecte automatiquement le contexte dans le prochain prompt.
    """
    _WINDOW = 10          # Nombre maximum d'échanges mémorisés
    _MAX_CHARS = 200      # Tronquer les réponses longues dans le résumé

    def __init__(self):
        self._store: Dict[int, deque] = {}

    def _key(self, project_id: int) -> deque:
        if project_id not in self._store:
            self._store[project_id] = deque(maxlen=self._WINDOW)
        return self._store[project_id]

    def add(self, project_id: int, question: str, answer: str):
        q = str(question)[:300]
        a = str(answer)[:self._MAX_CHARS]
        self._key(project_id).append({"q": q, "a": a})

    def get_context(self, project_id: int) -> str:
        history = self._key(project_id)
        if not history:
            return ""
        lines = ["\n\n══════ MÉMOIRE DES ÉCHANGES PRÉCÉDENTS ══════"]
        for i, turn in enumerate(history, 1):
            lines.append(f"[{i}] Utilisateur : {turn['q']}")
            lines.append(f"     Assistant  : {turn['a']}")
        lines.append("══════════════════════════════════════════════\n")
        return "\n".join(lines)

    def clear(self, project_id: int):
        self._store.pop(project_id, None)


EXCEL_MEMORY = ExcelAgentMemory()


# ══════════════════════════════════════════════════════════════════════════════
# AUTO-INSTALL DÉPENDANCES
# ══════════════════════════════════════════════════════════════════════════════

def _ensure_openpyxl():
    try:
        import openpyxl  # noqa
        return True
    except ImportError:
        logger.warning("⚠️  openpyxl absent — installation automatique...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "openpyxl", "tabulate", "--quiet"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            import openpyxl  # noqa
            logger.info("✅ openpyxl installé.")
            return True
        except Exception as e:
            logger.error(f"❌ Impossible d'installer openpyxl : {e}")
            return False


def _ensure_tabulate():
    try:
        import tabulate  # noqa
        return True
    except ImportError:
        logger.warning("⚠️  tabulate absent — installation automatique...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "tabulate", "--quiet"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            import tabulate  # noqa
            logger.info("✅ tabulate installé.")
            return True
        except Exception as e:
            logger.error(f"❌ Impossible d'installer tabulate : {e}")
            return False


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DATAFRAMES
# ══════════════════════════════════════════════════════════════════════════════

def load_dataframe(file_path: str) -> pd.DataFrame:
    suffix = Path(file_path).suffix.lower()
    logger.info(f"📊 Chargement : {file_path}")

    if suffix == ".csv":
        for enc in ("utf-8", "latin-1", "cp1252", "utf-8-sig"):
            try:
                df = pd.read_csv(file_path, encoding=enc)
                logger.info(f"   → {df.shape[0]}L × {df.shape[1]}C (encoding={enc})")
                return df
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Impossible de lire le CSV {file_path}")

    elif suffix in (".xlsx", ".xlsm", ".xltx", ".xltm"):
        _ensure_openpyxl()
        for engine in ["openpyxl", "calamine"]:
            try:
                df = pd.read_excel(file_path, engine=engine)
                logger.info(f"   → {df.shape[0]}L × {df.shape[1]}C (engine={engine})")
                return df
            except Exception as e:
                logger.warning(f"   ⚠️  Engine '{engine}' échoué : {e}")
        raise ImportError("Impossible de lire le xlsx — installe openpyxl : pip install openpyxl")

    elif suffix == ".xls":
        try:
            df = pd.read_excel(file_path, engine="xlrd")
            logger.info(f"   → {df.shape[0]}L × {df.shape[1]}C (engine=xlrd)")
            return df
        except Exception as e:
            raise ImportError(f"Impossible de lire le .xls — installe xlrd\nErreur : {e}")

    else:
        raise ValueError(f"Format non supporté : {suffix}")


def load_all_tables(tables_folder: str) -> Dict[str, pd.DataFrame]:
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
    _ensure_openpyxl()
    _ensure_tabulate()
    dataframes: Dict[str, pd.DataFrame] = {}
    for uf in uploaded_files:
        suffix = Path(uf.name).suffix.lower()
        if suffix not in (".csv", ".xlsx", ".xls", ".xlsm"):
            continue
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uf.read())
            tmp_path = tmp.name
        try:
            df = load_dataframe(tmp_path)
            dataframes[Path(uf.name).stem] = df
        except Exception as e:
            logger.error(f"❌ Erreur chargement {uf.name} : {e}")
            raise
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    return dataframes


# ══════════════════════════════════════════════════════════════════════════════
# GRAPHIQUES AUTOMATIQUES ENRICHIS
# ══════════════════════════════════════════════════════════════════════════════

def _decode_plotly_bdata(obj):
    """Décode récursivement les bdata binaires Plotly en listes Python."""
    if isinstance(obj, dict):
        if "dtype" in obj and "bdata" in obj:
            try:
                import numpy as np
                arr = np.frombuffer(base64.b64decode(obj["bdata"]), dtype=obj["dtype"])
                return arr.tolist()
            except Exception:
                return obj
        return {k: _decode_plotly_bdata(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_decode_plotly_bdata(x) for x in obj]
    return obj


PREMIUM_PALETTE = ["#534AB7", "#27AE60", "#E67E22", "#E74C3C", "#3498DB",
                   "#9B59B6", "#1ABC9C", "#F39C12", "#2C3E50", "#7F8C8D"]


def _apply_premium_layout(fig, theme_mode: str = "light", chart_type: str = "bar"):
    """Applique le style Premium sur une figure Plotly."""
    is_dark = theme_mode.lower() == "dark"
    bg       = "#121212" if is_dark else "#FFFFFF"
    plot_bg  = "#1E1E1E" if is_dark else "#F8F9FA"
    font_c   = "#F3F4F6" if is_dark else "#1F2937"
    grid_c   = "#2D3748" if is_dark else "#E5E7EB"

    fig.update_layout(
        font=dict(family="Inter, DM Sans, sans-serif", size=12, color=font_c),
        paper_bgcolor=bg, plot_bgcolor=plot_bg,
        margin=dict(l=50, r=20, t=50, b=120),
        legend=dict(orientation="h", yanchor="top", y=-0.3,
                    xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)",
                    font=dict(color=font_c)),
    )
    if chart_type in ("bar", "line"):
        fig.update_xaxes(showgrid=True, gridcolor=grid_c, zeroline=False,
                         tickangle=45, color=font_c)
        fig.update_yaxes(showgrid=True, gridcolor=grid_c, zeroline=True,
                         zerolinecolor=grid_c, color=font_c)
    elif chart_type == "pie":
        fig.update_traces(hole=0.4, textinfo="percent+label")


def _fig_to_chart_dict(fig, title: str, chart_type: str,
                        theme_mode: str = "light") -> Optional[Dict]:
    """Convertit une figure Plotly en dict prêt pour Angular."""
    try:
        _apply_premium_layout(fig, theme_mode, chart_type)
        img_bytes = fig.to_image(format="png", width=800, height=500, scale=1.5)
        b64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode()
        return {
            "title":   title,
            "type":    chart_type,
            "base64":  b64,
            "plotly":  _decode_plotly_bdata(json.loads(pio.to_json(fig))),
            "chartjs": None,
        }
    except Exception as e:
        logger.error(f"Erreur conversion figure → chart dict : {e}")
        return None


# ── Nouveau : graphiques automatiques sur le DataFrame ─────────────────────

def generate_auto_charts(
    dataframes: Dict[str, pd.DataFrame],
    theme_mode: str = "light",
) -> List[Dict]:
    """
    Génère automatiquement 4 types de graphiques pertinents selon le contenu du DataFrame.
    Appelé sans demande explicite, pour enrichir chaque réponse Excel avec des visuels.

    Graphiques générés (si colonnes compatibles) :
      1. Distribution numérique (histogramme ou box plot)
      2. Top 10 par colonne catégorielle × numérique (bar chart)
      3. Tendance temporelle (line chart) si colonne date/mois détectée
      4. Heatmap de corrélation entre colonnes numériques
    """
    charts: List[Dict] = []

    for df_name, df in dataframes.items():
        if df.empty:
            continue

        num_cols  = df.select_dtypes(include="number").columns.tolist()
        cat_cols  = df.select_dtypes(include=["object", "category"]).columns.tolist()
        date_cols = [c for c in df.columns
                     if any(kw in c.lower() for kw in
                            ["date", "mois", "month", "annee", "année", "year",
                             "periode", "période", "temps", "time"])]

        # 1. Distribution numérique — boxplot multi-colonnes
        if len(num_cols) >= 2:
            try:
                fig = go.Figure()
                for col in num_cols[:6]:
                    fig.add_trace(go.Box(y=df[col].dropna(), name=col,
                                         marker_color=PREMIUM_PALETTE[num_cols.index(col) % len(PREMIUM_PALETTE)]))
                fig.update_layout(title=f"📦 Distribution des variables numériques — {df_name}")
                c = _fig_to_chart_dict(fig, "Distribution numérique", "bar", theme_mode)
                if c:
                    charts.append(c)
            except Exception as e:
                logger.warning(f"Chart distribution : {e}")

        # 2. Top 10 — première col catégorielle × première col numérique
        if cat_cols and num_cols:
            try:
                x_col = cat_cols[0]
                y_col = num_cols[0]
                top10 = (df.groupby(x_col)[y_col].sum()
                           .nlargest(10).reset_index())
                fig = px.bar(top10, x=x_col, y=y_col,
                             title=f"🏆 Top 10 — {y_col} par {x_col} ({df_name})",
                             color=x_col,
                             color_discrete_sequence=PREMIUM_PALETTE,
                             template="plotly_white")
                c = _fig_to_chart_dict(fig, f"Top 10 {y_col}", "bar", theme_mode)
                if c:
                    charts.append(c)
            except Exception as e:
                logger.warning(f"Chart top10 : {e}")

        # 3. Tendance temporelle
        if date_cols and num_cols:
            try:
                d_col = date_cols[0]
                y_col = num_cols[0]
                trend = (df.groupby(d_col)[y_col].sum()
                           .reset_index().sort_values(d_col))
                fig = px.line(trend, x=d_col, y=y_col,
                              title=f"📈 Tendance — {y_col} par {d_col} ({df_name})",
                              markers=True, template="plotly_white",
                              color_discrete_sequence=[PREMIUM_PALETTE[0]])
                c = _fig_to_chart_dict(fig, f"Tendance {y_col}", "line", theme_mode)
                if c:
                    charts.append(c)
            except Exception as e:
                logger.warning(f"Chart tendance : {e}")

        # 4. Heatmap corrélation
        if len(num_cols) >= 3:
            try:
                corr = df[num_cols[:8]].corr().round(2)
                fig = go.Figure(go.Heatmap(
                    z=corr.values.tolist(),
                    x=corr.columns.tolist(),
                    y=corr.index.tolist(),
                    colorscale="RdBu", zmid=0,
                    text=corr.values.round(2).tolist(),
                    texttemplate="%{text}",
                ))
                fig.update_layout(
                    title=f"🔥 Corrélation entre variables — {df_name}",
                    paper_bgcolor="#FFFFFF" if theme_mode == "light" else "#121212",
                    font=dict(color="#1F2937" if theme_mode == "light" else "#F3F4F6"),
                    margin=dict(l=50, r=20, t=50, b=50),
                )
                c = _fig_to_chart_dict(fig, "Heatmap corrélation", "bar", theme_mode)
                if c:
                    charts.append(c)
            except Exception as e:
                logger.warning(f"Chart heatmap : {e}")

    logger.info(f"📊 {len(charts)} graphique(s) automatique(s) générés")
    return charts


# ══════════════════════════════════════════════════════════════════════════════
# NETTOYAGE CODE PYTHON
# ══════════════════════════════════════════════════════════════════════════════

def sanitize_python_code(code: str) -> str:
    code = code.strip()
    match = re.search(r"```(?:python)?\n?(.*?)\n?```", code, re.DOTALL)
    if match:
        return match.group(1).strip()
    lines, cleaned = code.splitlines(), []
    for line in lines:
        s = line.strip()
        if s.startswith("(") and s.endswith(")"):
            continue
        if any(s.startswith(kw) for kw in
               ["Note :", "Note:", "Remarque :", "Remarque:", "Attention :"]):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


# ══════════════════════════════════════════════════════════════════════════════
# AGENT PANDAS
# ══════════════════════════════════════════════════════════════════════════════

def get_pandas_agent(dataframes: Dict[str, pd.DataFrame], verbose: bool = True):
    """Crée un agent LangChain Pandas tool-calling avec prefix détaillé."""
    _ensure_tabulate()

    llm      = get_llm(temperature=0.0)
    df_list  = list(dataframes.values())
    df_input = df_list[0] if len(df_list) == 1 else df_list

    logger.info(f"🤖 Création agent Pandas ({len(df_list)} DataFrame(s))")

    if isinstance(df_input, list):
        schema_info = ""
        for i, d in enumerate(df_input):
            cols = ", ".join([f"`{col}` ({dtype})"
                              for col, dtype in zip(d.columns, d.dtypes)])
            schema_info += f"- DataFrame {i} : {cols}\n"
    else:
        cols_list = ", ".join([f"`{col}` ({dtype})"
                               for col, dtype in zip(df_input.columns, df_input.dtypes)])
        schema_info = f"Colonnes de `df` : {cols_list}"

    prefix_str = (
        "Tu es un Expert Data Analyst. La variable `df` contient déjà les données réelles.\n"
        "INTERDICTION ABSOLUE de redéfinir `df` avec pd.DataFrame() dans ton code.\n\n"
        f"STRUCTURE DES DONNÉES :\n{schema_info}\n"
        "⚠️ Respecte STRICTEMENT la casse exacte des colonnes listées ci-dessus.\n\n"
        "CONSIGNES :\n"
        "1. Utilise directement `df` pour tes calculs.\n"
        "2. Présente tes résultats en tableaux Markdown COMPACTS (pas d'espaces de padding).\n"
        "3. Si l'utilisateur demande un graphique, utilise Plotly Express et appelle fig.show().\n"
        "4. Réponds EXCLUSIVEMENT en français.\n"
        "5. N'invente jamais de données — analyse uniquement ce qui est dans `df`.\n"
        "6. Si la question fait référence à un échange précédent (ex: 'ce résultat', 'ces données'),\n"
        "   utilise le contexte mémorisé fourni dans le prompt.\n"
        "7. Sois extrêmement rigoureux dans l'interprétation des résultats statistiques et des agrégations "
        "(comme groupby ou crosstab). Ne confonds pas des colonnes catégorielles contenant des identifiants ou noms "
        "de groupes (ex: des terminaux 'T1', 'T2', 'T3' indiquant l'emplacement d'un stand) avec des compteurs de quantités physiques.\n"
        "8. Évite absolument d'afficher de grands tableaux bruts (comme des crosstabs ou des tables entières de plus de 10 lignes) "
        "pour essayer de les lire ou de les compter manuellement dans ta pensée. Utilise toujours des opérations d'agrégation de Pandas "
        "(comme .value_counts(), .groupby(), .sum(), .mean(), .nunique()) pour obtenir directement les compteurs ou les résumés sous forme "
        "numérique consolidée avant de formuler ta réponse finale.\n"
    )

    agent = create_pandas_dataframe_agent(
        llm=llm,
        df=df_input,
        agent_type="tool-calling",
        verbose=verbose,
        allow_dangerous_code=True,
        max_iterations=10,
        handle_parsing_errors=True,
        prefix=prefix_str,
    )

    # Nettoyage automatique du code
    for tool in agent.tools:
        if tool.name == "python_repl_ast":
            original_run = tool._run

            def patched_run(query: str, *args, _orig=original_run, **kwargs):
                sanitized = sanitize_python_code(query)
                logger.info(f"🧹 Code nettoyé :\n{sanitized}")
                return _orig(sanitized, *args, **kwargs)

            tool._run = patched_run

    return agent


# ══════════════════════════════════════════════════════════════════════════════
# CAPTURE DES FIGURES
# ══════════════════════════════════════════════════════════════════════════════

def _capture_matplotlib_figures(theme_mode: str = "light") -> List[Dict]:
    charts: List[Dict] = []
    fignums = plt.get_fignums()
    logger.info(f"📊 Matplotlib : {len(fignums)} figures")
    for num in fignums:
        try:
            fig = plt.figure(num)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            b64 = "data:image/png;base64," + base64.b64encode(buf.read()).decode()
            title = "Analyse graphique"
            if fig.axes and fig.axes[0].get_title():
                title = fig.axes[0].get_title()
            charts.append({"title": title, "type": "bar",
                           "base64": b64, "plotly": None, "chartjs": None})
        except Exception as e:
            logger.error(f"Erreur capture matplotlib {num}: {e}")
    plt.close("all")
    return charts


def _capture_plotly_figures(theme_mode: str = "light") -> List[Dict]:
    charts: List[Dict] = []
    logger.info(f"📊 Plotly : {len(plotly_capture_renderer.figures)} figures")
    for i, fig in enumerate(plotly_capture_renderer.figures):
        try:
            chart_type = "bar"
            if fig.data:
                pt = fig.data[0].type
                if pt == "pie":
                    chart_type = "pie"
                elif pt in ("scatter", "scattergl"):
                    chart_type = "line"

            try:
                from utils.staffing_charts import apply_premium_layout, decode_plotly_bdata
                apply_premium_layout(fig, theme_mode, chart_type)
                plotly_json = decode_plotly_bdata(json.loads(pio.to_json(fig)))
            except Exception:
                _apply_premium_layout(fig, theme_mode, chart_type)
                plotly_json = _decode_plotly_bdata(json.loads(pio.to_json(fig)))

            img_bytes = fig.to_image(format="png", width=800, height=500, scale=1.5)
            b64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode()

            title = "Analyse graphique"
            if hasattr(fig, "layout") and fig.layout.title and fig.layout.title.text:
                title = fig.layout.title.text

            charts.append({"title": title, "type": chart_type,
                           "base64": b64, "plotly": plotly_json, "chartjs": None})
        except Exception as e:
            logger.error(f"Erreur capture plotly {i}: {e}")

    plotly_capture_renderer.figures = []
    return charts


# ══════════════════════════════════════════════════════════════════════════════
# RETRY 429
# ══════════════════════════════════════════════════════════════════════════════

def _extract_retry_seconds(error_message: str) -> int:
    m = re.search(r'in (?:(\d+)m)?(\d+(?:\.\d+)?)s', error_message)
    if m:
        return int(int(m.group(1) or 0) * 60 + float(m.group(2)))
    return 60


def _clean_markdown_table(answer: str) -> str:
    lines, cleaned = answer.split("\n"), []
    for line in lines:
        if "|" in line:
            line = re.sub(r"\s*\|\s*", "|", line)
            line = line.replace("|", " | ").strip()
            if "---" in line:
                line = re.sub(r"\s*-\s*", "-", line)
        cleaned.append(line)
    return "\n".join(cleaned)


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def run_excel_agent(
    question:      str,
    dataframes:    Dict[str, pd.DataFrame],
    history:       Optional[List[Dict]] = None,
    theme_mode:    str = "light",
    max_retries:   int = 2,
    project_id:    int = 0,
    enable_charts: bool = False,   # ← AJOUT : False par défaut
) -> Dict[str, Any]:

    """
    Exécute l'agent Pandas et retourne {"answer": str, "charts": list}.

    RÈGLE GRAPHIQUES :
      - Les graphiques sont générés UNIQUEMENT si l'utilisateur en demande
        explicitement (mots-clés : graphe, graphique, chart, plot, barre…).
      - Le graphique généré est CONTEXTUEL à la question posée (filtré par
        l'agent lui-même via le code Plotly qu'il écrit).
      - Aucun graphique automatique non demandé n'est ajouté.
    """
    logger.info(f"❓ Question Excel (projet {project_id}) : {question}")

    plotly_capture_renderer.figures = []
    plt.close("all")

    # ── Mémoire propre à cet agent Excel ──────────────────────────────────────
    memory_ctx = EXCEL_MEMORY.get_context(project_id)

    # ── Contexte historique (échanges courants de la session) ─────────────────
    history_context = ""
    if history:
        history_context = "\n\n══════ HISTORIQUE SESSION ══════\n"
        for h in history[-8:]:
            role    = "Utilisateur" if h.get("role") == "user" else "Assistant"
            content = str(h.get("content", ""))[:300]
            history_context += f"- {role} : {content}\n"

    lower_q = question.lower()
    chart_kws = ["graphe", "graphique", "chart", "plot", "barre",
                 "courbe", "diagramme", "barchart", "piechart", "visualise",
                 "affiche", "montre", "trace"]
    
    # ── MODIFICATION : is_chart_request uniquement si enable_charts=True ──
    is_chart_request = enable_charts and any(kw in lower_q for kw in chart_kws)

    chart_injection = ""
    if is_chart_request:
        chart_injection = (
            "\n\nIMPORTANT : L'utilisateur demande UN graphique CONTEXTUEL à sa question. "
            "Utilise Plotly Express (import plotly.express as px) et appelle fig.show() à la fin. "
            "Le graphique doit représenter UNIQUEMENT les données liées à la question posée. "
            "Filtre d'abord, trace ensuite."
        )


    question_extended = memory_ctx + question + history_context + chart_injection

    agent = get_pandas_agent(dataframes)

    for attempt in range(max_retries + 1):
        try:
            result = agent.invoke({"input": question_extended})
            answer = (result.get("output", str(result))
                      if isinstance(result, dict) else str(result))
            answer = _clean_markdown_table(answer)
            logger.info(f"✅ Réponse Excel ({len(answer)} chars)")

            # ── Mémoriser l'échange ────────────────────────────────────────────
            EXCEL_MEMORY.add(project_id, question, answer)

            # ── Capture graphiques explicitement demandés ──────────────────────
            charts: List[Dict] = []
            if is_chart_request:
                charts = (_capture_plotly_figures(theme_mode)
                          + _capture_matplotlib_figures(theme_mode))

                # Fallback : blocs de code dans la trajectoire
                if not charts:
                    full_traj = answer
                    if isinstance(result, dict) and "intermediate_steps" in result:
                        for action, obs in result["intermediate_steps"]:
                            full_traj += (f"\n{getattr(action, 'tool_input', '')}"
                                         f"\n{obs}")
                    code_blocks = re.findall(
                        r"```python\s*(.*?)\s*```", full_traj, re.DOTALL)
                    if code_blocks:
                        logger.info(f"🔍 Fallback : {len(code_blocks)} bloc(s) de code")
                        local_ns: Dict = {}
                        df_list = list(dataframes.values())
                        if len(df_list) == 1:
                            local_ns["df"] = df_list[0]
                        for name, df in dataframes.items():
                            local_ns[name] = df
                        for code in code_blocks:
                            try:
                                exec(sanitize_python_code(code), globals(), local_ns)
                            except Exception as exec_err:
                                logger.warning(f"⚠️ Fallback exec : {exec_err}")
                        charts = (_capture_plotly_figures(theme_mode)
                                  + _capture_matplotlib_figures(theme_mode))

            return {"answer": answer, "charts": charts}

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate_limit_exceeded" in error_str:
                wait_sec = min(_extract_retry_seconds(error_str), 35)
                if attempt < max_retries:
                    logger.warning(
                        f"⏳ [Tentative {attempt + 1}] Rate limit 429 — attente {wait_sec}s...")
                    time.sleep(wait_sec)
                    continue
                return {
                    "answer": "⚠️ **Quota Groq temporairement atteint.**\nRéessayez dans quelques secondes.",
                    "charts": [],
                }

            logger.error(f"❌ Erreur agent Excel : {e}")
            plt.close("all")
            return {"answer": f"❌ Erreur lors de l'analyse : {str(e)}", "charts": []}

    return {"answer": "❌ Nombre maximum de tentatives atteint.", "charts": []}