# AI/NLP Engine to Detect Serious Injury & Fatality (SIF) Precursors
### Oil India Limited (OIL) • Problem Statement ID: 26165 (Smart India Hackathon)

An enterprise-grade, explainable AI/NLP HSE decision-support platform that automatically screens free-text **Unsafe Act / Unsafe Condition (UA/UC)** and **Near-Miss** safety reports, classifies **SIF-potential** vs routine observations, maps events to **IOGP Life-Saving Rules**, extracts precursor dimensions (activity, site, failed barriers, trigger evidence), and calculates **SIF-Precursor Density** across oilfields with an interactive Command Center dashboard and **Human-in-the-Loop (HITL)** expert review queue.

---

## Key Features

1. **Multi-Task AI/NLP Engine**:
   - **Calibrated SIF Classifier**: Evaluates high-energy potential (high-pressure gas release, toxic $H_2S$, energized circuits, suspended loads, working at height) with probabilistic confidence scores ($0.0 - 1.0$).
   - **IOGP Life-Saving Rules Classifier**: Automatically maps observations to 9 standard IOGP safety categories (*Energy Isolation/LOTO, Working at Height, Confined Space, Line of Fire, Hot Work, Mechanical Lifting, Toxic Gas/$H_2S$, Driving Safety, System Bypass*) + General UA/UC.
   - **Precursor & Barrier Extractor**: Mines root activity, specific rig/station section, and the failed safety barrier.
   - **Explainable AI (XAI)**: Highlights the specific textual triggers and clauses that determined the risk classification.

2. **HSE Analytics & SIF Precursor Density**:
   - **SIF Precursor Density**:
     $$\text{SIF Density (\%)} = \left(\frac{\text{SIF-Potential Reports}}{\text{Total Reports}}\right) \times 100$$
   - Top high-risk OIL site & operational activity rankings.
   - IOGP Rule volume breakdown & Barrier Failure Pareto analysis ($80/20$ vital few failed controls).
   - Monthly temporal risk trends.

3. **Human-in-the-Loop (HITL) Review Queue**:
   - Automatically routes uncertain predictions (confidence $< 75\%$) to safety specialists.
   - Allows safety officers to confirm or reclassify SIF potential and rules with audit logs.

4. **Dual-Mode Database Architecture**:
   - **Embedded Persistent Document Store**: Runs out of the box with zero external configuration.
   - **MongoDB / Atlas Ready**: Connects automatically if `MONGODB_URI` is provided in `.env`.

5. **Interactive Executive HSE Dashboard**:
   - Real-time AI text analyzer sandbox with sample scenarios.
   - Searchable, filterable safety reports table with drill-down modal inspection.
   - Drag-and-drop batch CSV/Excel ingestion.
   - One-click CSV export.

---

## System Architecture

```
                                  +---------------------------------------+
                                  |   OIL Safety Observations (Free Text)  |
                                  |   - Unsafe Acts / Unsafe Conditions   |
                                  |   - Near-Misses & Incidents           |
                                  +---------------------------------------+
                                                     |
                                                     v
                                  +---------------------------------------+
                                  |      NLP Preprocessing Pipeline       |
                                  |  - HSE Abbreviation Expansion (LOTO)  |
                                  |  - Negation Preservation & Tokenizer  |
                                  +---------------------------------------+
                                                     |
                    +--------------------------------+--------------------------------+
                    |                                |                                |
                    v                                v                                v
       +-------------------------+      +-------------------------+      +-------------------------+
       |   SIF Binary Classifier |      |  IOGP 9 Life-Saving     |      |   Precursor & Barrier   |
       |  - P(SIF) Probability   |      |  Rules Classifier       |      |   Failure Extractor     |
       |  - Confidence Scoring   |      |  - 9 IOGP Categories    |      |  - Activity & Location  |
       |  - Uncertainty Routing  |      |  - Multi-Rule Tagging   |      |  - Evidence Snippets    |
       +-------------------------+      +-------------------------+      +-------------------------+
                    |                                |                                |
                    +--------------------------------+--------------------------------+
                                                     |
                                                     v
                                  +---------------------------------------+
                                  |       Dual-Mode Database Layer        |
                                  |  - Embedded Persistent JSON Storage   |
                                  |  - MongoDB Atlas / PyMongo Support    |
                                  +---------------------------------------+
                                                     |
                                                     v
                                  +---------------------------------------+
                                  |          FastAPI REST API             |
                                  |  /api/reports, /api/analyze,          |
                                  |  /api/dashboard, /api/reviews         |
                                  +---------------------------------------+
                                                     |
                                                     v
                                  +---------------------------------------+
                                  |      Interactive HSE Web Dashboard    |
                                  |  - Executive KPI Cards & SIF Density  |
                                  |  - High-Risk Site & Activity Ranking  |
                                  |  - Real-Time AI Analyzer Sandbox      |
                                  |  - Human-in-the-Loop Review Queue     |
                                  +---------------------------------------+
```

