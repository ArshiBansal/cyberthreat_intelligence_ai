# Ethics & Limitations

## Intended use

This project is designed for **defensive cybersecurity research, education, and analytics** only.

Appropriate uses include:

- Studying patterns in publicly described security incidents
- Teaching NLP / classical ML on a real-world threat-intelligence-style corpus
- Prototyping search and prioritization workflows for SOC / CTI education labs

---

## Prohibited / discouraged uses

- Targeting, harassing, or profiling victims of cyber attacks
- Presenting model **predictions as verified facts** or as a substitute for professional incident response
- Building offensive tooling, exploit development aids, or operational targeting systems
- Scraping or redistributing dataset content in ways that violate the **CC-BY-4.0** license terms

---

## Dataset limitations

1. **Model-generated text**  
   Titles and summaries in ThreatCluster may contain factual errors, omissions, or hallucinated details. Always treat narrative fields as *indicative*, not authoritative.

2. **Editorial scores**  
   `threat_score`, `severity_score`, and related fields are ranking signals produced by the dataset authors’ pipeline. They are **not** a universal industry severity standard (e.g. not CVSS).

3. **No raw indicators**  
   The public dataset does not ship full article text, binary samples, or complete IoC feeds (IPs, hashes, domains). This project does not attempt to reconstruct them.

4. **Coverage bias**  
   Incidents reflect what was reported and clustered by the upstream pipeline. Under-reported regions, languages, or sectors will be under-represented.

5. **License obligation**  
   Downstream use must retain **CC-BY-4.0** attribution to ThreatCluster.

---

## Modeling limitations

1. **Priority labels are project-defined**  
   The Low / Medium / High / Critical priority used in training is a **heuristic** derived from dataset scores and urgency. It is not ground-truth analyst labeling and must not be marketed as such.

2. **Class imbalance**  
   Urgency levels are often skewed. Accuracy alone can look optimistic; prefer **macro F1** and confusion matrices when assessing quality.

3. **Semantic search has no gold pairs**  
   Evaluation relies on self-retrieval checks and qualitative review. Precision@k / Recall@k against human-curated neighbors was not computed.

4. **Domain shift**  
   Models trained on this corpus may degrade on other languages, proprietary ticketing text, or future incident styles.

5. **No calibrated probabilities guarantee**  
   Classifier probability outputs are useful for ranking inside the demo but are not rigorously calibrated for risk thresholds.

---

## Application / operational limitations

- Streamlit and notebooks are **demo-oriented**, not production multi-tenant services.
- Secrets must stay in environment variables (`.env`); never commit credentials.
- MongoDB should not be exposed publicly without authentication and network controls.
- Cached Streamlit data may lag behind DB updates until cache TTL expires or is cleared.

---

## Ethical commitments

| Commitment | Practice |
|------------|----------|
| Transparency | About page and this document state limitations clearly |
| Attribution | Dataset citation and license shown in UI and docs |
| Defensive framing | UI copy and README emphasize research / education use |
| No overclaim | Predictions labeled as model outputs, not verified assessments |
| Separation of concerns | Analytics path (notebooks) can be demonstrated without the web UI |

---

## Suggested user-facing disclaimer

> Model predictions and dataset scores are assistive signals for research and education.  
> They are **not** verified security assessments. Do not use them as the sole basis for operational response, legal action, or public attribution of attacks.

---

## Contact / responsible disclosure of project issues

If you find a safety, privacy, or licensing concern in this repository’s *code* (not in upstream threat data), open an issue or contact the project maintainer through the repository’s documented channel.
