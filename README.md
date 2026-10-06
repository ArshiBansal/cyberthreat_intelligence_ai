# Threat Incident Intelligence Platform

Defensive cybersecurity analytics platform that turns structured threat-incident summaries into searchable, explainable, ML-assisted intelligence.

**Author:** ARSHI BANSAL · **License:** MIT · **Dataset:** [ThreatCluster](https://huggingface.co/datasets/threatcluster/threat-incident-clusters) (CC-BY-4.0)

---

## Problem

Security teams and researchers face a growing volume of publicly reported cyber incidents. Raw feeds are noisy, inconsistently structured, and hard to search or prioritize at scale. Analysts need a way to:

- Store incident summaries in a queryable database
- Explore trends, entities, and scores interactively
- Apply classical NLP and ML to rank urgency and priority
- Retrieve related incidents with semantic (meaning-based) search

without coupling offline analysis notebooks to a live application, and without redistributing large local dataset files.

---

## Objectives

1. **Ingest** the ThreatCluster incident-cluster dataset into MongoDB using only the Hugging Face `datasets` API (no dataset files committed to the repo).
2. **Explore** distributions, temporal trends, keywords, and structured entities (CVE, company, malware, country, sector, ATT&CK) through Jupyter notebooks and a Streamlit UI.
3. **Engineer NLP features** — text cleaning, TF-IDF baselines, and sentence embeddings for semantic retrieval.
4. **Train and evaluate** classical models for:
   - Urgency classification (TF-IDF + Logistic Regression / Linear SVM)
   - Priority classification (Random Forest on structured scores)
5. **Deliver** a multipage Streamlit application for search, incident exploration, analytics, entity browsing, and AI/NLP insights.
6. **Keep notebooks and Streamlit fully independent at runtime** — both use MongoDB and shared `src/` modules only; neither executes the other.
7. **Document** architecture, methodology, limitations, and ethical (defensive-only) use.

---

## Dataset

| Item | Detail |
|------|--------|
| **Name** | ThreatCluster — *threat-incident-clusters* |
| **Source** | [https://huggingface.co/datasets/threatcluster/threat-incident-clusters](https://huggingface.co/datasets/threatcluster/threat-incident-clusters) |
| **License** | CC-BY-4.0 |
| **Access** | Hugging Face `datasets` Python library only |
| **Content** | Incident-cluster summaries with titles, entities, keywords, sources, editorial threat/severity/credibility scores, and urgency labels |

**Citation:**

```text
@misc{threatcluster_threat_incident_clusters,
  title  = {Threat incident clusters},
  author = {ThreatCluster},
  year   = {2026},
  url    = {https://huggingface.co/datasets/threatcluster/threat-incident-clusters}
}
```

No local dataset CSV/JSON dumps are stored in this repository. After ingestion, MongoDB is the working store.

---

## Architecture

```
Hugging Face Dataset  →  Python ingestion  →  MongoDB
                                              ↑
                         Jupyter notebooks ───┤  (PyMongo)
                         Streamlit app     ───┘

Shared: src/config · src/db · src/preprocessing · src/models · src/utils
```

| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| Database | MongoDB (PyMongo) |
| Analytics | Jupyter Notebook |
| Application | Streamlit |
| NLP / ML | scikit-learn, sentence-transformers, TF-IDF |
| Dataset access | Hugging Face `datasets` |

Full detail: [docs/architecture.md](docs/architecture.md).

---

## Prerequisites

- Python 3.10+
- MongoDB (local or remote URI)
- Internet access for the first Hugging Face dataset load

---

## Setup

```bash
cd threat-incident-intelligence-platform

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env — set at least:
#   MONGODB_URI=mongodb://localhost:27017
#   MONGODB_DB=threat_intel
```

Optional: `HF_TOKEN` in `.env` for authenticated Hugging Face access.

```bash
# Notebooks
jupyter lab

# Streamlit (from project root)
streamlit run streamlit_app/app.py
```

---

## Machine learning tasks

| Task | Method | Artifact |
|------|--------|----------|
| Urgency classification | TF-IDF + Logistic Regression / Linear SVM | `models/urgency_classifier.joblib` |
| Priority classification | Random Forest on structured scores | `models/priority_model.joblib` |
| Semantic search | `all-MiniLM-L6-v2` + cosine similarity | `models/embeddings.npy`, `cluster_ids.npy` |

Priority labels are **project-defined heuristics**, not an industry severity standard.  
See [docs/methodology.md](docs/methodology.md).

---

## Configuration (`.env`)

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DB` | Database name | `threat_intel` |
| `HF_TOKEN` | Optional Hugging Face token | (empty if public) |

Never commit `.env`. Use `.env.example` as the template.

---

## Ethics & limitations

- **Defensive use only** — research, education, defensive analytics.
- Dataset titles/summaries may be model-generated and imperfect.
- Scores are ranking signals, not universal severity ratings.
- Do **not** present model predictions as verified security facts.

Full write-up: [docs/ethics_limitations.md](docs/ethics_limitations.md).

---

## License

This **software** is released under the [MIT License](LICENSE).  
Copyright (c) 2026 ARSHI BANSAL.

The **dataset** remains under CC-BY-4.0 (ThreatCluster); attribution is required.
