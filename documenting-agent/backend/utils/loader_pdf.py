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
