import os
import sys
import base64
import tempfile
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import requests

# 🌟 Étape 1 : Aligner les chemins pour importer les modules du sous-dossier `utils`
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.loader_pdf import load_uploaded_files_from_paths
from utils.loader_excel import load_dataframe
from utils.vector_store import load_faiss_index, save_faiss_index, build_faiss_index

# ⚙️ Configuration de la Base de Données PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "Motuldb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
SPRING_BOOT_CALLBACK_URL = os.getenv("SPRING_BOOT_CALLBACK_URL", "http://localhost:8080/api/internal/documents/callback")


def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    # ✅ FIX: autocommit=False so we control transactions explicitly
    conn.autocommit = False
    return conn


def index_documents_job():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # ─────────────────────────────────────────────────────────────────────
        # STEP 1 — Atomically claim documents with FOR UPDATE SKIP LOCKED
        #          This prevents the cron from touching rows already being
        #          processed by FastAPI (or another cron instance).
        # ─────────────────────────────────────────────────────────────────────
        query_select = """
            SELECT d.id, d.file_name, d.content, p.name AS project_name
            FROM documents d
            JOIN projects p ON d.project_id = p.id
            WHERE d.is_indexed = FALSE
              AND d.indexing = FALSE
            FOR UPDATE OF d SKIP LOCKED;
        """
        cursor.execute(query_select)
        pending_docs = cursor.fetchall()

        if not pending_docs:
            print(f"[{datetime.now()}] 💤 Aucun document en attente d'indexation.")
            conn.rollback()
            return

        print(f"[{datetime.now()}] 🚀 Tâche planifiée : {len(pending_docs)} document(s) à traiter.")

        # ─────────────────────────────────────────────────────────────────────
        # STEP 2 — Immediately mark all claimed rows as indexing=TRUE and
        #          commit so FastAPI sees them as "in progress" right away.
        # ─────────────────────────────────────────────────────────────────────
        doc_ids = [doc['id'] for doc in pending_docs]
        cursor.execute(
            """
            UPDATE documents
            SET indexing = TRUE
            WHERE id = ANY(%s);
            """,
            (doc_ids,)
        )
        conn.commit()  # ✅ Lock committed — FastAPI won't touch these rows now
        print(f"[{datetime.now()}] 🔒 {len(doc_ids)} document(s) verrouillés (indexing=TRUE).")

    except Exception as db_err:
        conn.rollback()
        print(f"🚨 Erreur critique lors de la sélection/verrouillage : {db_err}")
        cursor.close()
        conn.close()
        return

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3 — Process each document individually with its own commit
    # ─────────────────────────────────────────────────────────────────────────
    for doc in pending_docs:
        doc_id = doc['id']
        file_name = doc['file_name']
        project_name = doc['project_name'].strip()
        base64_content = doc['content']
        suffix = os.path.splitext(file_name)[1].lower()
        temp_filepath = None

        print(f"\n🔄 Traitement en cours : {file_name} (Projet: {project_name})")

        try:
            # 3a. Decode and write to a temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                file_bytes = base64.b64decode(base64_content)
                tmp.write(file_bytes)
                temp_filepath = tmp.name

            # 3b. Branch by file type
            if suffix in (".pdf", ".docx", ".doc"):
                print("📄 Type détecté : Document textuel. Lancement de loader_pdf...")
                chunks = load_uploaded_files_from_paths([temp_filepath])

                if not chunks:
                    raise ValueError("Le fichier n'a généré aucun chunk de texte exploitable.")

                for chunk in chunks:
                    chunk.metadata["source"] = file_name
                    chunk.metadata["project"] = project_name

                project_index_path = os.path.join("data", project_name, "faiss_index")
                os.makedirs(os.path.dirname(project_index_path), exist_ok=True)

                existing_vectorstore = load_faiss_index(project_index_path)
                if existing_vectorstore is not None:
                    print("➕ Index existant trouvé. Fusion des nouveaux vecteurs...")
                    existing_vectorstore.add_documents(chunks)
                    save_faiss_index(existing_vectorstore, project_index_path)
                else:
                    print("🆕 Aucun index trouvé. Initialisation d'une nouvelle structure FAISS...")
                    build_faiss_index(chunks, save_path=project_index_path)

            elif suffix in (".csv", ".xlsx", ".xls", ".xlsm"):
                print("📊 Type détecté : Tableau de données. Lancement de loader_excel...")
                df = load_dataframe(temp_filepath)
                print(f"✅ Fichier table valide : {df.shape[0]} lignes × {df.shape[1]} colonnes détectées.")

            else:
                raise ValueError(f"Extension non supportée : '{suffix}'")

            # 3c. Cleanup temp file
            if temp_filepath and os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

            # 3d. ✅ Mark as successfully indexed and COMMIT immediately
            cursor.execute(
                """
                UPDATE documents
                SET is_indexed = TRUE,
                    indexing   = FALSE,
                    index_error = NULL,
                    indexed_at  = %s
                WHERE id = %s;
                """,
                (datetime.now(), doc_id)
            )
            conn.commit()  # ✅ Each document committed independently
            print(f"💾 [PostgreSQL] is_indexed=TRUE commité avec succès pour : {file_name}")

            # 3e. Notify Spring Boot of success
            try:
                requests.post(
                    SPRING_BOOT_CALLBACK_URL,
                    json={"documentId": doc_id, "success": True, "error": None},
                    timeout=5
                )
                print(f"📞 Spring Boot notifié avec succès pour le document ID {doc_id}")
            except Exception as cb_err:
                print(f"⚠️ Impossible de contacter Spring Boot : {cb_err}")

        except Exception as e:
            # ─────────────────────────────────────────────────────────────────
            # STEP 4 — On failure: rollback any pending state, reset the row,
            #          then commit the failure so the row isn't stuck forever.
            # ─────────────────────────────────────────────────────────────────
            conn.rollback()  # Discard any partial write for this document

            error_msg = f"Erreur Traitement Cron : {str(e)}"
            print(f"❌ Échec de l'indexation pour {file_name} : {error_msg}")

            try:
                cursor.execute(
                    """
                    UPDATE documents
                    SET is_indexed  = FALSE,
                        indexing    = FALSE,
                        index_error = %s
                    WHERE id = %s;
                    """,
                    (error_msg, doc_id)
                )
                conn.commit()  # ✅ Commit the failure state so row is unlocked
            except Exception as db_fail_err:
                conn.rollback()
                print(f"🚨 Impossible d'écrire l'erreur en base pour {file_name} : {db_fail_err}")

            # Notify Spring Boot of failure
            try:
                requests.post(
                    SPRING_BOOT_CALLBACK_URL,
                    json={"documentId": doc_id, "success": False, "error": error_msg},
                    timeout=5
                )
            except Exception:
                pass

            # Cleanup temp file on error
            if temp_filepath and os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 5 — Close DB connection
    # ─────────────────────────────────────────────────────────────────────────
    cursor.close()
    conn.close()
    print(f"\n[{datetime.now()}] ✅ Tâche cron terminée.")


if __name__ == "__main__":
    index_documents_job()