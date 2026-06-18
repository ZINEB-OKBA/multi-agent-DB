"""
utils/staffing_calculator.py
────────────────────────────────────────────────────────────────────
Calcule à partir des records extraits :
  - Coût total par employé / par mois / par projet
  - Rentabilité : gain ou perte (si CA facturable est connu)
  - Taux d'occupation mensuel (jours travaillés / jours ouvrés du mois)
  - Synthèse narrative pour le LLM
"""

import calendar
import logging
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Jours ouvrés moyens par mois (approximation si non calculé dynamiquement)
JOURS_OUVRES_MOIS = 21.0


# ══════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ══════════════════════════════════════════════════════════════════

def compute_staffing_analysis(
    records: List[Dict[str, Any]],
    employe_filter: Optional[str] = None,
    ca_facturable: Optional[float] = None,   # CA total facturé (si connu)
    cout_journalier_interne: Optional[float] = None,  # coût interne/jour (salaire+charges)
) -> Dict[str, Any]:
    """
    Paramètres
    ----------
    records               : liste issue de staffing_extractor
    employe_filter        : filtrer sur un employé spécifique (None = tous)
    ca_facturable         : chiffre d'affaires facturé total (pour calculer gain/perte)
    cout_journalier_interne : coût réel journalier interne (pour calculer marge)

    Retourne
    --------
    {
      "par_employe":  { nom: {total_jours, total_cout, mois_detail, projets} },
      "par_mois":     { "YYYY-MM": {total_jours, total_cout} },
      "par_projet":   { nom_projet: {total_jours, total_cout} },
      "rentabilite":  { gain_net, marge_pct, statut } ou None,
      "synthese":     "texte narratif pour le LLM",
      "dataframe":    pd.DataFrame (pour les graphes),
    }
    """
    if not records:
        return {"erreur": "Aucune donnée de staffing disponible.", "dataframe": pd.DataFrame()}

    df = pd.DataFrame(records)

    # Filtrage par employé si demandé
    if employe_filter:
        mask = df["employe"].str.lower().str.contains(employe_filter.lower(), na=False)
        df = df[mask]
        if df.empty:
            return {
                "erreur": f"Employé '{employe_filter}' introuvable dans les données.",
                "dataframe": pd.DataFrame()
            }

    # Convert monthly salary to daily rate for calculations
    df["salaire_mensuel"] = df["tjm"]
    df["tjm"] = df["salaire_mensuel"] / JOURS_OUVRES_MOIS
    df["cout"] = df["jours"] * df["tjm"]

    # ── Par employé ───────────────────────────────────────────────
    par_employe: Dict[str, Any] = {}
    for emp, grp in df.groupby("employe"):
        mois_detail = []
        for mois, mg in grp.groupby("mois"):
            jours_mois = mg["jours"].sum()
            cout_mois  = mg["cout"].sum()
            taux_occ   = round(jours_mois / JOURS_OUVRES_MOIS * 100, 1)
            
            # CA (budget) facturable pour ce mois
            ca_mois = mg["budget"].sum() if "budget" in mg.columns else 0.0
            gain_mois = ca_mois - cout_mois
            marge_mois = (gain_mois / ca_mois * 100) if ca_mois else 0.0
            
            mois_detail.append({
                "mois":         mois,
                "jours":        round(jours_mois, 1),
                "cout":         round(cout_mois, 2),
                "taux_occ_pct": min(taux_occ, 100.0),
                "ca":           round(ca_mois, 2),
                "gain":         round(gain_mois, 2),
                "marge_pct":    round(marge_mois, 1),
            })

        par_employe[emp] = {
            "total_jours":  round(grp["jours"].sum(), 1),
            "total_cout":   round(grp["cout"].sum(), 2),
            "tjm_moyen":    round(grp["tjm"].mean(), 2), # Daily rate (calculated)
            "salaire_moyen": round(grp["salaire_mensuel"].mean(), 2), # Monthly salary (original)
            "projets":      grp["projet"].unique().tolist(),
            "mois_detail":  sorted(mois_detail, key=lambda x: x["mois"]),
            "nb_mois":      grp["mois"].nunique(),
        }

    # ── Par mois ──────────────────────────────────────────────────
    par_mois: Dict[str, Any] = {}
    for mois, grp in df.groupby("mois"):
        ca_mois = grp["budget"].sum() if "budget" in grp.columns else 0.0
        cout_mois = grp["cout"].sum()
        gain_mois = ca_mois - cout_mois
        marge_mois = (gain_mois / ca_mois * 100) if ca_mois else 0.0
        par_mois[mois] = {
            "total_jours": round(grp["jours"].sum(), 1),
            "total_cout":  round(cout_mois, 2),
            "ca":          round(ca_mois, 2),
            "gain":        round(gain_mois, 2),
            "marge_pct":   round(marge_mois, 1),
        }

    # ── Par projet ────────────────────────────────────────────────
    par_projet: Dict[str, Any] = {}
    for proj, grp in df.groupby("projet"):
        par_projet[proj] = {
            "total_jours": round(grp["jours"].sum(), 1),
            "total_cout":  round(grp["cout"].sum(), 2),
        }

    # ── Rentabilité ───────────────────────────────────────────────
    rentabilite = None
    total_cout  = round(df["cout"].sum(), 2)

    # Fallback sur la somme du budget_projet de l'Excel si aucun CA n'est mentionné dans la question
    if ca_facturable is None and "budget" in df.columns and df["budget"].sum() > 0:
        ca_facturable = df["budget"].sum()

    if ca_facturable is not None:
        gain_net  = round(ca_facturable - total_cout, 2)
        marge_pct = round(gain_net / ca_facturable * 100, 1) if ca_facturable else 0.0
        rentabilite = {
            "ca_facturable": ca_facturable,
            "cout_total":    total_cout,
            "gain_net":      gain_net,
            "marge_pct":     marge_pct,
            "statut":        "✅ Rentable" if gain_net >= 0 else "❌ En perte",
        }
    elif cout_journalier_interne is not None:
        total_jours      = df["jours"].sum()
        cout_interne_tot = round(total_jours * cout_journalier_interne, 2)
        gain_net         = round(total_cout - cout_interne_tot, 2)
        marge_pct        = round(gain_net / total_cout * 100, 1) if total_cout else 0.0
        rentabilite = {
            "cout_facture":       total_cout,
            "cout_interne_total": cout_interne_tot,
            "gain_net":           gain_net,
            "marge_pct":          marge_pct,
            "statut":             "✅ Rentable" if gain_net >= 0 else "❌ En perte",
        }

    # Détecter les années présentes dans les données
    annees_presentes = sorted(list({str(m)[:4] for m in df["mois"] if pd.notna(m) and len(str(m)) >= 4}))
    annees_str = ", ".join(annees_presentes) if annees_presentes else "Non spécifiées"

    # ── Synthèse narrative ────────────────────────────────────────
    synthese = _build_synthese(par_employe, par_mois, rentabilite, employe_filter, annees_str)

    return {
        "par_employe":  par_employe,
        "par_mois":     par_mois,
        "par_projet":   par_projet,
        "rentabilite":  rentabilite,
        "synthese":     synthese,
        "dataframe":    df,
        "total_cout":   total_cout,
    }


