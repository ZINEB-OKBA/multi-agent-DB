"""
utils/loader_pdf.py
--------------------
Charge PDF/Word depuis des chemins disque (pas Streamlit UploadedFile).
"""

import logging
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger       = logging.getLogger(__name__)
CHUNK_SIZE   = 1000
CHUNK_OVERLAP = 150


def _load_pdf(file_path: str) -> List[Document]:
    from langchain_community.document_loaders import PyPDFLoader
    logger.info(f"📄 PDF : {file_path}")
    docs = PyPDFLoader(file_path).load()
    # Ajoute le nom du fichier dans les métadonnées
    for d in docs:
        d.metadata["source"] = Path(file_path).name
    logger.info(f"   → {len(docs)} page(s)")
    
    # Si le texte extrait est vide, on tente une extraction par OCR !
    full_text = "".join(d.page_content for d in docs).strip()
    if not full_text:
        logger.info("⚠️ Aucun texte extrait par PyPDFLoader. Tentative d'OCR via pdf2image et pytesseract...")
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            # Convertir le PDF en images
            images = convert_from_path(file_path)
            ocr_docs = []
            for i, img in enumerate(images):
                # Utiliser tesseract pour extraire le texte de l'image (Français + Anglais)
                text = pytesseract.image_to_string(img, lang="fra+eng")
                ocr_docs.append(Document(
                    page_content=text,
                    metadata={"source": Path(file_path).name, "page": i}
                ))
            logger.info(f"   → OCR réussi. {len(ocr_docs)} page(s) extraite(s) par OCR.")
            return ocr_docs
        except Exception as ocr_err:
            logger.error(f"❌ Échec de l'OCR sur {file_path} : {ocr_err}")
            
    return docs


def _load_docx(file_path: str) -> List[Document]:
    from langchain_community.document_loaders import Docx2txtLoader
    logger.info(f"📝 DOCX : {file_path}")
    docs = Docx2txtLoader(file_path).load()
    for d in docs:
        d.metadata["source"] = Path(file_path).name
    logger.info(f"   → {len(docs)} section(s)")
    return docs


def _split(raw_docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = CHUNK_SIZE,
        chunk_overlap = CHUNK_OVERLAP,
        separators    = ["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(raw_docs)
    logger.info(f"✂️  {len(raw_docs)} doc(s) → {len(chunks)} chunk(s)")
    return chunks


def load_uploaded_files_from_paths(file_paths: List[str]) -> List[Document]:
    """
    Charge des fichiers depuis leurs chemins disque.
    Utilisé par IndexService (FastAPI).
    """
    raw_docs: List[Document] = []
    for path in file_paths:
        suffix = Path(path).suffix.lower()
        try:
            if suffix == ".pdf":
                raw_docs.extend(_load_pdf(path))
            elif suffix in (".docx", ".doc"):
                raw_docs.extend(_load_docx(path))
        except Exception as e:
            logger.error(f"❌ Erreur chargement {path} : {e}")

    if not raw_docs:
        return []
    return _split(raw_docs)
