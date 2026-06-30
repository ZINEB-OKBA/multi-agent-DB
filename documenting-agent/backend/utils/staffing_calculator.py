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
import re
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
    projet_filter: Optional[str] = None,
    ca_facturable: Optional[float] = None,   # CA total facturé (si connu)
    cout_journalier_interne: Optional[float] = None,  # coût interne/jour (salaire+charges)
    question: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Paramètres
    ----------
    records               : liste issue de staffing_extractor
    employe_filter        : filtrer sur un employé spécifique (None = tous)
    projet_filter         : filtrer sur un projet spécifique (None = tous)
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
      "dataframe":    pd.DataFrame (pour les graphiques),
    }
    """
    if not records:
        return {"erreur": "Aucune donnée de staffing disponible.", "dataframe": pd.DataFrame()}

    df = pd.DataFrame(records)
    # 1. Create a copy of the unfiltered DataFrame for project-level stats
    df_unfiltered = df.copy()
    df_unfiltered["salaire_mensuel"] = df_unfiltered["tjm"] * JOURS_OUVRES_MOIS
    df_unfiltered["cout"] = df_unfiltered["jours"] * df_unfiltered["tjm"]

    # Filtrage par employé si demandé
    if employe_filter:
        if isinstance(employe_filter, list):
            mask = pd.Series(False, index=df.index)
            for emp_f in employe_filter:
                mask |= df["employe"].str.lower().str.contains(emp_f.lower(), regex=False, na=False)
            df = df[mask]
            if df.empty:
                return {
                    "erreur": f"Employés {employe_filter} introuvables dans les données.",
                    "dataframe": pd.DataFrame()
                }
        else:
            mask = df["employe"].str.lower().str.contains(employe_filter.lower(), regex=False, na=False)
            df = df[mask]
            if df.empty:
                return {
                    "erreur": f"Employé '{employe_filter}' introuvable dans les données.",
                    "dataframe": pd.DataFrame()
                }

    # Filtrage par projet si demandé
    if projet_filter:
        mask = df["projet"].str.lower().str.contains(projet_filter.lower(), regex=False, na=False)
        df = df[mask]
        if df.empty:
            return {
                "erreur": f"Projet '{projet_filter}' introuvable pour cet employé.",
                "dataframe": pd.DataFrame()
            }

    # df["tjm"] est déjà le coût journalier (CJM) extrait. On reconstruit le salaire mensuel.
    df["salaire_mensuel"] = df["tjm"] * JOURS_OUVRES_MOIS
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
            ca_mois = sum(pgrp["budget"].max() for _, pgrp in mg.groupby("projet")) if "budget" in mg.columns else 0.0
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

        projets_detail = []
        for proj, pgrp in grp.groupby("projet"):
            projets_detail.append({
                "projet": proj,
                "jours": round(pgrp["jours"].sum(), 1),
                "cout": round(pgrp["cout"].sum(), 2)
            })

        par_employe[emp] = {
            "total_jours":  round(grp["jours"].sum(), 1),
            "total_cout":   round(grp["cout"].sum(), 2),
            "total_ca":     round(sum(pgrp["budget"].max() for _, pgrp in grp.groupby("projet")), 2),
            "tjm_moyen":    round(grp["tjm"].mean(), 2), # Daily rate (calculated)
            "salaire_moyen": round(grp["salaire_mensuel"].mean(), 2), # Monthly salary (original)
            "projets":      grp["projet"].unique().tolist(),
            "projet_detail": projets_detail,
            "mois_detail":  sorted(mois_detail, key=lambda x: x["mois"]),
            "nb_mois":      grp["mois"].nunique(),
            "profil":         grp["profil"].iloc[0] if "profil" in grp.columns else "",
            "date_demarrage": grp["date_demarrage"].iloc[0] if "date_demarrage" in grp.columns else "",
            "anciennete":     grp["anciennete"].iloc[0] if "anciennete" in grp.columns else "",
            "localisation":   grp["localisation"].iloc[0] if "localisation" in grp.columns else "",
        }

    # ── Par mois ──────────────────────────────────────────────────
    par_mois: Dict[str, Any] = {}
    for mois, grp in df.groupby("mois"):
        ca_mois = sum(pgrp["budget"].max() for _, pgrp in grp.groupby("projet")) if "budget" in grp.columns else 0.0
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
    projects_to_show = df["projet"].unique() if not df.empty else []
    for proj, grp in df_unfiltered.groupby("projet"):
        if proj not in projects_to_show:
            continue
        ca_proj = grp["budget"].max() if "budget" in grp.columns and len(grp) > 0 else 0.0
        cout_proj = grp["cout"].sum()
        gain_proj = ca_proj - cout_proj
        marge_proj = (gain_proj / ca_proj * 100) if ca_proj else 0.0
        roi_proj = (gain_proj / cout_proj * 100) if cout_proj else 0.0
        par_projet[proj] = {
            "total_jours": round(grp["jours"].sum(), 1),
            "total_cout":  round(cout_proj, 2),
            "ca":          round(ca_proj, 2),
            "gain":        round(gain_proj, 2),
            "marge_pct":   round(marge_proj, 1),
            "roi_pct":     round(roi_proj, 1),
        }

    # ── Rentabilité ───────────────────────────────────────────────
    rentabilite = None
    total_cout  = round(df["cout"].sum(), 2)

    # Fallback sur la somme du budget_projet de l'Excel si aucun CA n'est mentionné dans la question
    is_ca_fallback = False
    if ca_facturable is None and "budget" in df.columns and len(df) > 0:
        ca_facturable = sum(pgrp["budget"].max() for _, pgrp in df.groupby("projet"))
        is_ca_fallback = True

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

    # Afficher la rentabilité globale uniquement si le CA a été explicitement spécifié par l'utilisateur
    show_global_rentability = (ca_facturable is not None and not is_ca_fallback)

    # ── Synthèse narrative ────────────────────────────────────────
    synthese = _build_synthese(
        par_employe,
        par_mois,
        rentabilite,
        employe_filter,
        annees_str,
        show_global_rentability=show_global_rentability,
        projet_filter=projet_filter,
        par_projet=par_projet,
        question=question
    )

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
    show_global_rentability: bool = False,
    projet_filter: Optional[str] = None,
    par_projet: Optional[Dict] = None,
    question: Optional[str] = None,
) -> str:
    lines = []

    # Détecter si la question porte sur des données financières ou un bilan global
    is_financial = True
    if question:
        q_low = question.lower()
        is_financial = any(kw in q_low for kw in [
            "coût", "cout", "ca", "budget", "gain", "perte", "marge", "rentabilité", 
            "rentable", "roi", "salaire", "cjm", "tjm", "paye", "paie", "rémunération", 
            "remuneration", "chiffre", "rapport", "synthese", "bilan", "financier", "financiere"
        ])
        # Si c'est une question simple de comptage d'employés ou de projets, ce n'est pas financier
        if any(kw in q_low for kw in ["combien", "nombre", "liste"]) and not any(kw in q_low for kw in ["cout", "coût", "salaire", "cjm", "tjm", "budget"]):
            is_financial = False

    if employe_filter:
        header = ""
        matched_emps = []
        if isinstance(employe_filter, list):
            header = f"Analyse de staffing — " + ", ".join(employe_filter)
            for emp in par_employe.keys():
                if emp in employe_filter:
                    matched_emps.append(emp)
        else:
            header = f"Analyse de staffing — {employe_filter}"
            filter_lower = employe_filter.lower().strip()
            for emp in par_employe.keys():
                emp_clean = re.sub(r"\s*\(id:\s*\d+\)", "", emp, flags=re.IGNORECASE).lower().strip()
                if emp_clean in filter_lower or filter_lower in emp_clean or filter_lower in emp.lower():
                    matched_emps.append(emp)
        
        # Fallback si aucun match précis
        if not matched_emps:
            matched_emps = list(par_employe.keys())

        if projet_filter:
            header += f" sur le projet {projet_filter}"
        lines.append(f"## {header}")

        for emp in matched_emps:
            data = par_employe[emp]
            lines.append(f"\n### {emp}")
            lines.append(f"- **Jours travaillés** : {data['total_jours']} jours sur {data['nb_mois']} mois")
            if is_financial:
                lines.append(f"- **Salaire mensuel** : {data['salaire_moyen']} Dhs/mois")
                lines.append(f"- **Coût journalier moyen (CJM)** : {data['tjm_moyen']} Dhs/jour")
                lines.append(f"- **Coût calculé** : {data['total_cout']:,.2f} Dhs")
            lines.append(f"- **Projets** : {', '.join(data['projets'])}")

            if is_financial and "projet_detail" in data:
                lines.append("\n**Détail du coût de l'employé par projet :**")
                lines.append("| Projet | Jours travaillés | Coût de l'employé |")
                lines.append("| :--- | :---: | :---: |")
                for pdet in data["projet_detail"]:
                    lines.append(f"| **{pdet['projet']}** | {pdet['jours']}j | {pdet['cout']:,.2f} Dhs |")

            if "mois_detail" in data:
                lines.append("\n**Détail mensuel :**")
                if is_financial:
                    lines.append("| Mois | Jours travaillés | Taux d'occupation | Coût de la ressource |")
                    lines.append("|------|------------------|-------------------|----------------------|")
                    for m in data["mois_detail"]:
                        statut = "🟢" if m["taux_occ_pct"] >= 80 else ("🟡" if m["taux_occ_pct"] >= 50 else "🔴")
                        lines.append(
                            f"| {m['mois']} | {m['jours']}j | {statut} {m['taux_occ_pct']}% | {m['cout']:,.2f} Dhs |"
                        )
                else:
                    lines.append("| Mois | Jours travaillés | Taux d'occupation |")
                    lines.append("|------|------------------|-------------------|")
                    for m in data["mois_detail"]:
                        statut = "🟢" if m["taux_occ_pct"] >= 80 else ("🟡" if m["taux_occ_pct"] >= 50 else "🔴")
                        lines.append(
                            f"| {m['mois']} | {m['jours']}j | {statut} {m['taux_occ_pct']}% |"
                        )
    else:
        if is_financial:
            has_budgets = any(any(m.get("ca", 0) > 0 for m in data.get("mois_detail", [])) for data in par_employe.values())
            if has_budgets:
                lines.append(f"## Synthèse globale de staffing et rentabilité par employé — {len(par_employe)} employé(s)")
                lines.append("\n| Employé | Jours travaillés | CJM (Journalier) | Salaire mensuel | Coût calculé | CA généré | Gain net | Taux de gain | Projets |")
                lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
                for emp, data in par_employe.items():
                    total_ca = data.get("total_ca", 0.0)
                    total_cout = data["total_cout"]
                    gain_net = total_ca - total_cout
                    marge_pct = (gain_net / total_ca * 100) if total_ca > 0 else 0.0
                    lines.append(
                        f"| **{emp}** | {data['total_jours']}j ({data['nb_mois']} mois) | {data['tjm_moyen']:,.2f} Dhs/jour | {data['salaire_moyen']:,.2f} Dhs/mois | {total_cout:,.2f} Dhs | {total_ca:,.2f} Dhs | {gain_net:+,.2f} Dhs | {marge_pct:.1f}% | {', '.join(data['projets'])} |"
                    )
            else:
                lines.append(f"## Synthèse globale de staffing — {len(par_employe)} employé(s)")
                lines.append("\n| Employé | Jours travaillés | CJM (Journalier) | Salaire mensuel | Coût calculé | Projets |")
                lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
                for emp, data in par_employe.items():
                    lines.append(
                        f"| **{emp}** | {data['total_jours']}j ({data['nb_mois']} mois) | {data['tjm_moyen']:,.2f} Dhs/jour | {data['salaire_moyen']:,.2f} Dhs/mois | {data['total_cout']:,.2f} Dhs | {', '.join(data['projets'])} |"
                    )
        else:
            # Mode très compact pour éviter d'exploser la limite de tokens de l'API LLM (ex: 6000 TPM limit)
            lines.append(f"## Synthèse globale — {len(par_employe)} employé(s)")
            lines.append("\nListe condensée des employés :")
            for emp, data in par_employe.items():
                lines.append(f"- **{emp}** : {data['total_jours']} jours travaillés sur les projets : {', '.join(data['projets'])}")

    if par_projet and is_financial:
        lines.append("\n## Synthèse par Projet")
        lines.append("| Projet | Jours travaillés | Coût total | CA facturé (Budget) | Gain net | Marge de rentabilité | Retour sur investissement (ROI) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for proj, data in par_projet.items():
            lines.append(
                f"| **{proj}** | {data['total_jours']}j | {data['total_cout']:,.2f} Dhs | {data['ca']:,.2f} Dhs | {data['gain']:+,.2f} Dhs | {data['marge_pct']:.1f}% | {data['roi_pct']:.1f}% |"
            )

    # ── Registre des Collaborateurs (Détails RH) ──────────────────
    has_meta = any(data.get("profil") or data.get("date_demarrage") for data in par_employe.values())
    if has_meta:
        lines.append("\n## Registre des Collaborateurs (Détails RH)")
        lines.append("| Employé | Profil Professionnel | Date de Démarrage | Ancienneté | Localisation |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for emp, data in par_employe.items():
            lines.append(
                f"| **{emp}** | {data.get('profil') or 'Non spécifié'} | {data.get('date_demarrage') or 'Non spécifiée'} | {data.get('anciennete') or 'Non spécifiée'} | {data.get('localisation') or 'Non spécifiée'} |"
            )

    if rentabilite and show_global_rentability and is_financial:
        lines.append("\n## Rentabilité Globale")
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
