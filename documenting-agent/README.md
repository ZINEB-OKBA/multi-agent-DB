# 🤖 Multi-Agent RAG — Groq + Llama-3.3-70B

Système de RAG multi-agent avec classification d'intention automatique.

## Architecture

```
Streamlit (app.py)
    └─→ Orchestrateur (classify_intent)
            ├─→ Agent PDF  → FAISS + nomic-embed-text (Ollama) + Llama-3.3
            └─→ Agent Excel → create_pandas_dataframe_agent + Llama-3.3
```

## Installation

### 1. Cloner et installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Configurer la clé API Groq

```bash
# .env
GROQ_API_KEY=your_groq_api_key_here
```

Obtenir une clé gratuite sur : https://console.groq.com

### 3. Lancer Ollama avec nomic-embed-text

```bash
# Installer Ollama : https://ollama.com
ollama pull nomic-embed-text
ollama serve
```

### 4. Lancer l'application

```bash
streamlit run app.py
```

## Utilisation

1. **Uploader des PDF/Word** → Cliquer sur "Indexer les documents"
2. **Uploader des CSV/Excel** → Cliquer sur "Charger les tableaux"
3. **Poser votre question** → L'orchestrateur route automatiquement vers le bon agent

## Structure des fichiers

```
/
├── .env                    # GROQ_API_KEY
├── app.py                  # Interface Streamlit
├── requirements.txt
├── data/
│   └── [nom_projet]/
│       ├── docs/           # PDF & Word
│       ├── tables/         # CSV & Excel
│       └── faiss_index/    # Index vectoriels
└── utils/
    ├── __init__.py
    ├── llm_factory.py      # Groq (Llama-3.3-70B)
    ├── loader_pdf.py       # Traitement PDF/Word
    ├── loader_excel.py     # Traitement CSV/Excel
    ├── vector_store.py     # FAISS
    └── orchestrator.py     # Classification + Routing
```

## Modèles utilisés

| Rôle | Modèle | Fournisseur |
|------|--------|-------------|
| LLM (génération + classification) | `llama-3.3-70b-versatile` | Groq Cloud |
| Embeddings (vectorisation) | `nomic-embed-text` | Ollama (local) |
