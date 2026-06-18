"""
utils/staffing_charts.py
────────────────────────────────────────────────────────────────────
Génère les graphiques de staffing et les retourne sous deux formes :
  1. Base64 PNG  → pour l'affichage direct dans le chat Angular (img src)
  2. Dict Plotly → pour le composant Plotly/Chart.js Angular existant

Tous les graphiques sont générés à l'aide de Plotly Express.
"""

import base64
import json
import logging
from typing import Dict, Any, List, Optional

import pandas as pd
import plotly.express as px
import plotly.io as pio

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# DÉCODAGE RECURSIF DE BDATA (POUR LES GRAPHIQUES NON EXPLOITABLES)
# ══════════════════════════════════════════════════════════════════

def decode_plotly_bdata(obj):
    """
    Décode récursivement les données binaires base64 'bdata' de Plotly
    en listes Python standards pour éviter que Plotly.js ou Pydantic
    ne reçoivent des structures illisibles/incomplètes.
    """
    if isinstance(obj, dict):
        if "dtype" in obj and "bdata" in obj:
            try:
                import numpy as np
                data_bytes = base64.b64decode(obj["bdata"])
                arr = np.frombuffer(data_bytes, dtype=obj["dtype"])
                return arr.tolist()
            except Exception as e:
                logger.error(f"Erreur décodage bdata : {e}")
                return obj
        else:
            return {k: decode_plotly_bdata(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decode_plotly_bdata(x) for x in obj]
    return obj


# ══════════════════════════════════════════════════════════════════
# FONCTIONS EXIGÉES PAR L'UTILISATEUR (PREMIUM STYLING & JSON)
# ══════════════════════════════════════════════════════════════════

def generate_plotly_json(
    df_result: pd.DataFrame,
    chart_type: str,
    theme_mode: str,
    x_col: str = None,
    y_col: str = None
) -> str:
    """
    Génère un graphique Plotly Express formaté de manière premium sous forme de chaîne JSON,
    avec un thème dynamique (dark/light) et une détection automatique des colonnes.
    """
    if df_result.empty:
        raise ValueError("Le DataFrame fourni est vide.")

    # 1. Détection automatique des colonnes X et Y si non fournies
    if not x_col or not y_col:
        numeric_cols = df_result.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df_result.select_dtypes(include=['object', 'category', 'datetime']).columns.tolist()
        all_cols = df_result.columns.tolist()

        if not x_col:
            x_col = categorical_cols[0] if categorical_cols else all_cols[0]
            
        if not y_col:
            y_col = numeric_cols[0] if numeric_cols else [c for c in all_cols if c != x_col][0]

    # Palette de couleurs élégante
    color_palette = ["#1E3A8A", "#3B82F6", "#60A5FA", "#94A3B8", "#475569", "#0F172A"]

    # 2. Génération de la figure selon le type de graphique
    chart_type = chart_type.lower()
    if chart_type == "bar":
        fig = px.bar(
            df_result, 
            x=x_col, 
            y=y_col, 
            color_discrete_sequence=color_palette,
            template="plotly_white"
        )
    elif chart_type == "pie":
        fig = px.pie(
            df_result, 
            names=x_col, 
            values=y_col, 
            color_discrete_sequence=color_palette,
            template="plotly_white"
        )
    elif chart_type == "line":
        fig = px.line(
            df_result, 
            x=x_col, 
            y=y_col, 
            color_discrete_sequence=color_palette,
            template="plotly_white",
            markers=True
        )
    else:
        raise ValueError(f"Type de graphique '{chart_type}' non supporté. Choisissez parmi 'bar', 'pie' ou 'line'.")

    # 3. Application du style premium & thème
    apply_premium_layout(fig, theme_mode, chart_type)

    # 4. Sérialisation JSON avec décodage des bdata
    decoded_dict = decode_plotly_bdata(json.loads(pio.to_json(fig)))
    return json.dumps(decoded_dict)


def apply_premium_layout(fig, theme_mode: str, chart_type: str):
    """
    Applique le style Premium & Thème Dynamique (Dark/Light) sur une figure Plotly existante.
    """
    is_dark = theme_mode.lower() == "dark"
    bg_color = "#121212" if is_dark else "#FFFFFF"
    plot_bg_color = "#1E1E1E" if is_dark else "#F8F9FA"
    font_color = "#F3F4F6" if is_dark else "#1F2937"
    grid_color = "#2D3748" if is_dark else "#E5E7EB"
    
    fig.update_layout(
        font=dict(
            family="Inter, DM Sans, sans-serif",
            size=12,
            color=font_color
        ),
        paper_bgcolor=bg_color,
        plot_bgcolor=plot_bg_color,
        margin=dict(l=80, r=20, t=30, b=80),
        
        # Positionnement vertical de la légende à droite
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=font_color)
        )
    )

    if chart_type in ["bar", "line"]:
        fig.update_xaxes(
            showgrid=True,
            gridcolor=grid_color,
            zeroline=False,
            tickangle=45,  # Inclinaison à 45 degrés
            color=font_color
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor=grid_color,
            zeroline=True,
            zerolinecolor=grid_color,
            color=font_color
        )
    elif chart_type == "pie":
        fig.update_traces(hole=0.4, textinfo="percent+label")


