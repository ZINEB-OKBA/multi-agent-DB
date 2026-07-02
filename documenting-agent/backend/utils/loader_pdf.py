"""
utils/loader_pdf.py
────────────────────────────────────────────────────────────────────
Charge PDF/Word depuis des chemins disque (pas Streamlit UploadedFile).
Améliorations supplémentaires :
  ✅ PyMuPDFLoader  → extraction haute fidélité (colonnes, tableaux, layout)
  ✅ PyPDFLoader    → fallback léger si PyMuPDF non installé
  ✅ OCR pytesseract → pour PDF scannés (image only)
  ✅ CHUNK_SIZE 800 / OVERLAP 200 → précision retrieval améliorée 
  ✅ Métadonnées enrichies → source, page, nb_chars, has_ocr, loader_used
  ✅ Déduplication des chunks quasi-vides (< 30 chars)
  ✅ Chargement multi-format unifié
"""

import logging
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# ── Paramètres de découpage ────────────────────────────────────────────────────
# ahmed : 800/200 vs zineb 1000/150 → meilleur recall sur questions précises
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 200
MIN_CHUNK_LEN = 30   # ignorer les chunks quasi-vides (headers orphelins, numéros de page)


# ══════════════════════════════════════════════════════════════════════════════
# LOADERS INTERNES
# ══════════════════════════════════════════════════════════════════════════════

def _load_pdf(file_path: str) -> List[Document]:
    """
    Stratégie d'extraction en cascade :
      1. PyMuPDFLoader  → meilleure gestion des colonnes et du layout (ahmed)
      2. PyPDFLoader    → fallback si PyMuPDF absent
      3. OCR pdfplumber → tables natives dans PDF structuré (zineb)
      4. OCR pytesseract via pdf2image → si PDF entièrement scanné (zineb)

    Métadonnées ajoutées : source, page, nb_chars, has_ocr, loader_used
    """
    file_name = Path(file_path).name
    docs: List[Document] = []
    loader_used = "unknown"

    # ── Tentative 1 : PyMuPDF (ahmed — meilleur sur les colonnes/tableaux) ────
    try:
        from langchain_community.document_loaders import PyMuPDFLoader
        raw = PyMuPDFLoader(file_path).load()
        if raw:
            docs = raw
            loader_used = "PyMuPDF"
            logger.info(f"📄 PDF (PyMuPDF) : {file_name} → {len(docs)} page(s)")
    except ImportError:
        logger.warning("⚠️ PyMuPDF absent — fallback PyPDFLoader")
    except Exception as e:
        logger.warning(f"⚠️ PyMuPDF échoué ({e}) — fallback PyPDFLoader")

    # ── Tentative 2 : PyPDFLoader (zineb — toujours disponible) ──────────────
    if not docs:
        try:
            from langchain_community.document_loaders import PyPDFLoader
            raw = PyPDFLoader(file_path).load()
            if raw:
                docs = raw
                loader_used = "PyPDF"
                logger.info(f"📄 PDF (PyPDF) : {file_name} → {len(docs)} page(s)")
        except Exception as e:
            logger.error(f"❌ PyPDFLoader échoué : {e}")

    # ── Vérification du contenu textuel ───────────────────────────────────────
    full_text = "".join(d.page_content for d in docs).strip()

    # ── Tentative 3 : pdfplumber sur tableaux (zineb) ─────────────────────────
    if docs and not full_text:
        logger.info("⚠️ Texte natif vide — tentative pdfplumber (extraction de tableaux)...")
        try:
            import pdfplumber, tempfile

            extra_docs: List[Document] = []
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    table_text = ""
                    for table in tables:
                        for row in table:
                            table_text += " | ".join(
                                str(cell).strip() if cell else "" for cell in row
                            ) + "\n"
                    page_text = page.extract_text() or ""
                    combined = (page_text + "\n" + table_text).strip()
                    if combined:
                        extra_docs.append(Document(
                            page_content=combined,
                            metadata={"source": file_name, "page": i}
                        ))
            if extra_docs:
                docs = extra_docs
                loader_used = "pdfplumber"
                full_text = "".join(d.page_content for d in docs).strip()
                logger.info(f"   → pdfplumber : {len(docs)} page(s) avec contenu")
        except Exception as e:
            logger.warning(f"⚠️ pdfplumber échoué : {e}")

    # ── Tentative 4 : OCR pytesseract (zineb — PDF scannés) ──────────────────
    if not full_text:
        logger.info("📸 Aucun texte natif détecté — lancement de l'OCR (pdf2image + pytesseract)...")
        try:
            from pdf2image import convert_from_path
            import pytesseract

            images = convert_from_path(file_path, dpi=300)
            ocr_docs: List[Document] = []
            for i, img in enumerate(images):
                text = pytesseract.image_to_string(img, lang="fra+eng")
                if text.strip():
                    ocr_docs.append(Document(
                        page_content=text,
                        metadata={
                            "source": file_name,
                            "page": i,
                            "has_ocr": True,
                            "loader_used": "pytesseract",
                        }
                    ))
            if ocr_docs:
                docs = ocr_docs
                loader_used = "pytesseract (OCR)"
                logger.info(f"   → OCR réussi : {len(docs)} page(s)")
            else:
                logger.warning(f"   → OCR n'a extrait aucun texte pour {file_name}")

        except ImportError:
            logger.error("❌ pdf2image ou pytesseract non installés — OCR impossible.")
        except Exception as ocr_err:
            logger.error(f"❌ OCR échoué sur {file_name} : {ocr_err}")

    # ── Enrichissement des métadonnées ────────────────────────────────────────
    for d in docs:
        d.metadata.setdefault("source", file_name)
        d.metadata["loader_used"] = loader_used
        d.metadata["has_ocr"]     = (loader_used == "pytesseract (OCR)")
        d.metadata["nb_chars"]    = len(d.page_content)

    logger.info(
        f"✅ {file_name} — {len(docs)} page(s) via {loader_used} "
        f"({sum(d.metadata['nb_chars'] for d in docs)} caractères total)"
    )
    return docs


