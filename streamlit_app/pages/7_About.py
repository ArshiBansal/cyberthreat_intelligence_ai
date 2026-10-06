"""
About / Methodology page — dataset attribution, architecture, limitations, ethics.

Fully independent of Jupyter notebooks.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import settings, validate_config
from src.db import ping_database, count_incidents
from src.models.loaders import list_available_models, get_models_dir, load_model_metadata_file

st.set_page_config(
    page_title="About — Threat Intelligence",
    page_icon="ℹ️",
    layout="wide",
)

st.title("ℹ️ About / Methodology")
st.caption("Architecture, dataset attribution, model information, limitations, and ethical use")


# ---------------------------------------------------------------------------
# Live status (optional)
# ---------------------------------------------------------------------------
mongo_ok = False
n_incidents = 0
try:
    validate_config()
    mongo_ok = ping_database()
    if mongo_ok:
        n_incidents = count_incidents()
except Exception:
    pass

c1, c2, c3 = st.columns(3)
c1.metric("MongoDB", "Connected" if mongo_ok else "Unavailable")
c2.metric("Incidents loaded", f"{n_incidents:,}" if mongo_ok else "—")
try:
    arts = list_available_models()
    c3.metric("Model artifacts", str(len(arts)))
except Exception:
    c3.metric("Model artifacts", "—")

st.divider()


# ---------------------------------------------------------------------------
# Project overview
# ---------------------------------------------------------------------------
st.header("Project overview")

st.markdown(
    """
**Threat Incident Intelligence Platform** is a defensive cybersecurity analytics system
that turns incident summaries and structured threat metadata into searchable,
explainable, ML-assisted intelligence.

| Layer | Technology |
|-------|------------|
| Language | Python |
| Database | MongoDB (PyMongo) |
| Analytics | Jupyter Notebook |
| Application | Streamlit |
| NLP / ML | scikit-learn, sentence-transformers, TF-IDF |
| Dataset access | Hugging Face `datasets` library only (no local dataset files) |

**Architecture principle:** Jupyter notebooks and the Streamlit app are **fully independent**.
Both connect directly to MongoDB and may share reusable Python modules under `src/`.
Neither interface executes or imports the other.
"""
)

st.header("Architecture")

st.code(
    """Hugging Face Dataset  →  Python ingestion  →  MongoDB
                                              ↑
                         Jupyter notebooks ───┤  (PyMongo)
                         Streamlit app     ───┘

Shared: src/config, src/db, src/preprocessing, src/models, src/utils
Not shared at runtime: notebooks  spawns  Streamlit (or vice versa)
""",
    language="text",
)

st.header("Dataset attribution")

st.markdown(
    """
**Source:** ThreatCluster — *threat-incident-clusters*  
**License:** CC-BY-4.0  
**Access:** [https://huggingface.co/datasets/threatcluster/threat-incident-clusters](https://huggingface.co/datasets/threatcluster/threat-incident-clusters)

Suggested citation:

```text
@misc{threatcluster_threat_incident_clusters,
  title  = {Threat incident clusters},
  author = {ThreatCluster},
  year   = {2026},
  url    = {https://huggingface.co/datasets/threatcluster/threat-incident-clusters}
}
```

The dataset is loaded **only** via the Hugging Face `datasets` Python library.
No dataset CSV/JSON files are committed to the repository.
"""
)

st.header("Model information")

meta = {}
try:
    meta = load_model_metadata_file() or {}
except Exception:
    pass

if meta:
    st.json(meta)
else:
    st.info(
        "No `models/metadata.json` found yet. "
        "Train models with notebooks `03_nlp_preprocessing.ipynb` → "
        "`05_ml_training.ipynb` (and optionally `04_embeddings_similarity.ipynb`)."
    )

try:
    models_dir = get_models_dir()
    files = sorted(p.name for p in models_dir.iterdir() if p.is_file())
    if files:
        st.markdown("**Artifacts on disk:**")
        for f in files:
            st.write(f"- `{f}`")
except Exception:
    pass

st.header("What the models do")

st.markdown(
    """
| Task | Method | Notes |
|------|--------|-------|
| **Urgency classification** | TF-IDF + Logistic Regression / Linear SVM | Predicts dataset `urgency_level` from title/summary/keywords |
| **Priority classification** | Random Forest on structured scores | Project-defined Low/Medium/High/Critical heuristic — not an industry standard |
| **Semantic search** | sentence-transformers (`all-MiniLM-L6-v2`) + cosine similarity | Retrieves related incidents for free-text queries |

Predictions are **assistive ranking signals**. They are not verified security assessments.
"""
)

st.header("Limitations")

st.markdown(
    """
1. Titles and summaries in the dataset are **model-generated** and may contain errors.
2. ThreatCluster scores are **editorial ranking signals**, not a universal severity scale.
3. Priority labels used in training are **project-defined heuristics**, not analyst ground truth.
4. Semantic search has **no gold similar-pair labels**; evaluation is qualitative + self-retrieval checks.
5. The dataset does **not** include full source-article text or raw indicators (IPs, hashes, domains).
6. Class imbalance in urgency levels can make accuracy look higher than macro-F1 suggests.
"""
)

st.header("Ethical use")

st.warning(
    """
**Defensive use only.**

- Use this system for cybersecurity research, education, and defensive analytics.
- Do **not** use it to target, harass, or profile victims.
- Do **not** present model predictions as verified facts.
- Keep MongoDB credentials in environment variables; never commit secrets to Git.
"""
)

st.header("How to run")

st.markdown(
    """
**Notebooks (Stage A — demo without Streamlit)**

```bash
jupyter lab   # or jupyter notebook
# Run in order: 01 → 02 → 03 → 04 → 05 → 06
```

**Streamlit (Stage B)**

```bash
# from project root
streamlit run streamlit_app/pages/1_Home.py
# multipage sidebar lists all pages under streamlit_app/pages/
```

**Environment**

```bash
cp .env.example .env   # set MONGODB_URI, MONGODB_DB
pip install -r requirements.txt
```
"""
)

st.header("Repository layout (reference)")

st.code(
    """threat-incident-intelligence-platform/
├── .env / .env.example
├── requirements.txt / pyproject.toml
├── src/                    # shared library (notebooks + Streamlit)
│   ├── config.py
│   ├── db/
│   ├── preprocessing/
│   ├── models/
│   └── utils/
├── notebooks/              # 01 … 06 independent suite
├── streamlit_app/pages/    # 1_Home … 7_About
└── models/                 # joblib / npy artifacts (gitignored large files)
""",
    language="text",
)

st.divider()
st.caption(
    f"Configured database: **{settings.mongodb_db}** · "
    "Threat Incident Intelligence Platform · CC-BY-4.0 dataset attribution required."
)
