"""
utils/staffing_extractor.py
────────────────────────────────────────────────────────────────────
Extrait les données de staffing depuis :
  - PDF  → OCR via pdfplumber + pytesseract (fallback)
  - Excel/CSV → Pandas direct

Structure cible retournée (liste de dicts) :
[
  {
    "employe":    "Jean Dupont",
    "projet":     "Projet Alpha",
    "mois":       "2024-03",        # YYYY-MM
    "jours":      18,               # jours travaillés ce mois
    "tjm":        650.0,            # Taux Journalier Moyen (€)
    "cout":       11700.0,          # jours × tjm
    "facturable": True              # le mois est-il facturable ?
  },
  ...
]
"""

import re
import logging
import tempfile
import os
from typing import List, Dict, Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# EXTRACTION DEPUIS EXCEL / CSV
# ══════════════════════════════════════════════════════════════════

# Colonnes reconnues (insensible à la casse, accents tolérés)
_COL_MAP = {
    "employe":    ["employe", "employé", "nom", "collaborateur", "name", "employee", "prenom", "prénom", "ressource"],
    "projet":     ["projet", "project", "affaire", "mission", "projet affecté", "projet affecte", "nom du projet / client", "nom du projet", "nom projet", "projet affecté (mois)"],
    "mois":       ["mois", "month", "periode", "période", "date", "date de début", "date de debut", "date debut"],
    "jours":      ["jours", "nb_jours", "nb jours", "jours travaillés", "days", "worked_days", "nombre de jours travaillés (mois)", "nombre de jours travailles (mois)", "nombre de jours", "nb de jours"],
    "tjm":        ["tjm", "cjm", "taux", "taux journalier", "daily_rate", "rate", "salaire", "salaire (mad)", "salaire moyen (dhs/mois)", "cjm (dhs/jour)", "salaire moyen (mad/mois)"],
    "facturable": ["facturable", "billable", "facturé"],
    "budget":     ["budget", "budget_projet", "ca", "chiffre d'affaires", "facture", "montant_facture", "billing", "revenue", "chiffre d'affaires (mad)", "ca (mad)", "budget (mad)"],
    "annee":      ["annee", "année", "year", "an"],
    "id":         ["id", "id_collaborateur", "id_employe", "matricule", "code", "identifiant", "id collab", "id_collab", "id collab", "id collab."],
}


def _normalize_col(col: str) -> Optional[str]:
    """Retourne la clé normalisée ou None si inconnue."""
    c = col.strip().lower()
    c = c.replace("é", "e").replace("è", "e").replace("ê", "e")
    for key, variants in _COL_MAP.items():
        if c in variants:
            return key
    return None


MONTH_MAP = {
    "janvier": "01", "fevrier": "02", "mars": "03", "avril": "04", "mai": "05", "juin": "06",
    "juillet": "07", "aout": "08", "septembre": "09", "octobre": "10", "novembre": "11", "decembre": "12",
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"
}


def _combine_mois_annee(mois_val: Any, annee_val: Any) -> str:
    m_str = str(mois_val).strip().lower().replace("é", "e").replace("û", "u").replace("v", "v")
    # Supprimer les éventuels décimaux de l'année (ex: 2026.0)
    a_str = str(annee_val).strip().split(".")[0]
    a_str = re.sub(r"\D", "", a_str)
    
    year = a_str if len(a_str) == 4 else None
    
    # Si l'année n'est pas spécifiée séparément dans la colonne Année, essayons de l'extraire du mois
    if not year:
        parsed_mois = _parse_mois(mois_val)
        m = re.match(r"(20\d{2})[-/](\d{2})", parsed_mois)
        if m:
            return f"{m.group(1)}-{m.group(2)}"
        # Par défaut
        year = "2026"
    else:
        # Si une année est spécifiée dans la colonne Année, mais que la colonne Mois contient une date complète, on privilégie la date complète
        parsed_mois = _parse_mois(mois_val)
        m = re.match(r"(20\d{2})[-/](\d{2})", parsed_mois)
        if m:
            return f"{m.group(1)}-{m.group(2)}"
            
    month = "06"
    if m_str in MONTH_MAP:
        month = MONTH_MAP[m_str]
    elif m_str.isdigit():
        val = int(m_str)
        if 1 <= val <= 12:
            month = f"{val:02d}"
    else:
        parsed_mois = _parse_mois(mois_val)
        m = re.match(r"(20\d{2})[-/](\d{2})", parsed_mois)
        if m:
            return f"{year}-{m.group(2)}"
            
    return f"{year}-{month}"


