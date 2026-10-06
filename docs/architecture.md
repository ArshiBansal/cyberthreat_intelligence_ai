# Architecture

## Overview

The **Threat Incident Intelligence Platform** is a defensive cybersecurity analytics system that ingests structured threat-incident summaries, stores them in MongoDB, and exposes both a Jupyter notebook suite and a Streamlit application for exploration, NLP feature engineering, classical ML prediction, and semantic search.

**Core principle:** Jupyter notebooks and the Streamlit app are **fully independent at runtime**. Both talk only to MongoDB (and optional on-disk model artifacts). Neither interface imports or executes the other.

```
Hugging Face Dataset  →  Python ingestion  →  MongoDB
                                              ↑
                         Jupyter notebooks ───┤  (PyMongo)
                         Streamlit app     ───┘

Shared library: src/
  config · db · preprocessing · models · utils
```

---

## Components

| Component | Role |
|-----------|------|
| **Hugging Face `datasets`** | Sole dataset access path — no local CSV/JSON dataset files |
| **MongoDB** | Single source of truth for incident documents |
| **`src/` package** | Shared Python library used by notebooks *and* Streamlit |
| **Notebooks (`01`–`06`)** | Offline analytics, training, evaluation (Stage A demo) |
| **Streamlit app** | Interactive UI for search, exploration, predictions (Stage B) |
| **`models/`** | Joblib / NumPy artifacts produced by notebooks, consumed by Streamlit |

---

## Data flow

1. **Ingestion** (`01_data_ingestion.ipynb`)
   - `load_dataset("threatcluster/threat-incident-clusters")`
   - Validate / normalize fields
   - Clean text via `src.preprocessing`
   - Bulk-insert into MongoDB `incidents` collection
   - Create indexes (`cluster_id`, urgency, scores, text)

2. **Exploration** (`02_eda.ipynb`, Streamlit Home / Analytics)
   - Read from MongoDB only
   - Distributions, temporal trends, entity frequencies

3. **NLP** (`03_nlp_preprocessing.ipynb`)
   - Tokenization, TF-IDF fit
   - Persist `tfidf_vectorizer.joblib` + sparse matrix

4. **Embeddings** (`04_embeddings_similarity.ipynb`)
   - `sentence-transformers` (`all-MiniLM-L6-v2`)
   - Persist `embeddings.npy` + `cluster_ids.npy`

5. **ML training** (`05_ml_training.ipynb`)
   - Urgency classifier (TF-IDF + LR / Linear SVM)
   - Priority classifier (Random Forest on structured scores)
   - Persist `urgency_classifier.joblib`, `priority_model.joblib`, `metadata.json`

6. **Evaluation** (`06_evaluation.ipynb`)
   - Hold-out metrics, semantic self-retrieval, latency
   - Write `evaluation_report.json`

7. **Streamlit**
   - Pages read MongoDB via `src.db`
   - Optionally load artifacts from `models/` via `src.models`
   - Never call notebook code

---

## MongoDB design

**Database:** value of `MONGODB_DB` (default `threat_intel`)

**Primary collection:** `incidents`

| Field | Type | Notes |
|-------|------|-------|
| `cluster_id` | string | Unique key (indexed) |
| `title` / `title_clean` | string | Original + cleaned |
| `summary` / `summary_clean` | string | Original + cleaned |
| `entities` | object | `{cve, company, malware, country, sector, mitre_attack, …}` |
| `keywords` | string[] | |
| `sources` | string[] | |
| `source_count` / `article_count` | int | |
| `threat_score` / `severity_score` / `credibility_score` | float | Dataset ranking signals |
| `urgency_level` | string | critical / high / medium / low / … |
| `first_reported` / `last_reported` | datetime | |
| `url` | string | |
| `ingested_at` | datetime | Ingestion timestamp |

Optional collections (future / extended use): `predictions`, `embeddings_meta`.

---

## Shared `src/` layout

```
src/
├── config.py          # Settings from .env (URI, DB name, paths)
├── db/
│   ├── connection.py  # Singleton MongoClient, get_collection helpers
│   └── queries.py     # find / aggregate / KPI helpers
├── preprocessing/
│   ├── text.py        # clean_text, tokenize, TF-IDF corpus builders
│   └── entities.py    # normalize / flatten entity documents
├── models/
│   ├── loaders.py     # joblib / npy loaders, models/ path
│   └── predictors.py  # predict_urgency, predict_priority, find_similar
└── utils/
    └── helpers.py     # logging, dates, safe casts, batching, timers
```

---

## Streamlit layout

```
streamlit_app/
├── app.py                 # Entry point (landing page)
├── pages/
│   ├── 1_Home.py
│   ├── 2_Incident_Search.py
│   ├── 3_Incident_Explorer.py
│   ├── 4_Threat_Analytics.py
│   ├── 5_Entity_Explorer.py
│   ├── 6_AI_NLP_Insights.py
│   └── 7_About.py
└── components/
    ├── charts.py          # Plotly helpers
    └── filters.py         # Sidebar filter widgets
```

Run:

```bash
streamlit run streamlit_app/app.py
```

---

## Configuration

All secrets and environment-specific values live in `.env` (never committed):

```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=threat_intel
HF_TOKEN=          # optional
```

Loaded by `src.config.Settings` via `python-dotenv`.

---

## Independence guarantees

| Rule | Enforcement |
|------|-------------|
| Notebooks never import Streamlit | No `streamlit` imports in `notebooks/` |
| Streamlit never runs notebooks | No `nbformat` / `papermill` / subprocess notebook calls |
| Both use the same DB layer | Only `src.db.*` for Mongo access |
| Dataset not stored in repo | Hugging Face API / library only |
