<p align="center">
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=28&duration=4000&pause=800&color=3B82F6&center=true&vCenter=true&width=800&lines=Threat+Incident+Intelligence+Platform;MongoDB+%2B+NLP+%2B+Classical+ML;Notebooks+%26+Streamlit+Independent" alt="Typing SVG" />
</p>

<p align="center">
<strong>Defensive cybersecurity analytics</strong> over structured threat-incident summaries from the<br>
<a href="https://huggingface.co/datasets/threatcluster/threat-incident-clusters">ThreatCluster</a> dataset — searchable, explainable, and ML-assisted.
</p>

<p align="center">
<img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"/>
<img src="https://img.shields.io/badge/Dataset-ThreatCluster-orange" alt="Dataset"/>
<img src="https://img.shields.io/badge/DB-MongoDB-brightgreen?logo=mongodb&logoColor=white" alt="MongoDB"/>
<img src="https://img.shields.io/badge/App-Streamlit-red" alt="Streamlit"/>
<img src="https://img.shields.io/badge/Author-ARSHI%20BANSAL-blueviolet" alt="Author"/>
</p>

---

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=3B82F6&vCenter=true&width=500&lines=Problem" alt="Problem"/>

Security teams face a flood of publicly reported cyber incidents. Feeds are noisy, inconsistently structured, and hard to search or prioritise at scale. Analysts need to:

- Store incident summaries in a **queryable database**
- Explore trends, entities, and scores interactively
- Apply **classical NLP and ML** to rank urgency and priority
- Retrieve related incidents with **semantic search**

without coupling offline notebooks to a live app, and without shipping large local dataset files in the repository.

---

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=3B82F6&vCenter=true&width=500&lines=Objectives" alt="Objectives"/>

1. **Ingest** ThreatCluster via the Hugging Face `datasets` API into MongoDB (no dataset files committed).
2. **Explore** distributions, temporal trends, keywords, and entities (CVE, company, malware, country, sector, ATT&CK).
3. **Engineer NLP features** — cleaning, TF-IDF, and sentence embeddings.
4. **Train & evaluate** urgency classification and project-defined priority classification.
5. **Ship** a multipage Streamlit app for search, exploration, analytics, entities, and AI insights.
6. Keep **Jupyter and Streamlit fully independent** at runtime — both use MongoDB + shared `src/` only.
7. **Document** architecture, methodology, limitations, and defensive-only ethics.

---

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=3B82F6&vCenter=true&width=500&lines=Dataset" alt="Dataset"/>

**ThreatCluster — threat-incident-clusters**