# ══════════════════════════════════════════════════════════════════
# GÉNÉRATEUR PRINCIPAL — retourne tous les graphiques
# ══════════════════════════════════════════════════════════════════

def generate_staffing_charts(
    analysis: Dict[str, Any],
    employe_filter: Optional[str] = None,
    theme_mode: str = "light",
) -> List[Dict[str, Any]]:
    """
    Retourne une liste de graphiques de staffing formatés avec le thème choisi.
    """
    charts = []
    df: pd.DataFrame = analysis.get("dataframe", pd.DataFrame())

    if df.empty:
        return charts

    par_mois    = analysis.get("par_mois", {})
    par_projet  = analysis.get("par_projet", {})
    par_employe = analysis.get("par_employe", {})
    rentabilite = analysis.get("rentabilite")

    # 1. Occupation mensuelle (jours par mois)
    c = _chart_occupation_mensuelle(df, employe_filter, theme_mode)
    if c: charts.append(c)

    # 2. Coût mensuel (courbe)
    c = _chart_cout_mensuel(par_mois, theme_mode)
    if c: charts.append(c)

    # 3. Répartition par projet (camembert)
    c = _chart_repartition_projets(par_projet, theme_mode)
    if c: charts.append(c)

    # 4. TJM comparatif entre employés
    if len(par_employe) > 1:
        c = _chart_tjm_comparatif(par_employe, theme_mode)
        if c: charts.append(c)

    # 5. Rentabilité gain/perte
    if rentabilite:
        c = _chart_rentabilite(rentabilite, theme_mode)
        if c: charts.append(c)

    return charts


# ══════════════════════════════════════════════════════════════════
# HELPERS DE CONVERSION PLOTLY TO BASE64
# ══════════════════════════════════════════════════════════════════

def _plotly_to_base64(fig, width: int = 800, height: int = 500) -> str:
    """Export la figure Plotly en PNG Base64."""
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height, scale=1.5)
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        logger.error(f"Erreur de conversion de figure Plotly en base64 : {e}")
        return ""


# ══════════════════════════════════════════════════════════════════
# GRAPHIQUE 1 — Occupation mensuelle
# ══════════════════════════════════════════════════════════════════

