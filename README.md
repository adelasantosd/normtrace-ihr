# NormTrace-IHR (IHR 2005+)

# NormTrace-IHR — Early Prototype

> **Status:** Legacy early prototype.  
> This repository documents an initial exploratory version of NormTrace-IHR. It is not the current methodological version of the project and should not be used as the active research dataset.

The current NormTrace-IHR Mexico Pilot is being developed as a separate, curated legal-institutional mapping infrastructure focused on domestic legal internalisation of the International Health Regulations (2005), the 2024 IHR amendments, and the WHO Pandemic Agreement.

This early prototype is preserved for transparency and version history.


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19677846.svg)](https://doi.org/10.5281/zenodo.19677846)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.2-blue)](CHANGELOG.md)

---

## What NormTrace-IHR does

NormTrace-IHR analyses whether a country's domestic normative architecture genuinely enables compliance with the International Health Regulations (IHR 2005, as amended through 2024). It does not measure administrative practice, infrastructure, or political commitment. It measures whether the legal instruments that would be needed to exercise specific IHR powers actually exist in a country's legal order, whether they are of sufficient normative rank, whether they designate a competent actor with explicit authority, and whether they are enforceable.

The tool addresses a structural limitation of the WHO's State Party Self-Assessment Annual Reporting (e-SPAR): self-reporting instruments are susceptible to optimistic bias and cannot distinguish between a country that has a robust legal framework and one that has a general health ministry mandate with no specific IHR powers. NormTrace-IHR produces a parallel, source-traceable score for IHR Core Capacity 1 (legislation, policy, and financing) that can be compared directly against the e-SPAR.

The analysis covers 29 IHR provisions across seven thematic blocks, selected on the basis of an administrative law criterion: provisions are included when they require an act of public authority that restricts private rights and therefore cannot be activated by policy, protocol, or institutional practice alone, but only by an express domestic legal norm. The full methodological justification is in `METHODOLOGY.md`.

---

## NormTrace as a framework

NormTrace-IHR is one instance of the broader NormTrace analytical framework, which applies the same legal assessment methodology to different international instruments. The current versions are:

| Version | International instrument | Zenodo |
|---------|--------------------------|--------|
| NormTrace-CRPD | Convention on the Rights of Persons with Disabilities | [[10.5281/zenodo.19676921](https://doi.org/10.5281/zenodo.19676921)]|
| NormTrace-IHR | International Health Regulations (IHR 2005+) | This repository |


Both versions share the core methodology: a structured discovery of the country's domestic normative corpus, a multi-instrument analysis tracing coverage gaps and intersectoral fragmentation, and a scored assessment comparable with the relevant international monitoring instrument. Researchers using both versions should cite each independently, as the corpora and analytical criteria differ by instrument.

---

## Who this is for

NormTrace-IHR is designed for two overlapping audiences. Researchers in global health governance, legislative studies, and comparative public law can use it to produce objective, reproducible assessments of IHR implementation across countries. Technical teams in health ministries, WHO/PAHO, and related organisations can use it to identify specific normative gaps and generate structured reform proposals, with traceability to the exact legal texts analysed.

The tool produces output in English, Spanish, and French. The interface language and the analysis output language are configured independently.

---

## Architecture

The application has three components:

**Backend** -- Python 3.12 with FastAPI. Manages the analytical workflow, communicates with the Anthropic API for corpus discovery and block-by-block analysis, and persists all results in PostgreSQL.

**Database** -- PostgreSQL. Stores countries, analyses, corpus items with source metadata (including the date each text was consulted and the date of its most recent reform), block results, scores, and reform proposals.

**Frontend** -- React (Vite). Provides the corpus validation interface, the sequential block analysis workflow, and the comparative dashboard.

The analytical logic is encoded as structured prompts in `backend/skill_prompt.py`. These prompts implement the methodology described in `METHODOLOGY.md`. Modifying the prompts without updating the methodology document would create a discrepancy between the documented and the actual analytical procedure.

---

## Repository structure

```
normtrace-ihr/
├── README.md
├── METHODOLOGY.md          Analytical methodology, full description
├── CHANGELOG.md            Version history
├── LICENSE                 MIT
├── CITATION.cff            Citation metadata for Zenodo and GitHub
├── CONTRIBUTING.md         Guidelines for contributions and issue reporting
├── backend/
│   ├── main.py             API endpoints
│   ├── models.py           Database models
│   ├── schemas.py          Request and response schemas
│   ├── skill_prompt.py     Analytical prompts (the core logic)
│   ├── database.py         Database connection
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   ├── components/
│   │   ├── lib/api.js
│   │   └── i18n/locales/   en.json, es.json, fr.json
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── railway.toml            Deploy configuration for Railway
└── docs/
    └── IHR_Observatory_Methodological_Note.docx
```

---

## Installation and local setup

### Requirements

- Python 3.12 or later
- Node.js 20 or later
- PostgreSQL 14 or later (or Docker)
- An Anthropic API key (`claude-sonnet-4` access required)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Set ANTHROPIC_API_KEY and DATABASE_URL in .env

uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive documentation is at `http://localhost:8000/docs`.

### Database (local, with Docker)

```bash
docker run -d \
  --name normtrace-db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=normtrace_ihr \
  -p 5432:5432 \
  postgres:16-alpine
```

Tables are created automatically on first application startup.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The application will be available at `http://localhost:5173`.

---

## Deployment

The backend is designed for deployment on Railway using the included `railway.toml` and `backend/Dockerfile`. The frontend deploys as a static build on any static hosting service (Vercel, Netlify, Railway static).

Full deployment instructions are in `METHODOLOGY.md` under the Software Architecture section.

Environment variables required for production:

```
ANTHROPIC_API_KEY     Your Anthropic API key
DATABASE_URL          PostgreSQL connection string (Railway provides this automatically)
FRONTEND_URL          URL of the deployed frontend (for CORS configuration)
VITE_API_URL          URL of the deployed backend (frontend only)
```

---

## Analytical workflow

A complete analysis for a new country proceeds in five stages:

1. The country is added with its ISO3 code, legal system type (civil law, common law, mixed), and whether it has a federal or unitary structure.

2. The system executes a structured web search across eight sectors to discover all normative instruments potentially relevant to IHR compliance. Each instrument is classified as: include (direct IHR intersection), review (possible relevance, requires text confirmation), discard (no intersection, documented with rationale), or laguna (existence known but text not obtained).

3. The classified corpus is presented to the user for validation. The user may add instruments not found in the automated search, reclassify items, and annotate reform status. Analysis does not begin until the user confirms the corpus.

4. The system analyses the confirmed corpus against the 29 selected IHR provisions, organised in seven blocks (A through G) plus a scoring block. Each block is analysed independently and results are stored in the database as the analysis proceeds. For each provision, the analysis applies a four-link enablement chain (norm, actor, authority, enforceability) across all corpus instruments.

5. Results are presented as a scored normative assessment, a gap table with attention-level classifications, and structured reform proposals specifying the recommended instrument type and the rationale for that choice over alternatives.

All source documents are stored with the date they were consulted and the date of their most recent reform. Users can inspect these dates for any analysis and decide whether a reform published since the consultation date warrants a new analysis.

---

## Versioning and reproducibility

Each analysis is timestamped and linked to the corpus instruments with their consultation dates and last-reform dates. This allows any analysis to be assessed for currency and repeated under the same conditions.

The version of the analytical prompts in use at the time of an analysis is not currently stored in the database. Researchers who require full reproducibility should record the git commit hash of the repository at the time of analysis alongside their results. This will be addressed in a future version through prompt versioning in the database schema.

---

## Known limitations

The analysis is limited to instruments whose text is publicly accessible or provided by the user. Unpublished implementing agreements and non-public inter-ministerial protocols cannot be captured by the automated discovery and must be introduced manually during corpus validation.

In federal systems, subnational legislation is flagged but not fully analysed in the default workflow. The extent to which federal obligations are implemented at subnational level requires a separate subnational corpus analysis.

The four-link enablement chain applies general principles of administrative law. Its application to a specific jurisdiction may require review by a practitioner familiar with that jurisdiction's interpretive traditions, particularly regarding the scope of implied powers and the constitutional status of regulatory instruments.

---

## How to cite

If you use NormTrace-IHR in published research, please cite the Zenodo record:

> Santos-Dominguez, A.B. (2025). *NormTrace-IHR (IHR 2005+): A systematic tool for assessing the domestic legal implementation of the International Health Regulations* (Version v1.0.2). Zenodo. https://doi.org/10.5281/zenodo.19677846

A `CITATION.cff` file is included in this repository for reference managers that support the Citation File Format.

If you also use the NormTrace-CRPD version, please cite it separately using its own Zenodo DOI.

---

## Contributing

Please read `CONTRIBUTING.md` before opening issues or pull requests. The most useful contributions at this stage are:

- Country normative references for countries not yet in the reference files
- Corrections to analytical criteria or prompt logic, with methodological justification
- Bug reports with a reproducible description

---

## Contact

Adela B. Santos-Dominguez  
Postdoctoral Fellow, Swiss Excellence Government Scholarship (ESKAS)  
Geneva, Switzerland  
[GitHub profile](https://github.com/adelasantosd)
