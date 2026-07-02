import sys
import psycopg2
import re
import base64
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from agents.staffing_agent import run_staffing_agent

def main():
    # Inside docker compose network, db host is staffing_db
    conn = psycopg2.connect(
        host="staffing_db",
        port=5432,
        database="staffdb",
        user="postgres",
        password="Admin123"
    )
    cursor = conn.cursor()
    
    # Get excel content for project 2 (staff_excel)
    cursor.execute("SELECT file_name, content FROM documents;")
    docs = cursor.fetchall()
    
    docs_raw = []
    for doc in docs:
        file_name = doc[0]
        content = doc[1] or ""
        suffix = Path(file_name).suffix.lower()
        
        # Nettoyer le préfixe data-URL
        if ";base64," in content:
            pure = re.sub(r'^data:.*?;base64,', '', content)
        elif "," in content:
            pure = content.split(",")[1]
        else:
            pure = content

        pure = pure.strip().replace(" ", "").replace("\n", "")
        file_bytes = base64.b64decode(pure)
        docs_raw.append({
            "file_name": file_name,
            "file_bytes": file_bytes,
            "suffix": suffix
        })
        
    question = "presente cela dans un pie chart"
    history = [
        {"role": "user", "content": "donne les top 3 employer qui possede le salaire mensuelle le plus eleve"},
        {"role": "assistant", "content": "Voici les top 3 employés..."}
    ]
    print("Running staffing agent...")
    res = run_staffing_agent(question, docs_raw, history=history)
    
    print("=== ANSWER ===")
    print(res["answer"])
    
    print("=== CHARTS ===")
    for c in res["charts"]:
        print(f"Title: {c['title']}, Type: {c['type']}, Data keys: {c['chartjs']['data']['labels']}")
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
