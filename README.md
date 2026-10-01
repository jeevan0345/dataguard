# DataGuard 2.0 🛡️
### An Autonomous Multi-Agent System for Automated ETL Pipeline Auditing and Anomaly Detection

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.140-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python)](https://www.python.org/)
[![PostgreSQL 17](https://img.shields.io/badge/Database-PostgreSQL%2017-336791.svg?style=flat&logo=postgresql)](https://www.postgresql.org/)
[![React 18](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite%20%2B%20TS-61DAFB.svg?style=flat&logo=react)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/UI-Tailwind%20CSS-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Isolation%20Forest%20%2B%20SciPy-F7931E.svg?style=flat&logo=scikit-learn)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Deployment-Docker%20Compose-2496ED.svg?style=flat&logo=docker)](https://www.docker.com/)

---

## 1. Executive Summary & Problem Statement

In modern cloud data architectures and enterprise analytics platforms, data pipelines continuously extract, transform, and load (ETL) petabytes of mission-critical information. However, traditional monitoring systems rely on static threshold alerts or silent failure logs. When schema drift, subtle null propagation, duplicate transaction bursts, or multivariate statistical corruption occur, they propagate undetected downstream into broken machine learning models, poisoned data warehouses, and incorrect executive decision-making.

**DataGuard 2.0** solves this paradigm by introducing an **Autonomous Multi-Agent AI System** that audits data streams in real time. Rather than relying on rigid rules or hallucinating generative AI on raw numbers, DataGuard combines **pure mathematical and statistical machine learning** with a **cooperative swarm of specialized agents** to inspect data quality, detect distribution drift, synthesize root causes, propose policy-checked recovery actions, certify post-remediation outcomes, generate audit reports, and converse through an interactive AI Copilot.

---

## 2. Core System Architecture

```
                                  [ Data Sources ]
                         (Olist CSV / JSON / Excel Streams)
                                         │
                                         ▼
                             [ Pandas-Free Ingestion ]
                        (Python csv/json + OpenPyXL Engine)
                                         │
                                         ▼
                            [ Schema Inference Engine ]
                        (String, Int, Float, Datetime, Bool)
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
      [ 1. Inspector Agent ]                           [ 2. Drift Agent ]
  • Data Quality (Nulls, Dups)                     • Two-Sample KS-Test
  • Schema Drift (Add/Remove/Type)                 • Distribution Shift
  • ML Engine (IQR, Z-Score, IsolationForest)      • Categorical Proportions
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                             [ 3. Evidence Engine ]
                     Converts findings into structured evidence
                             items (E1, E2, E3, ...)
                                         │
                                         ▼
                            [ 4. Root Cause Agent ]
                     Cross-finding correlation & diagnostic
                       hypotheses with confidence scores
                                         │
                                         ▼
                         [ 5. Recommendation Agent ]
                    Prioritized engineering advice (P0 - P3)
                             & synthesized SQL fixes
                                         │
                                         ▼
                           [ 6. Recovery & Policy Agent ]
                     Controlled self-healing candidate actions
                     (Policy bounds, risk checks, approval gate)
                                         │
                                         ▼
                             [ Verification Engine ]
                     Re-profiles remediated data & issues
                     certified PASS / PARTIAL / FAIL verdict
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
      [ 7. Reporter Agent ]                           [ 8. AI Copilot Agent ]
  • ReportLab Multi-Page PDF                      • Interactive Conversational UI
  • OpenPyXL Excel Audit Workbook                 • Grounded in Evidence (No Hallucination)
  • Tamper-Evident Sign-Off                       • Explains Root Causes & Fixes
```

---

## 3. Technology Stack & Key Design Principles

| Layer | Technology | Architectural Rationale |
| :--- | :--- | :--- |
| **Backend API** | FastAPI + Python 3.12 | High-performance asynchronous REST endpoints with Pydantic v2 serialization and automatic OpenAPI documentation. |
| **Data Handling** | Standard Python `csv` / `json` + `openpyxl` | **Strictly Pandas-Free**: Avoids high memory footprints, non-deterministic object coercions, and hidden latency spikes. |
| **Machine Learning** | NumPy, SciPy, Scikit-learn | Fast vectorized computations, Two-sample Kolmogorov-Smirnov distribution tests, and unsupervised multivariate **Isolation Forest**. |
| **Database & ORM** | PostgreSQL 17 + SQLAlchemy 2.0 + Alembic | Relational integrity with UUID primary keys, timestamped audit runs, finding relationships, and migration history. |
| **Authentication & RBAC**| Native Bcrypt + Python-Jose (JWT) | Role-Based Access Control enforcing permissions across `ADMIN`, `DATA_ENGINEER`, and `VIEWER`. |
| **Background Tasks** | Celery + Redis | Asynchronous background dataset inspections and recurring pipeline health audits. |
| **Reporting** | ReportLab + OpenPyXL | Production-grade executive PDF reports with summary tables and multi-tab Excel audit workbooks. |
| **Frontend UI** | React 18 + TypeScript + Vite + Tailwind CSS + Recharts | Polished enterprise dark-mode dashboard, live agent visualizer, fault simulator, and copilot chat. |
| **Containerization** | Docker + Docker Compose | One-command fullstack container orchestration. |

---

## 4. The 7 Autonomous Swarm Agents & Core Engines

The platform coordinates a cooperative swarm of 7 specialized agents orchestrated by the `MultiAgentOrchestrator`:

1. **Inspector Agent**: Unifies data quality checks (missing/empty values, duplicates), schema drift (added, removed, or mutated column types), and statistical/ML anomaly detection.
2. **Drift Agent**: Performs two-sample Kolmogorov-Smirnov (`scipy.stats.ks_2samp`) tests comparing current batch distributions against historical baseline references.
3. **Root Cause Agent**: Correlates multi-source symptoms (e.g. dropped columns + missing values = upstream extraction contract change) into ranked diagnostic hypotheses with confidence scores.
4. **Recommendation Agent**: Formulates prioritized technical action plans (P0 to P3) with production-ready SQL remediation scripts.
5. **Recovery Agent**: Formulates policy-guarded candidate actions (row deduplication, null quarantine, schema restoration) subject to strict safety rules, generates remediated CSVs, and issues SHA-256 integrity hashes.
6. **Reporter Agent**: Generates executive PDF audit reports and Excel workbooks with cryptographic SHA-256 and HMAC-SHA256 signatures for tamper-evident compliance sign-off.
7. **AI Copilot Agent**: Conversational data engineering assistant with dual-mode architecture: live Google Gemini (gemini-2.5-flash) reasoning when configured, or offline deterministic evidence-grounded reasoning.

Supporting Engines:
- **Evidence Engine**: Converts multi-agent findings into canonical structured evidence items with SHA-256 and HMAC-SHA256 digital seals.
- **Verification Engine**: Re-audits remediated datasets post-recovery to certify anomaly eradication with a signed PASS/FAIL verdict.

---

## 5. Empirical Performance Benchmarks (Pandas-Free)

Benchmarked on Python 3.12 (standard library `csv` + NumPy/SciPy + Scikit-Learn) on real-world Brazilian Olist datasets without Pandas:

| Dataset | Record Count | Ingestion Throughput | Profiling Speed | Swarm Audit Throughput | Total Pipeline Time | Peak Heap Memory |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `olist_customers_dataset.csv` | 20,000 | 22,401 rows/s | 36,478 rows/s | 6,113 rows/s | 4.16 s | 45.55 MB |
| `olist_customers_dataset.csv` | 99,441 | 124,152 rows/s | 35,622 rows/s | 6,231 rows/s | 16.76 s | 45.40 MB |
| `olist_order_items_dataset.csv` | 112,650 | 91,925 rows/s | 23,368 rows/s | 5,028 rows/s | 23.63 s | 70.11 MB |

*Reproducible via `python scripts/benchmark.py`.*

---

## 6. Getting Started & Installation

### Prerequisites
- Python 3.12+
- PostgreSQL 17 (or use Docker Compose)
- Node.js 20+ & npm

### Method A: Quick Local Launch

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/DataGuard.git
   cd DataGuard
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Configure Environment Variables (`backend/.env`)**:
   ```env
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/dataguard
   SECRET_KEY=dataguard_secret_key_2026
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   REDIS_URL=redis://localhost:6379/0
   ```

4. **Initialize Database & Seed Demo Accounts**:
   ```bash
   python -c "from app.database.init_db import create_tables; from app.database.session import SessionLocal; from app.auth.router import seed_demo_users; create_tables(); db = SessionLocal(); seed_demo_users(db); db.close()"
   ```

5. **Start Backend Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *Swagger Docs will be live at `http://localhost:8000/docs`*

6. **Frontend Setup**:
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```
   *Frontend UI will be live at `http://localhost:3000`*

---

### Method B: One-Command Docker Compose Launch

```bash
docker-compose up --build
```
*Spins up PostgreSQL 17, Redis, FastAPI Backend, Celery Worker, and React Frontend automatically.*

---

## 7. Demo Accounts & RBAC Roles

The system is pre-seeded with 3 demo accounts featuring 1-click login on the UI:

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@dataguard.ai` | `admin123` | Full administrative control, user management, and recovery approval. |
| **Data Engineer** | `engineer@dataguard.ai` | `engineer123` | Pipeline auditing, fault simulation, recovery execution, and copilot interaction. |
| **Viewer** | `viewer@dataguard.ai` | `viewer123` | Read-only stakeholder access to dashboards, reports, and audit logs. |

---

## 8. Interactive Fault Simulator Scenarios

DataGuard features an interactive pipeline simulator designed for live project demonstrations and examiner evaluations:

- **Clean Baseline**: Normal pipeline execution validating zero false-positives.
- **Missing Values Injection**: Injects 20% nulls in critical key columns.
- **Duplicate Records Surge**: Injects duplicate transaction records simulating broker replay failure.
- **Breaking Schema Drift**: Drops an expected column from the extraction stream.
- **ML Outliers**: Injects extreme numeric spikes detected by Isolation Forest.
- **Composite Disaster**: Simultaneous multi-fault corruption testing full swarm coordination.

---

## 9. Academic Viva & Faculty Defense Positioning

- **Q: Why a Multi-Agent Swarm instead of a single script?**
  *A: Separation of concerns. Specialized agents operate independently with clear contracts, allowing inspection, diagnostic reasoning, policy-controlled self-healing, and compliance reporting to scale modularly.*

- **Q: Why was Pandas intentionally excluded?**
  *A: Pandas introduces significant memory bloat, non-deterministic type coercion, and runtime overhead. Pure Python standard libraries combined with vectorized NumPy and SciPy arrays deliver superior throughput and deterministic guarantees.*

- **Q: Why combine Statistical/ML Methods with Generative Reasoning?**
  *A: Numerical anomaly detection requires mathematical certainty (Z-score, IQR, Isolation Forest, KS-tests). Generative models hallucinate numbers when asked to detect statistical anomalies directly. DataGuard computes exact metrics first, builds structured evidence, and uses agentic reasoning strictly over verified facts.*

- **Q: How is Self-Healing / Recovery made safe in production?**
  *A: Zero uncontrolled production mutations. Recovery proposals undergo safety policy checks (e.g. maximum drop thresholds, protected primary keys), require human operator sign-off for high-risk changes, and run sandbox verification dry-runs before issuing a certified PASS verdict.*

---

## 10. License

Developed as an undergraduate final-year engineering project. Distributed under the MIT License.
