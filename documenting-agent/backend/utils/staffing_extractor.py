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
    "employe":    ["employe", "employé", "nom", "collaborateur", "name", "employee", "prenom", "prénom"],
    "projet":     ["projet", "project", "affaire", "mission"],
    "mois":       ["mois", "month", "periode", "période", "date"],
    "jours":      ["jours", "nb_jours", "nb jours", "jours travaillés", "days", "worked_days"],
    "tjm":        ["tjm", "taux", "taux journalier", "daily_rate", "rate", "salaire"],
    "facturable": ["facturable", "billable", "facturé"],
    "budget":     ["budget", "budget_projet", "ca", "chiffre d'affaires", "facture", "montant_facture", "billing", "revenue"],
    "annee":      ["annee", "année", "year", "an"],
    "id":         ["id", "id_collaborateur", "id_employe", "matricule", "code", "identifiant"],
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


def extract_from_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Normalise un DataFrame brut en liste de records staffing."""
    mapping = {}
    for col in df.columns:
        norm = _normalize_col(str(col))
        if norm:
            mapping[norm] = col

    required = {"employe", "mois", "jours", "tjm"}
    missing = required - set(mapping.keys())
    if missing:
        logger.warning(f"Colonnes manquantes dans le fichier : {missing}")
        logger.warning(f"Colonnes détectées : {list(df.columns)}")

    records = []
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
        rec["tjm"]        = _safe_float(row.get(mapping.get("tjm",   ""), 0))
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


# ══════════════════════════════════════════════════════════════════
# EXTRACTION DEPUIS PDF (OCR)
# ══════════════════════════════════════════════════════════════════

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

        # Si aucun tableau trouvé → parsing regex du texte brut
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