| Item | Detail |
|------|--------|
| Source | [Hugging Face – threatcluster/threat-incident-clusters](https://huggingface.co/datasets/threatcluster/threat-incident-clusters) |
| License | **CC-BY-4.0** |
| Access | Hugging Face `datasets` library **only** |
| Content | Titles, summaries, entities, keywords, sources, threat/severity/credibility scores, urgency labels |

> No local dataset CSV/JSON dumps are stored in this repo. After ingestion, **MongoDB** is the working store.

```bibtex
@misc{threatcluster_threat_incident_clusters,
  title  = {Threat incident clusters},
  author = {ThreatCluster},
  year   = {2026},
  url    = {https://huggingface.co/datasets/threatcluster/threat-incident-clusters}
}
```

---

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=3B82F6&vCenter=true&width=500&lines=Architecture" alt="Architecture"/>

```text
Hugging Face Dataset  →  Python ingestion  →  MongoDB
                                              ↑
                         Jupyter notebooks ───┤  (PyMongo)
                         Streamlit app     ───┘

Shared library: src/config · src/db · src/preprocessing · src/models · src/utils
```

| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| Database | MongoDB (PyMongo) |
| Analytics | Jupyter Notebook |
| Application | Streamlit |
| NLP / ML | scikit-learn, sentence-transformers, TF-IDF |

More detail: [`docs/architecture.md`](docs/architecture.md) · [`docs/methodology.md`](docs/methodology.md)

---

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=3B82F6&vCenter=true&width=500&lines=Installation" alt="Installation"/>

```bash
# Clone
git clone <your-repo-url>
cd threat-incident-intelligence-platform

# Virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows

# Dependencies
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env — set MONGODB_URI and MONGODB_DB
```

| Variable | Example |
|----------|---------|
| `MONGODB_URI` | `mongodb://localhost:27017` |
| `MONGODB_DB` | `threat_intel` |
| `HF_TOKEN` | optional (public dataset) |

---

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=3B82F6&vCenter=true&width=500&lines=Quick+Start" alt="Quick Start"/>

### Notebooks (recommended order)

```bash
jupyter lab
# or: jupyter notebook
```

| # | Notebook | Purpose |
|---|----------|---------|
| 01 | `01_data_ingestion.ipynb` | HF API → clean → MongoDB + indexes |
| 02 | `02_eda.ipynb` | Distributions, trends, entities |
| 03 | `03_nlp_preprocessing.ipynb` | TF-IDF vectorizer |
| 04 | `04_embeddings_similarity.ipynb` | Sentence embeddings + search demos |
| 05 | `05_ml_training.ipynb` | Urgency + priority models |
| 06 | `06_evaluation.ipynb` | Metrics & evaluation report |

### Streamlit app

```bash
# from project root
streamlit run streamlit_app/app.py
```

| Page | Purpose |
|------|---------|
| Home | KPIs, urgency chart, recent incidents |
| Incident Search | Keyword + semantic search |
| Incident Explorer | Single-incident deep dive |
| Threat Analytics | Scores, trends, correlation |
| Entity Explorer | CVE, company, malware, ATT&CK, … |
| AI / NLP Insights | Predict urgency/priority, similar incidents |
| About | Architecture, attribution, ethics |

---

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=3B82F6&vCenter=true&width=500&lines=Models" alt="Models"/>

| Task | Method | Artifact |
|------|--------|----------|
| **Urgency classification** | TF-IDF + Logistic Regression / Linear SVM | `models/urgency_classifier.joblib` |
| **Priority classification** | Random Forest on structured scores | `models/priority_model.joblib` |
| **Semantic search** | `all-MiniLM-L6-v2` + cosine similarity | `models/embeddings.npy` |

> Priority labels are **project-defined heuristics**, not an industry severity standard.

---

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=3B82F6&vCenter=true&width=500&lines=Ethics+%26+Limitations" alt="Ethics"/>

- **Defensive use only** — research, education, defensive analytics
- Titles/summaries may be model-generated and imperfect
- Dataset scores are ranking signals, not universal severity ratings
- Do **not** present model predictions as verified security facts

Full write-up: [`docs/ethics_limitations.md`](docs/ethics_limitations.md)

---

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=3B82F6&vCenter=true&width=500&lines=License" alt="License"/>

This **software** is released under the **MIT License**.  
Copyright (c) 2026 **ARSHI BANSAL**.

```text
MIT License

Copyright (c) 2026 ARSHI BANSAL

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

> **Note:** The ThreatCluster dataset is licensed under **CC-BY-4.0** and requires attribution.

---

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=3B82F6&vCenter=true&width=500&lines=Acknowledgements" alt="Acknowledgements"/>

- [ThreatCluster dataset](https://huggingface.co/datasets/threatcluster/threat-incident-clusters)
- Hugging Face `datasets` & `sentence-transformers`
- MongoDB, scikit-learn, Streamlit, Plotly

---

<p align="center">
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=4000&pause=1200&color=3B82F6&center=true&vCenter=true&width=700&lines=Defensive+cybersecurity+analytics;MongoDB+%E2%80%A2+NLP+%E2%80%A2+Classical+ML+%E2%80%A2+Streamlit" alt="Footer"/>
</p>