# ══════════════════════════════════════════════════════════════════
# SYNTHÈSE NARRATIVE
# ══════════════════════════════════════════════════════════════════

def _build_synthese(
    par_employe: Dict,
    par_mois: Dict,
    rentabilite: Optional[Dict],
    employe_filter: Optional[str],
    annees_str: str,
) -> str:
    lines = []

    if employe_filter:
        lines.append(f"## Analyse de staffing — {employe_filter} (Année(s) : {annees_str})")
        for emp, data in par_employe.items():
            lines.append(f"\n### {emp}")
            lines.append(f"- **Jours travaillés** : {data['total_jours']} jours sur {data['nb_mois']} mois")
            lines.append(f"- **Salaire mensuel** : {data['salaire_moyen']} Dhs/mois")
            lines.append(f"- **Salaire journalier (TJM)** : {data['tjm_moyen']} Dhs/jour")
            lines.append(f"- **Coût calculé** : {data['total_cout']:,.2f} Dhs")
            lines.append(f"- **Projets** : {', '.join(data['projets'])}")

            lines.append("\n**Détail mensuel :**")
            lines.append("| Mois | Jours | Taux occupation | Coût | CA facturé | Gain net | Marge |")
            lines.append("|------|-------|-----------------|------|------------|----------|-------|")
            for m in data["mois_detail"]:
                statut = "🟢" if m["taux_occ_pct"] >= 80 else ("🟡" if m["taux_occ_pct"] >= 50 else "🔴")
                ca_str = f"{m['ca']:,.2f} Dhs" if m.get('ca', 0) > 0 else "Non spécifié"
                gain_str = f"{m['gain']:+,.2f} Dhs" if m.get('ca', 0) > 0 else "Non calculé"
                marge_str = f"{m['marge_pct']}%" if m.get('ca', 0) > 0 else "Non calculée"
                lines.append(
                    f"| {m['mois']} | {m['jours']}j | {statut} {m['taux_occ_pct']}% | {m['cout']:,.2f} Dhs | {ca_str} | {gain_str} | {marge_str} |"
                )
    else:
        lines.append(f"## Synthèse globale de staffing — {len(par_employe)} employé(s) (Année(s) : {annees_str})")
        lines.append("\n| Employé | Jours travaillés | Salaire mensuel | Coût calculé | Projets |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for emp, data in par_employe.items():
            lines.append(
                f"| **{emp}** | {data['total_jours']}j ({data['nb_mois']} mois) | {data['salaire_moyen']:,.2f} Dhs/mois | {data['total_cout']:,.2f} Dhs | {', '.join(data['projets'])} |"
            )

    if rentabilite:
        lines.append("\n## Rentabilité")
        lines.append(f"**Statut : {rentabilite['statut']}**")
        if "ca_facturable" in rentabilite:
            lines.append(f"- CA facturé : {rentabilite['ca_facturable']:,.2f} Dhs")
            lines.append(f"- Coût total : {rentabilite['cout_total']:,.2f} Dhs")
        elif "cout_interne_total" in rentabilite:
            lines.append(f"- Coût facturé client : {rentabilite['cout_facture']:,.2f} Dhs")
            lines.append(f"- Coût interne : {rentabilite['cout_interne_total']:,.2f} Dhs")
        lines.append(f"- **Gain net : {rentabilite['gain_net']:+,.2f} Dhs**")
        lines.append(f"- Marge : {rentabilite['marge_pct']}%")

    return "\n".join(lines)