def _melt_wide_months_df(df: pd.DataFrame) -> pd.DataFrame:
    """Détecte si le DataFrame est au format large avec les mois en colonnes, et le fond (melt) au format long."""
    cols_lower = [str(c).strip().lower().replace("é", "e").replace("û", "u").replace("v", "v") for c in df.columns]
    
    french_months = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]
    month_indices = [i for i, c in enumerate(cols_lower) if c in french_months]
    
    if not month_indices:
        return df
        
    # Colonnes de mois et autres colonnes d'identification
    month_cols = [df.columns[i] for i in month_indices]
    id_cols = [c for c in df.columns if c not in month_cols]
    
    # Pivoter
    df_melted = df.melt(
        id_vars=id_cols,
        value_vars=month_cols,
        var_name="Mois",
        value_name="Jours"
    )
    
    # Supprimer les lignes où Jours est NaN/vide ou 0 pour ne garder que les imputations effectives
    df_melted = df_melted.dropna(subset=["Jours"])
    df_melted = df_melted[df_melted["Jours"].astype(str).str.strip().str.lower() != "nan"]
    df_melted = df_melted[df_melted["Jours"] != 0]
    
    return df_melted


def extract_from_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Normalise un DataFrame brut en liste de records staffing."""
    df = _melt_wide_months_df(df)
    mapping = {}
    for col in df.columns:
        norm = _normalize_col(str(col))
        if norm:
            mapping[norm] = col

    # Vérifier si on a séparément 'Nom' et 'Prénom' et les combiner
    nom_col = None
    prenom_col = None
    for col in df.columns:
        c_norm = str(col).strip().lower().replace("é", "e").replace("è", "e").replace("ê", "e")
        if c_norm == "nom":
            nom_col = col
        elif c_norm in ("prenom", "prénom"):
            prenom_col = col

    if nom_col is not None and prenom_col is not None:
        df = df.copy()
        combined_names = []
        for _, row in df.iterrows():
            n_val = str(row.get(nom_col, "")).strip() if pd.notna(row.get(nom_col)) else ""
            p_val = str(row.get(prenom_col, "")).strip() if pd.notna(row.get(prenom_col)) else ""
            if n_val.lower() == "nan": n_val = ""
            if p_val.lower() == "nan": p_val = ""
            combined_names.append(f"{p_val} {n_val}".strip())
        df["Employe_Combined"] = combined_names
        mapping["employe"] = "Employe_Combined"

    required = {"employe", "mois", "jours", "tjm"}
    missing = required - set(mapping.keys())
    if missing:
        logger.warning(f"Colonnes manquantes dans le fichier : {missing}")
        logger.warning(f"Colonnes détectées : {list(df.columns)}")

    records = []
    tjm_col = mapping.get("tjm")
    for _, row in df.iterrows():
        rec: Dict[str, Any] = {}

        emp_name = str(row.get(mapping.get("employe", ""), "Inconnu")).strip()
        emp_id_raw = str(row.get(mapping.get("id", ""), "")).strip()
        if emp_id_raw and emp_id_raw.lower() != "nan" and emp_id_raw.lower() != "none" and emp_id_raw != "0" and emp_id_raw != "":
            # clean up raw float representation e.g. "1.0" -> "1"
            if emp_id_raw.endswith(".0"):
                emp_id_raw = emp_id_raw[:-2]
            rec["employe"] = f"{emp_name} (ID: {emp_id_raw})"
        else:
            rec["employe"] = emp_name

        rec["projet"]     = str(row.get(mapping.get("projet",  ""), "N/A")).strip()
        
        # Récupérer mois et année pour combiner
        mois_val = row.get(mapping.get("mois", ""), "")
        annee_val = row.get(mapping.get("annee", ""), "")
        rec["mois"]       = _combine_mois_annee(mois_val, annee_val)
        
        rec["jours"]      = _safe_float(row.get(mapping.get("jours", ""), 0))
        
        tjm_val = _safe_float(row.get(tjm_col, 0))
        # Si la colonne est un salaire mensuel, on le divise par 21 pour obtenir le CJM journalier
        if tjm_col and "salaire" in str(tjm_col).lower():
            tjm_val = round(tjm_val / 21.0, 2)
        rec["tjm"]        = tjm_val
        
        rec["facturable"] = _parse_bool(row.get(mapping.get("facturable", ""), True))
        rec["budget"]     = _safe_float(row.get(mapping.get("budget", ""), 0))

        if rec["jours"] > 0 and rec["tjm"] > 0:
            rec["cout"] = round(rec["jours"] * rec["tjm"], 2)
        else:
            rec["cout"] = 0.0

        if rec["employe"] and rec["employe"] != "Inconnu":
            records.append(rec)

    logger.info(f"✅ {len(records)} lignes de staffing extraites du DataFrame.")
    return records


def extract_from_multiple_dataframes(dfs: List[pd.DataFrame]) -> List[Dict[str, Any]]:
    """
    Extrait les données de staffing à partir de plusieurs DataFrames.
    Utile si les données sont réparties sur plusieurs feuilles (ex: 'feuille de projet' et 'collab')
    ou plusieurs fichiers.
    """
    if not dfs:
        return []

    complete_records = []
    project_rows = []
    budget_by_project = {}
    
    collab_by_id = {}
    collab_by_name = {}
    
    # 1. Pré-détection des doublons de projets sur des années différentes
    from collections import defaultdict
    project_years_map = {}
    for df in dfs:
        if df is None or df.empty:
            continue
        mapping = {}
        for col in df.columns:
            norm = _normalize_col(str(col))
            if norm:
                mapping[norm] = col
        has_proj = "projet" in mapping
        has_budget = "budget" in mapping
        has_emp_name = "employe" in mapping or "nom" in [str(c).strip().lower() for c in df.columns] or "prenom" in [str(c).strip().lower() for c in df.columns]
        
        if has_proj and has_budget and not has_emp_name:
            date_col = None
            for col in df.columns:
                c_norm = str(col).strip().lower().replace("é", "e").replace("è", "e").replace("ê", "e")
                if "demarrage" in c_norm or "debut" in c_norm or "start" in c_norm or "démarrage" in c_norm:
                    date_col = col
                    break
            for _, row in df.iterrows():
                proj_name = str(row.get(mapping.get("projet", ""), "")).strip()
                if proj_name and proj_name.lower() not in ("nan", "none", "", "total ca"):
                    year = None
                    if date_col:
                        date_val = str(row.get(date_col, "")).strip()
                        m = re.search(r"\b(20\d{2})\b", date_val)
                        if m:
                            year = m.group(1)
                    if year:
                        if proj_name.lower() not in project_years_map:
                            project_years_map[proj_name.lower()] = set()
                        project_years_map[proj_name.lower()].add(year)
                        
    duplicate_projects = {name for name, years in project_years_map.items() if len(years) > 1}

    def _normalize_name(n: str) -> str:
        if not n:
            return ""
        n = str(n).strip().lower()
        n = n.replace("é", "e").replace("è", "e").replace("ê", "e").replace("ë", "e")
        n = n.replace("à", "a").replace("â", "a").replace("ä", "a")
        n = n.replace("î", "i").replace("ï", "i")
        n = n.replace("ô", "o").replace("ö", "o")
        n = n.replace("û", "u").replace("ü", "u")
        n = n.replace("ç", "c")
        n = re.sub(r'[^a-z0-9\s]', '', n)
        return " ".join(n.split())

    for df in dfs:
        if df is None or df.empty:
            continue
        df = _melt_wide_months_df(df)

        # Normaliser les colonnes de ce DataFrame
        mapping = {}
        for col in df.columns:
            norm = _normalize_col(str(col))
            if norm:
                mapping[norm] = col

        # Vérifier si on a séparément 'Nom' et 'Prénom' et les combiner
        nom_col = None
        prenom_col = None
        for col in df.columns:
            c_norm = str(col).strip().lower().replace("é", "e").replace("è", "e").replace("ê", "e")
            if c_norm == "nom":
                nom_col = col
            elif c_norm in ("prenom", "prénom"):
                prenom_col = col

        if nom_col is not None and prenom_col is not None:
            df = df.copy()
            combined_names = []
            for _, row in df.iterrows():
                n_val = str(row.get(nom_col, "")).strip() if pd.notna(row.get(nom_col)) else ""
                p_val = str(row.get(prenom_col, "")).strip() if pd.notna(row.get(prenom_col)) else ""
                if n_val.lower() == "nan": n_val = ""
                if p_val.lower() == "nan": p_val = ""
                combined_names.append(f"{p_val} {n_val}".strip())
            df["Employe_Combined"] = combined_names
            mapping["employe"] = "Employe_Combined"

        has_emp_name = "employe" in mapping
        has_id = "id" in mapping
        has_tjm = "tjm" in mapping
        has_proj = "projet" in mapping
        has_jours = "jours" in mapping
        has_mois = "mois" in mapping
        has_budget = "budget" in mapping

        # Cas 1: Budget de projet (sans employé) - e.g. Feuille_projet_Rempli.xlsx
        if has_proj and has_budget and not has_emp_name:
            date_col = None
            # Trouver la colonne de date
            for col in df.columns:
                c_norm = str(col).strip().lower().replace("é", "e").replace("è", "e").replace("ê", "e")
                if "demarrage" in c_norm or "debut" in c_norm or "start" in c_norm or "démarrage" in c_norm:
                    date_col = col
                    break
            
            for _, row in df.iterrows():
                proj_name = str(row.get(mapping.get("projet", ""), "")).strip()
                budget_val = _safe_float(row.get(mapping.get("budget", ""), 0))
                
                # Extraire l'année
                year = None
                if date_col:
                    date_val = str(row.get(date_col, "")).strip()
                    m = re.search(r"\b(20\d{2})\b", date_val)
                    if m:
                        year = m.group(1)
                
                if proj_name and proj_name.lower() not in ("nan", "none", "", "total ca"):
                    final_proj_name = proj_name
                    if year and proj_name.lower() in duplicate_projects:
                        final_proj_name = f"{proj_name} ({year})"
                    budget_by_project[final_proj_name.lower()] = budget_val
                    # Garder aussi avec clé d'année et brute comme fallbacks
                    if year:
                        budget_by_project[f"{proj_name.lower()}_{year}"] = budget_val
                    budget_by_project[proj_name.lower()] = budget_val
            continue

        if not (has_emp_name or has_id):
            continue

        # Cas 2: DataFrame complet (avec employé + tjm + jours/projets)
        if has_tjm and (has_proj or has_jours or has_mois):
            complete_records.extend(extract_from_dataframe(df))
        # Cas 3: Collaborateurs uniquement (CJM / salaires) - e.g. Collaborateurs_Maroc_Final.xlsx
        elif has_tjm:
            tjm_col = mapping.get("tjm")
            date_col = None
            profil_col = None
            anc_col = None
            loc_col = None
            for col in df.columns:
                c_norm = str(col).strip().lower().replace("é", "e").replace("è", "e").replace("ê", "e")
                if "demarrage" in c_norm or "debut" in c_norm or "start" in c_norm or "démarrage" in c_norm:
                    date_col = col
                elif "profil" in c_norm or "role" in c_norm or "poste" in c_norm:
                    profil_col = col
                elif "ancien" in c_norm or "experience" in c_norm:
                    anc_col = col
                elif "local" in c_norm or "ville" in c_norm or "pays" in c_norm:
                    loc_col = col

            for _, row in df.iterrows():
                emp_name = str(row.get(mapping.get("employe", ""), "")).strip()
                emp_id_raw = str(row.get(mapping.get("id", ""), "")).strip()
                if emp_id_raw.endswith(".0"):
                    emp_id_raw = emp_id_raw[:-2]
                
                tjm = _safe_float(row.get(tjm_col, 0))
                # Si la colonne est un salaire mensuel, on le divise par 21 pour obtenir le CJM journalier
                if tjm_col and "salaire" in str(tjm_col).lower():
                    tjm = round(tjm / 21.0, 2)
                
                date_val = str(row.get(date_col, "")).strip() if date_col and pd.notna(row.get(date_col)) else ""
                profil_val = str(row.get(profil_col, "")).strip() if profil_col and pd.notna(row.get(profil_col)) else ""
                anc_val = str(row.get(anc_col, "")).strip() if anc_col and pd.notna(row.get(anc_col)) else ""
                loc_val = str(row.get(loc_col, "")).strip() if loc_col and pd.notna(row.get(loc_col)) else ""

                collab_info = {
                    "name": emp_name,
                    "id": emp_id_raw,
                    "tjm": tjm,
                    "date_demarrage": date_val,
                    "profil": profil_val,
                    "anciennete": anc_val,
                    "localisation": loc_val
                }
                if emp_id_raw and emp_id_raw.lower() not in ("nan", "none", "", "0"):
                    collab_by_id[emp_id_raw] = collab_info
                if emp_name and emp_name.lower() not in ("nan", "none", "", "inconnu"):
                    collab_by_name[_normalize_name(emp_name)] = collab_info
        # Cas 4: Imputations / projets uniquement (jours travaillés) - e.g. Imputation_Rempli.xlsx
        else:
            for _, row in df.iterrows():
                emp_name = str(row.get(mapping.get("employe", ""), "")).strip()
                emp_id_raw = str(row.get(mapping.get("id", ""), "")).strip()
                if emp_id_raw.endswith(".0"):
                    emp_id_raw = emp_id_raw[:-2]

                projet = str(row.get(mapping.get("projet", ""), "N/A")).strip()
                mois_val = row.get(mapping.get("mois", ""), "")
                annee_val = row.get(mapping.get("annee", ""), "")
                mois = _combine_mois_annee(mois_val, annee_val)
                jours = _safe_float(row.get(mapping.get("jours", ""), 0))
                facturable = _parse_bool(row.get(mapping.get("facturable", ""), True))
                budget = _safe_float(row.get(mapping.get("budget", ""), 0))

                project_rows.append({
                    "emp_name": emp_name,
                    "emp_id": emp_id_raw,
                    "projet": projet,
                    "mois": mois,
                    "jours": jours,
                    "facturable": facturable,
                    "budget": budget
                })

    # Fusionner les imputations et les collaborateurs/budgets
    merged_records = []
    assigned_budgets = set()  # Pour n'attribuer le budget du projet qu'une seule fois
    
    if project_rows:
        for prow in project_rows:
            collab_info = None
            emp_id = prow["emp_id"]
            emp_name = prow["emp_name"]

            if emp_id and emp_id.lower() not in ("nan", "none", "", "0"):
                collab_info = collab_by_id.get(emp_id)
            
            if not collab_info and emp_name:
                collab_info = collab_by_name.get(_normalize_name(emp_name))

            tjm = collab_info["tjm"] if collab_info else 0.0
            
            if emp_id and emp_id.lower() not in ("nan", "none", "", "0"):
                final_name = f"{emp_name} (ID: {emp_id})" if emp_name else f"ID: {emp_id}"
            else:
                final_name = emp_name or "Inconnu"

            # Attribuer le budget global de projet (CA) à chaque ligne
            proj_key = prow["projet"].lower()
            budget_val = prow["budget"]
            
            # Détecter l'année du projet
            final_mois = prow["mois"]
            emp_year = None
            if proj_key in project_years_map:
                years = project_years_map[proj_key]
                if len(years) == 1:
                    emp_year = list(years)[0]
                elif len(years) > 1:
                    start_date = collab_info.get("date_demarrage", "") if collab_info else ""
                    emp_year = "2025"
                    if start_date and str(start_date).strip().startswith("2026"):
                        emp_year = "2026"
            
            if emp_year:
                if prow["mois"] and len(prow["mois"]) >= 7:
                    final_mois = f"{emp_year}-{prow['mois'][5:7]}"
            
            imp_year = None
            if final_mois and len(final_mois) >= 4:
                m = re.match(r"^(20\d{2})", final_mois)
                if m:
                    imp_year = m.group(1)
            
            if budget_val == 0.0:
                if imp_year and f"{proj_key}_{imp_year}" in budget_by_project:
                    budget_val = budget_by_project[f"{proj_key}_{imp_year}"]
                elif proj_key in budget_by_project:
                    budget_val = budget_by_project[proj_key]

            # Si le projet est un doublon, on lui affecte le nom spécifique incluant l'année
            final_proj_name = prow["projet"]
            if proj_key in duplicate_projects and imp_year:
                final_proj_name = f"{prow['projet']} ({imp_year})"
                if final_proj_name.lower() in budget_by_project:
                    budget_val = budget_by_project[final_proj_name.lower()]

            rec = {
                "employe":    final_name,
                "projet":     final_proj_name,
                "mois":       final_mois,
                "jours":      prow["jours"],
                "tjm":        tjm,
                "facturable": prow["facturable"],
                "budget":     budget_val,
                "cout":       round(prow["jours"] * tjm, 2) if prow["jours"] > 0 and tjm > 0 else 0.0,
                "date_demarrage": collab_info.get("date_demarrage", "") if collab_info else "",
                "profil":         collab_info.get("profil", "") if collab_info else "",
                "anciennete":     collab_info.get("anciennete", "") if collab_info else "",
                "localisation":   collab_info.get("localisation", "") if collab_info else ""
            }
            if rec["employe"] != "Inconnu":
                merged_records.append(rec)

    total_records = complete_records + merged_records
    logger.info(f"✅ Total {len(total_records)} lignes extraites (Complets: {len(complete_records)}, Fusionnés: {len(merged_records)})")
    return total_records


# ══════════════════════════════════════════════════════════════════
# EXTRACTION DEPUIS PDF (OCR)
# ══════════════════════════════════════════════════════════════════

def _parse_split_pdf_table(text_pages: List[str]) -> List[Dict[str, Any]]:
    """
    Parse un tableau qui a été coupé horizontalement et réparti sur deux pages PDF.
    Page 1 contient : id, prenom, salaire, projet, jours, budget, mois.
    Page 2 contient : annee.
    """
    if len(text_pages) < 2:
        return []

    page1_lines = [line.strip() for line in text_pages[0].splitlines() if line.strip()]
    page2_lines = [line.strip() for line in text_pages[1].splitlines() if line.strip()]

    if not page1_lines or not page2_lines:
        return []

    header1 = page1_lines[0].lower()
    header2 = page2_lines[0].lower()

    # Vérification que la structure ressemble bien à notre table coupée
    if not ("prenom" in header1 or "salaire" in header1) or "annee" not in header2:
        return []

    records = []
    data1 = page1_lines[1:]
    data2 = page2_lines[1:]

    # Parcourir et assembler chaque ligne
    for line1, line2 in zip(data1, data2):
        parts1 = line1.split()
        if len(parts1) < 7:
            continue

        try:
            val_id = parts1[0]
            prenom = parts1[1]
            salaire = _safe_float(parts1[2])
            mois = parts1[-1]
            budget = _safe_float(parts1[-2])
            jours = _safe_float(parts1[-3])
            projet = " ".join(parts1[3:-3])

            # Récupère l'année sur la page 2
            annee = line2.split()[0] if line2 else "2026"

            mois_complet = _combine_mois_annee(mois, annee)

            rec = {
                "employe": f"{prenom} (ID: {val_id})" if val_id else prenom,
                "projet": projet,
                "mois": mois_complet,
                "jours": jours,
                "tjm": salaire,
                "cout": round(jours * salaire, 2),
                "facturable": True,
                "budget": budget
            }
            records.append(rec)
        except Exception as e:
            logger.warning(f"Erreur parsing ligne PDF coupée : {e}")
            continue

    logger.info(f"🧩 Assemblage PDF réussi : {len(records)} records reconstitués.")
    return records


def extract_from_pdf_bytes(file_bytes: bytes, file_name: str = "doc.pdf") -> List[Dict[str, Any]]:
    """
    Extrait les données de staffing depuis un PDF en mémoire.
    Stratégie :
      1. pdfplumber  → extraction texte natif (rapide)
      2. pytesseract → OCR page par page si le PDF est scanné
    """
    records = []

    try:
        import pdfplumber
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        text_pages = []
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                # Tenter d'abord d'extraire un tableau structuré
                tables = page.extract_tables()
                for table in tables:
                    df = _table_to_df(table)
                    if df is not None:
                        records.extend(extract_from_dataframe(df))

                # Texte brut pour le parsing regex
                text = page.extract_text() or ""
                if text.strip():
                    text_pages.append(text)

        os.unlink(tmp_path)

        # Si aucun tableau structuré trouvé, tenter d'assembler la table coupée en pages
        if not records and len(text_pages) >= 2:
            records = _parse_split_pdf_table(text_pages)

        # Si toujours rien, tenter le parsing regex historique
        if not records and text_pages:
            full_text = "\n".join(text_pages)
            records = _parse_text_staffing(full_text)

        # Si encore rien → OCR complet
        if not records:
            logger.info("📸 Aucun texte natif — lancement de l'OCR pytesseract...")
            records = _ocr_pdf_bytes(file_bytes)

    except ImportError:
        logger.warning("pdfplumber non installé — fallback OCR direct.")
        records = _ocr_pdf_bytes(file_bytes)
    except Exception as e:
        logger.error(f"Erreur extraction PDF '{file_name}': {e}")

    return records


def _ocr_pdf_bytes(file_bytes: bytes) -> List[Dict[str, Any]]:
    """OCR via pdf2image + pytesseract."""
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
        from PIL import Image

        images = convert_from_bytes(file_bytes, dpi=300)
        all_text = ""
        for img in images:
            text = pytesseract.image_to_string(img, lang="fra+eng")
            all_text += text + "\n"

        logger.info(f"OCR terminé — {len(all_text)} caractères extraits.")
        return _parse_text_staffing(all_text)

    except ImportError:
        logger.error("pytesseract ou pdf2image non installés.")
        return []
    except Exception as e:
        logger.error(f"Erreur OCR : {e}")
        return []


def _table_to_df(table: list) -> Optional[pd.DataFrame]:
    """Convertit un tableau pdfplumber (list of lists) en DataFrame."""
    if not table or len(table) < 2:
        return None
    try:
        df = pd.DataFrame(table[1:], columns=table[0])
        df.columns = [str(c).strip() if c else f"col_{i}" for i, c in enumerate(df.columns)]
        return df
    except Exception:
        return None


def _parse_text_staffing(text: str) -> List[Dict[str, Any]]:
    """
    Parsing regex pour extraire les données de staffing depuis un texte brut OCR.
    Format attendu (flexible) :
      NomPrenom | Projet | 2024-03 | 18j | 650€
    """
    records = []
    # Regex générique : cherche lignes avec un nombre de jours et un TJM
    pattern = re.compile(
        r"(?P<employe>[A-ZÀ-Ü][a-zà-ü]+(?: [A-ZÀ-Ü][a-zà-ü]+)+)"
        r".*?(?P<mois>20\d{2}[-/]\d{2}|\d{2}[-/]20\d{2})"
        r".*?(?P<jours>\d+(?:[.,]\d+)?)\s*(?:j(?:ours?)?)"
        r".*?(?P<tjm>\d+(?:[.,]\d+)?)\s*(?:€|EUR|eur)?",
        re.IGNORECASE
    )
    for match in pattern.finditer(text):
        try:
            jours = _safe_float(match.group("jours"))
            tjm   = _safe_float(match.group("tjm"))
            rec = {
                "employe":    match.group("employe").strip(),
                "projet":     "Extrait PDF",
                "mois":       _parse_mois(match.group("mois")),
                "jours":      jours,
                "tjm":        tjm,
                "cout":       round(jours * tjm, 2),
                "facturable": True,
            }
            records.append(rec)
        except Exception:
            continue

    logger.info(f"Regex staffing : {len(records)} entrées trouvées dans le texte brut.")
    return records


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _safe_float(val: Any) -> float:
    try:
        return float(str(val).replace(",", ".").replace(" ", "").replace("€", ""))
    except (ValueError, TypeError):
        return 0.0


def _parse_mois(val: Any) -> str:
    """Normalise n'importe quel format de date en YYYY-MM."""
    s = str(val).strip() if val is not None else ""
    if not s or s.lower() in ("nan", "none", "nat", ""):
        return "2026-06"
    # YYYY-MM ou YYYY/MM
    m = re.match(r"(20\d{2})[-/](\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    # MM/YYYY ou MM-YYYY
    m = re.match(r"(\d{2})[-/](20\d{2})", s)
    if m:
        return f"{m.group(2)}-{m.group(1)}"
    # Timestamp pandas
    try:
        return pd.to_datetime(s).strftime("%Y-%m")
    except Exception:
        return s


def _parse_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ("oui", "yes", "true", "1", "o", "vrai")