# Methodology

## Dataset access

- **Source:** [ThreatCluster / threat-incident-clusters](https://huggingface.co/datasets/threatcluster/threat-incident-clusters)
- **License:** CC-BY-4.0
- **Access method:** Hugging Face `datasets` Python library only
- **No** local dataset dumps (CSV/JSON) are committed or required at runtime after ingestion

Ingestion notebook loads the `train` split, normalizes fields, and writes MongoDB documents.

---

## Text preprocessing

Implemented in `src.preprocessing`:

1. **Cleaning** (`clean_text`)
   - Lowercasing (optional)
   - URL / email stripping
   - Whitespace normalization
   - Optional punctuation removal

2. **Tokenization** (`tokenize_and_clean`)
   - Simple whitespace / regex tokenization
   - Stopword removal (configurable list)

3. **TF-IDF** (`03_nlp_preprocessing.ipynb`)
   - `TfidfVectorizer`: max_features=10 000, ngram_range=(1, 2), min_df=3, max_df=0.90, sublinear_tf=True
   - Fitted on combined title + summary + keywords
   - Vectorizer persisted as `models/tfidf_vectorizer.joblib`

4. **Entities**
   - Dataset provides structured entity groups (CVE, company, malware, country, sector, ATT&CK, …)
   - Normalized via `normalize_entities_document` / `flatten_entities`

---

## Embeddings & semantic search

- **Model:** `sentence-transformers` — `all-MiniLM-L6-v2` (384-dim)
- **Input:** cleaned title + summary per incident
- **Normalization:** L2 so cosine similarity ≡ dot product
- **Artifacts:** `models/embeddings.npy`, `models/cluster_ids.npy`
- **Retrieval:** top-k by cosine similarity (`src.models.predictors.find_similar_incidents`)

Evaluation (no gold pairs):

- Self-retrieval@1 on a random sample
- Qualitative review of hand-written security queries
- Query latency measurement

---

## Machine learning tasks

### 1. Urgency classification

| Item | Detail |
|------|--------|
| **Target** | `urgency_level` from the dataset |
| **Features** | TF-IDF of combined text |
| **Models** | Logistic Regression (`class_weight=balanced`), Linear SVM |
| **Selection** | Best macro-F1 on stratified hold-out (20%) |
| **Artifact** | `models/urgency_classifier.joblib` |

### 2. Priority classification

| Item | Detail |
|------|--------|
| **Target** | Project-defined label derived from scores + urgency |
| **Heuristic** | critical if threat≥80 or urgency=critical (etc.); else high / medium / low |
| **Features** | `threat_score`, `severity_score`, `credibility_score`, `source_count`, `article_count` |
| **Model** | Random Forest (200 trees, max_depth=12, balanced) |
| **Artifact** | `models/priority_model.joblib` + `priority_meta.joblib` |

> Priority labels are **not** industry-standard severity ratings. They exist so the project can demonstrate a second supervised task with structured features.

### 3. Metrics reported

- Accuracy, macro F1, weighted F1, precision, recall
- Confusion matrices
- Feature importances (priority RF)
- Semantic: self-retrieval@1, latency

See `06_evaluation.ipynb` and `models/evaluation_report.json`.

---

## Indexing strategy (MongoDB)

| Index | Purpose |
|-------|---------|
| `cluster_id` (unique) | Primary lookup |
| `urgency_level` | Filter |
| `threat_score` / `severity_score` (desc) | Ranking / range filters |
| `first_reported` / `last_reported` | Temporal queries |
| `source_count` / `article_count` | Volume filters |
| Text index on `title`, `summary`, `keywords` | Keyword search |

---

## Streamlit application methods

| Page | Method |
|------|--------|
| Home | KPI aggregates + recent documents from MongoDB |
| Incident Search | Mongo text/regex filters **or** embedding cosine search |
| Incident Explorer | `find_incident_by_id` + entity/source display |
| Threat Analytics | Sampled frame → Plotly histograms, pie, lines, heatmap |
| Entity Explorer | Aggregation on `entities.*` arrays |
| AI / NLP Insights | Load joblib + embeddings; call `predict_*` / `find_similar_*` |
| About | Static methodology + live connectivity status |

All pages use `st.cache_data` / `st.cache_resource` for Mongo queries and model loads.

---

## Reproducibility

- Fixed `random_state=42` for train/test splits and RF
- Model hyperparameters documented in notebook cells and `metadata.json`
- Environment pinned via `requirements.txt` / `pyproject.toml`
- Config via `.env` (see `.env.example`)

---

## What is intentionally out of scope

- Deep learning sequence models / LLM fine-tuning
- Real-time streaming ingestion
- Storing raw malware samples or full article HTML
- Multi-tenant auth / production hardening (demo-oriented)