def _load_docx(file_path: str) -> List[Document]:
    """
    Charge un fichier Word (.docx / .doc).
    Tente Docx2txtLoader, fallback python-docx pour les .docx complexes.
    """
    file_name = Path(file_path).name
    docs: List[Document] = []

    try:
        from langchain_community.document_loaders import Docx2txtLoader
        docs = Docx2txtLoader(file_path).load()
        for d in docs:
            d.metadata["source"]      = file_name
            d.metadata["loader_used"] = "Docx2txt"
            d.metadata["nb_chars"]    = len(d.page_content)
        logger.info(f"📝 DOCX (Docx2txt) : {file_name} → {len(docs)} section(s)")

    except Exception as e:
        logger.warning(f"⚠️ Docx2txt échoué ({e}) — fallback python-docx")
        try:
            import docx
            doc_obj = docx.Document(file_path)
            full_text = "\n\n".join(p.text for p in doc_obj.paragraphs if p.text.strip())
            if full_text:
                docs = [Document(
                    page_content=full_text,
                    metadata={
                        "source": file_name,
                        "loader_used": "python-docx",
                        "nb_chars": len(full_text),
                    }
                )]
                logger.info(f"📝 DOCX (python-docx) : {file_name} → {len(full_text)} chars")
        except Exception as e2:
            logger.error(f"❌ Chargement DOCX totalement échoué pour {file_name} : {e2}")

    return docs


# ══════════════════════════════════════════════════════════════════════════════
# SPLITTER
# ══════════════════════════════════════════════════════════════════════════════

def _split(raw_docs: List[Document]) -> List[Document]:
    """
    Découpage en chunks avec RecursiveCharacterTextSplitter.
    Filtre les chunks quasi-vides (< MIN_CHUNK_LEN chars) et préserve les métadonnées source.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = CHUNK_SIZE,
        chunk_overlap = CHUNK_OVERLAP,
        separators    = ["\n\n", "\n", ".", " ", ""],
    )
    raw_chunks = splitter.split_documents(raw_docs)

    # Déduplication des micro-chunks (numéros de page orphelins, tirets, etc.)
    chunks = [c for c in raw_chunks if len(c.page_content.strip()) >= MIN_CHUNK_LEN]

    logger.info(
        f"✂️  {len(raw_docs)} doc(s) → {len(raw_chunks)} chunk(s) bruts "
        f"→ {len(chunks)} chunk(s) retenus (filtre >{MIN_CHUNK_LEN} chars)"
    )
    return chunks


# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE PUBLIC
# ══════════════════════════════════════════════════════════════════════════════

def load_uploaded_files_from_paths(
    file_paths: List[str],
    split: bool = True,
) -> List[Document]:
    """
    Charge un ou plusieurs fichiers PDF/Word depuis leurs chemins disque.
    Utilisé par l'orchestrateur (IndexService) et les tests.

    Paramètres
    ----------
    file_paths : chemins absolus ou relatifs vers les fichiers
    split      : True (défaut) → retourne des chunks ; False → retourne les pages brutes

    Retourne
    --------
    Liste de Document LangChain avec métadonnées enrichies
    """
    raw_docs: List[Document] = []

    for path in file_paths:
        suffix = Path(path).suffix.lower()
        try:
            if suffix == ".pdf":
                raw_docs.extend(_load_pdf(path))
            elif suffix in (".docx", ".doc"):
                raw_docs.extend(_load_docx(path))
            else:
                logger.warning(f"⚠️ Format non supporté par loader_pdf : {suffix}")
        except Exception as e:
            logger.error(f"❌ Erreur chargement {path} : {e}")

    if not raw_docs:
        logger.warning("⚠️ Aucun document chargé.")
        return []

    return _split(raw_docs) if split else raw_docs