def _chart_occupation_mensuelle(df: pd.DataFrame, employe_filter: Optional[str], theme_mode: str) -> Optional[Dict]:
    try:
        pivot = df.pivot_table(
            index="mois", columns="employe", values="jours", aggfunc="sum"
        ).fillna(0).sort_index().reset_index()

        df_melt = pivot.melt(id_vars=["mois"], value_vars=[c for c in pivot.columns if c != "mois"],
                             var_name="employe", value_name="jours")

        fig = px.bar(
            df_melt,
            x="mois",
            y="jours",
            color="employe",
            barmode="group",
            title="📅 Occupation mensuelle (jours travaillés)",
            labels={"jours": "Jours travaillés", "mois": "Mois", "employe": "Employé"},
            template="plotly_white"
        )
        
        # Ajouter des lignes de référence
        fig.add_hline(y=21, line_dash="dash", line_color="red", annotation_text="21j (100%)")
        fig.add_hline(y=17, line_dash="dot", line_color="orange", annotation_text="17j (80%)")

        apply_premium_layout(fig, theme_mode, "bar")
        b64 = _plotly_to_base64(fig, width=800, height=500)

        # Extraction des séries pour le format fallback chartjs
        months = list(pivot["mois"])
        datasets = []
        palette = ["#534AB7", "#27AE60", "#E67E22", "#E74C3C", "#3498DB"]
        for i, emp in enumerate([c for c in pivot.columns if c != "mois"]):
            datasets.append({
                "label": emp,
                "data": [round(v, 1) for v in pivot[emp].values],
                "backgroundColor": palette[i % len(palette)],
            })

        return {
            "title":  "Occupation mensuelle",
            "type":   "bar",
            "base64": b64,
            "plotly": decode_plotly_bdata(json.loads(pio.to_json(fig))),
            "chartjs": {
                "type": "bar",
                "data": {"labels": months, "datasets": datasets},
                "options": {
                    "responsive": True,
                    "plugins": {"title": {"display": True, "text": "Occupation mensuelle (jours)"}}
                }
            }
        }
    except Exception as e:
        logger.error(f"Erreur chart occupation : {e}")
        return None


# ══════════════════════════════════════════════════════════════════
# GRAPHIQUE 2 — Coût mensuel (courbe)
# ══════════════════════════════════════════════════════════════════

def _chart_cout_mensuel(par_mois: Dict, theme_mode: str) -> Optional[Dict]:
    try:
        mois_sorted = sorted(par_mois.keys())
        couts = [par_mois[m]["total_cout"] for m in mois_sorted]
        df_cout = pd.DataFrame({"Mois": mois_sorted, "Coût (Dhs)": couts})

        fig = px.line(
            df_cout,
            x="Mois",
            y="Coût (Dhs)",
            title="💰 Évolution du coût mensuel (Dhs)",
            markers=True,
            template="plotly_white"
        )
        # Couleur personnalisée
        fig.update_traces(line_color="#534AB7", marker=dict(size=8, color="#534AB7", symbol="circle"))

        apply_premium_layout(fig, theme_mode, "line")
        b64 = _plotly_to_base64(fig, width=800, height=400)

        return {
            "title":  "Coût mensuel",
            "type":   "line",
            "base64": b64,
            "plotly": decode_plotly_bdata(json.loads(pio.to_json(fig))),
            "chartjs": {
                "type": "line",
                "data": {
                    "labels": mois_sorted,
                    "datasets": [{
                        "label": "Coût mensuel (Dhs)",
                        "data":  couts,
                        "borderColor": "#534AB7",
                        "fill": True,
                        "tension": 0.3,
                    }]
                }
            }
        }
    except Exception as e:
        logger.error(f"Erreur chart coût mensuel : {e}")
        return None


# ══════════════════════════════════════════════════════════════════
# GRAPHIQUE 3 — Répartition coût par projet (camembert)
# ══════════════════════════════════════════════════════════════════

def _chart_repartition_projets(par_projet: Dict, theme_mode: str) -> Optional[Dict]:
    if len(par_projet) < 2:
        return None
    try:
        labels = list(par_projet.keys())
        values = [par_projet[p]["total_cout"] for p in labels]
        df_proj = pd.DataFrame({"Projet": labels, "Coût": values})

        fig = px.pie(
            df_proj,
            names="Projet",
            values="Coût",
            title="🗂️ Répartition du coût par projet",
            template="plotly_white"
        )

        apply_premium_layout(fig, theme_mode, "pie")
        b64 = _plotly_to_base64(fig, width=600, height=500)

        palette = ["#534AB7","#27AE60","#E67E22","#E74C3C","#3498DB","#9B59B6","#1ABC9C"]
        return {
            "title":  "Répartition par projet",
            "type":   "pie",
            "base64": b64,
            "plotly": decode_plotly_bdata(json.loads(pio.to_json(fig))),
            "chartjs": {
                "type": "pie",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "data": values,
                        "backgroundColor": palette[:len(labels)]
                    }]
                }
            }
        }
    except Exception as e:
        logger.error(f"Erreur chart projets : {e}")
        return None