---

## Directory Structure

```
SIH Project/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI entrypoint & static mount
│   │   ├── config.py                   # App configuration & thresholds
│   │   ├── database.py                 # Dual-mode persistent DB engine
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py              # Pydantic models & validation
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── reports.py              # Report CRUD, filtering, CSV upload/export
│   │   │   ├── analysis.py             # Real-time & batch text inference
│   │   │   ├── dashboard.py            # KPI metrics, rankings, distributions, trends
│   │   │   └── reviews.py              # Human-in-the-loop review queue & audit logs
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── nlp_preprocessor.py     # HSE jargon expansion & text normalizer
│   │       ├── sif_classifier.py       # Calibrated SIF-potential classifier
│   │       ├── rule_classifier.py      # IOGP Life-Saving Rules classifier
│   │       ├── precursor_extractor.py  # Activity, location & barrier extractor
│   │       ├── data_generator.py       # Synthetic OIL safety dataset generator
│   │       └── analytics.py            # SIF density & ranking computation
│   ├── tests/
│   │   ├── test_nlp.py                 # NLP & ML unit tests
│   │   └── test_api.py                 # FastAPI integration tests
│   └── requirements.txt
├── frontend/
│   ├── index.html                      # Single-page HSE web application
│   ├── css/
│   │   └── styles.css                  # Custom styling, badges & animations
│   └── js/
│       ├── app.js                      # Application state & tab router
│       ├── dashboard.js                # Chart.js visualizations & KPI renderers
│       ├── analyzer.js                 # Live AI sandbox & sample loader
│       ├── reports.js                  # Search, filters, modal inspector & upload
│       └── reviews.js                  # Review queue confirmation workflow
├── data/
│   ├── rules_taxonomy.json             # IOGP Life-Saving Rules definitions
│   └── oil_safety_reports_seed.csv     # Exportable seed dataset
├── run.sh                              # One-click startup script (Mac/Linux)
├── run.py                              # Cross-platform startup script
├── .env.example
└── README.md
```

---

## Quickstart Guide

### 1. One-Click Launch (Recommended)
```bash
./run.sh
```
Or with Python:
```bash
python3 run.py
```

### 2. Manual Setup
```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Start application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
```

### 3. Open in Browser
- **HSE Command Center**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Running Automated Tests

Run the full automated test suite to verify NLP models and API endpoints:
```bash
export PYTHONPATH=backend
pytest backend/tests -v
```

---

## Hackathon Demo Walkthrough

1. **Executive Dashboard**:
   - View high-level KPIs: Total Reports, SIF-Potential Reports, Overall SIF Precursor Density %, Pending Reviews, and High-Risk Sites.
   - Inspect Top High-Risk Sites bar chart (e.g. Moran GGS, Naharkatiya Rig D-14, Digboi Facility).
   - Review the IOGP Life-Saving Rules distribution donut chart and Barrier Failure Pareto analysis.
2. **Live AI Analyzer**:
   - Click "Sample: LOTO", "Sample: Height", or "Sample: Toxic Gas".
   - Click **Run AI Analysis** to observe real-time classification, confidence score, mapped rule, and extracted barrier failure with highlighted XAI triggers.
   - Click **Save to Database** to persist the report into live records.
3. **Safety Reports Explorer**:
   - Filter by Site, Life-Saving Rule, or SIF status.
   - Click **Inspect** on any report to open the detailed modal breakdown.
4. **Human-in-the-Loop Review Queue**:
   - Inspect borderline cases routed for human validation.
   - Confirm or reclassify the SIF status, add reviewer notes, and submit to update the audit log and dashboard metrics in real time.
5. **Batch CSV Upload**:
   - Drag and drop a safety report CSV file to test instant high-volume batch processing.
