# VisualSQL &bull; Enterprise Query Intelligence & Performance Optimization

**VisualSQL** is an advanced, production-grade SQL optimization explorer, visual execution plan analyzer, and benchmarking platform built with **Flask**, **SQLite (WAL mode)**, **MySQL 8.0**, and **Chart.js**.

---

## Key Features & Capabilities

### 1. Executive Telemetry & Analytics Dashboard
- **KPI Metrics**: Real-time experiment counts, unique SQL workload tracking, mean latency, and peak optimization gain.
- **Interactive Visualizations**:
  - Configuration latency comparisons (baseline vs. rewrite vs. indexed).
  - Relative speedup percentage distributions.
  - **Algorithmic Complexity Curve**: Interactive chart illustrating theoretical and measured differences between sequential full table scans ($O(N)$) and B-Tree index seeks ($O(\log N)$) across 1k &rarr; 100k records.

### 2. SQL Studio & Interactive Workbench
- **Live Schema Explorer**: Expandable table and column trees with primary key tags, data types, and index metadata.
- **Query Template Library**: Pre-built SQL workloads demonstrating filter selectivity, composite predicates, range queries, and aggregations.
- **AST Index Candidate Extraction**: Automatically inspects `WHERE`, `ORDER BY`, and `GROUP BY` clauses to suggest high-impact secondary indexes.
- **SQL Beautifier**: One-click formatting with uppercase keyword standardization.
- **Execution Telemetry**: Server execution timing, row count tracking, and automatic `LIMIT` protection.

### 3. Visual Execution Plan Analyzer
- **Multi-Engine Planner**: Supports both SQLite (`EXPLAIN QUERY PLAN`) and MySQL (`EXPLAIN`, `EXPLAIN FORMAT=JSON`, `EXPLAIN ANALYZE`).
- **Visual Execution Pipeline**: Flow graph mapping physical database operators:
  $$\text{Table Storage} \longrightarrow \text{Access Operator (Scan vs. Seek)} \longrightarrow \text{Predicate Filter} \longrightarrow \text{Projection Output}$$
- **Query Health Score (0–100)**: Instant rating with actionable DBA diagnostics for eliminating sequential scans.

### 4. Benchmark Lab & Multi-Variant Comparison
- **Automated Configuration Matrix**:
  - `baseline`: Unindexed query on raw storage.
  - `rewrite`: Projection optimization (explicit column projection replacing wildcard `SELECT *`).
  - `indexed`: Temporary B-Tree index on candidate columns.
  - `indexed+rewrite`: Index seek combined with explicit column projection.
- **Empirical Metrics**: Arithmetic mean, median, min, max, 95th percentile ($P95$), and standard deviation over configurable repetition passes.
- **Safe Transaction Cleanup**: Temporary benchmark indexes are automatically created and safely dropped in `finally` blocks, ensuring zero residual storage overhead.

### 5. DBA Recommendation & Audit Engine
- Evaluates scan patterns, selectivity, and column projection gains.
- Explains index write-amplification trade-offs (storage growth and $O(\log N)$ overhead on `INSERT`/`UPDATE`/`DELETE`).
- Recommends covering indexes when all queried attributes can be satisfied directly from the B-Tree leaf pages.

### 6. Reports & Data Factory
- **Executive PDF Export**: Formatted executive reports generated via ReportLab with tables, SQL code blocks, and recommendations.
- **CSV Data Export**: One-click download of all historical benchmark telemetry.
- **Data Factory**: Generates 1k, 10k, 50k, and 100k standard synthetic datasets or imports custom CSV files.

---

## Architecture & Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.10+, Flask, Werkzeug, Pandas, Sqlparse |
| **Database Engines** | SQLite 3 (WAL journal mode + foreign keys enabled) & MySQL 8.0+ |
| **Reporting** | ReportLab (Vector PDF generator) & Pandas CSV Engine |
| **Frontend** | HTML5, CSS3 Variables (Light & Dark themes), Vanilla ES6 JavaScript, Chart.js 4.4 |
| **Test Suite** | Pytest 8+ (15 end-to-end integration and unit tests) |

---

## Quickstart Guide

### 1. Requirements
Ensure Python 3.10+ is installed:
```powershell
python --version
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Launch Application
The application will automatically initialize the database schema and seed the baseline sample dataset (`employees_1000`):
```powershell
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your web browser.

---

## Running the Test Suite

Execute the automated test suite with pytest:
```powershell
pytest -v
```
All 15 tests cover SQL validation, AST index extraction, multi-engine explain planning, benchmarking, dataset lifecycle, PDF generation, and REST API endpoints.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | `GET` | Database backend status, table counts, and record metrics |
| `/api/schema` | `GET` | Schema introspection: tables, columns, data types, indexes |
| `/api/validate` | `POST` | Validates SQL, formats keywords, and extracts candidate indexes |
| `/api/query` | `POST` | Executes read-only query and returns timing and result grid |
| `/api/explain` | `POST` | Generates visual execution plan, health score, and operator breakdown |
| `/api/benchmark` | `POST` | Executes multi-pass benchmark across baseline, rewrite, and indexed variants |
| `/api/summary` | `GET` | Aggregated KPI statistics for the dashboard overview |
| `/api/datasets` | `GET` | Lists all active datasets and row counts |
| `/api/datasets/setup` | `POST` | Synthesizes standard benchmark datasets (1k, 10k, 50k, 100k) |
| `/api/datasets/generate` | `POST` | Generates custom row count dataset |
| `/api/history` | `GET` | Audit trail of past benchmark experiments |
| `/report/pdf/<id>` | `GET` | Downloads executive PDF performance report |
| `/report/csv` | `GET` | Downloads raw benchmark measurements in CSV format |