# ══════════════════════════════════════════════════════════════════
# GRAPHIQUE 4 — TJM comparatif
# ══════════════════════════════════════════════════════════════════

def _chart_tjm_comparatif(par_employe: Dict, theme_mode: str) -> Optional[Dict]:
    try:
        emps = list(par_employe.keys())
        tjms = [par_employe[e].get("salaire_moyen", par_employe[e]["tjm_moyen"]) for e in emps]
        df_tjm = pd.DataFrame({"Employé": emps, "Salaire": tjms})

        fig = px.bar(
            df_tjm,
            x="Salaire",
            y="Employé",
            orientation="h",
            title="💼 Salaire mensuel comparatif par employé",
            labels={"Salaire": "Salaire mensuel (Dhs/mois)", "Employé": "Employé"},
            template="plotly_white"
        )
        fig.update_traces(marker_color="#534AB7")

        apply_premium_layout(fig, theme_mode, "bar")
        b64 = _plotly_to_base64(fig, width=800, height=400)

        return {
            "title":  "Salaire mensuel comparatif",
            "type":   "bar",
            "base64": b64,
            "plotly": decode_plotly_bdata(json.loads(pio.to_json(fig))),
            "chartjs": {
                "type": "bar",
                "data": {
                    "labels": emps,
                    "datasets": [{
                        "label": "Salaire mensuel (Dhs/mois)",
                        "data": tjms,
                        "backgroundColor": "#534AB7",
                    }]
                }
            }
        }
    except Exception as e:
        logger.error(f"Erreur chart TJM : {e}")
        return None


# ══════════════════════════════════════════════════════════════════
# GRAPHIQUE 5 — Rentabilité (gain / perte)
# ══════════════════════════════════════════════════════════════════

def _chart_rentabilite(rentabilite: Dict, theme_mode: str) -> Optional[Dict]:
    try:
        if "ca_facturable" in rentabilite:
            labels = ["CA Facturé", "Coût Total", "Gain Net"]
            values = [
                rentabilite["ca_facturable"],
                rentabilite["cout_total"],
                rentabilite["gain_net"],
            ]
        else:
            labels = ["Coût Facturé", "Coût Interne", "Gain Net"]
            values = [
                rentabilite["cout_facture"],
                rentabilite["cout_interne_total"],
                rentabilite["gain_net"],
            ]

        df_rent = pd.DataFrame({"Catégorie": labels, "Montant (Dhs)": values})

        fig = px.bar(
            df_rent,
            x="Catégorie",
            y="Montant (Dhs)",
            color="Catégorie",
            title=f"📊 Rentabilité — {rentabilite['statut']}",
            labels={"Montant (Dhs)": "Montant (Dhs)", "Catégorie": "Rubrique"},
            template="plotly_white",
            color_discrete_map={
                "CA Facturé": "#27AE60",
                "Coût Facturé": "#27AE60",
                "Coût Total": "#E74C3C",
                "Coût Interne": "#E74C3C",
                "Gain Net": "#534AB7" if values[2] >= 0 else "#C0392B"
            }
        )

        apply_premium_layout(fig, theme_mode, "bar")
        b64 = _plotly_to_base64(fig, width=700, height=450)

        colors = ["#27AE60", "#E74C3C", "#534AB7" if values[2] >= 0 else "#C0392B"]
        return {
            "title":  "Rentabilité",
            "type":   "bar",
            "base64": b64,
            "plotly": decode_plotly_bdata(json.loads(pio.to_json(fig))),
            "chartjs": {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": "Montant (Dhs)",
                        "data": values,
                        "backgroundColor": colors,
                    }]
                }
            }
        }
    except Exception as e:
        logger.error(f"Erreur chart rentabilité : {e}")
        return None