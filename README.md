# RR EDGE — Finding the Competitive Edge

> **Advanced Pressure Intelligence, Player Evaluation & Grounded Tactical Simulation**  
> Engineered for Rajasthan Royals Franchise Leadership, High-Performance Staff, and Scouts.  
> **SupeRR Selector Competition Season 2**

---

## 1. Overview & Core Capabilities

**RR EDGE** transforms 194,014 ball-by-ball delivery records from the Indian Premier League (IPL) and Senior Men's T20 Internationals (2022–2026) into an explainable, decision-grade recruitment and match-strategy system.

Key Capabilities:
* **Cricket-First Pressure Engine:** Asymmetric match-leverage framework modeling 2nd-innings deterministic chase mathematics against 1st-innings par deficits.
* **Context-Adjusted Efficiency (RAE & RCAE):** Batter Run Acceleration Efficiency and Bowler Run Concession Abatement Efficiency benchmarked against situational par across format, phase, and match state.
* **Empirical Bayes Shrinkage ($M=45$):** Prior-regularized rates that protect auction purse capital from small-sample noise while preserving breakout upside.
* **Match-Cluster Bootstrap Uncertainty:** 10,000 cluster-resample iterations providing pairwise confidence intervals and honest non-separability reporting.
* **Zero-Leakage ML Delivery Models:** Pre-delivery contextual expected run and wicket models validated chronologically on the unseen 2026 holdout partition (144 matches, 31,165 batter deliveries).
* **Observable Behavioral Dynamics:** Non-psychological reaction metrics measuring post-dot acceleration and post-boundary next-legal-ball bounce-back.
* **Scenario Lab:** 16 standardized match crucibles evaluating batters and bowlers across distinct completed match episodes.
* **Interactive 2D Cricket Simulator:** Responsive SVG ground physics supporting 80 audited historical death-sequence replays and empirical What-if simulations with live strike rotation.

---

## 2. Technology Stack

* **Backend & Analytics:** Python 3.13, FastAPI, Uvicorn, Pandas, NumPy, Scipy, Scikit-learn, XGBoost, Joblib, PyArrow
* **Frontend & Visualization:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts, Responsive SVG Physics
* **Testing & Quality Assurance:** Pytest, AnyIO, Puppeteer

---

## 3. Directory Structure

```
rr-edge/
├── data/
│   ├── raw/                             # Raw match deliveries & rosters
│   └── processed/                       # Curated datasets, ML holdouts, final selections
├── docs/
│   └── RR_EDGE_FINAL_SUBMISSION.md      # Authoritative Final Competition Submission
├── frontend/                            # React 18 + TypeScript + Vite web interface
│   ├── src/                             # Simulator, Scenario Lab, Gallery & Intelligence components
│   └── dist/                            # Production pre-built assets
├── notebooks/                           # Exploratory data & pressure notebooks
├── reports/                             # Technical research audits & architectural figures
│   └── figures/                         # Core platform diagrams & architecture flowcharts
├── scripts/                             # Reproductibility audit scripts
├── src/                                 # Production backend architecture
│   ├── api/                             # FastAPI application & data services
│   ├── cricket/                         # Semantics, accounting & pressure calculation
│   └── models/                          # Bayesian shrinkage, ML pipelines, simulator engine
├── tests/                               # 178 automated unit & integration tests
├── run_dashboard.py                     # One-click platform launch script
└── requirements.txt                     # Python dependencies
```

---

## 4. Installation & Setup

### Prerequisites
* Python 3.10+ (tested on Python 3.13)
* Node.js 18+ and npm (for frontend development)

### Install Dependencies
```bash
# In project root
pip install -r requirements.txt

# In frontend directory
cd frontend
npm install
cd ..
```

---

## 5. Running the Application

### Option A: Unified Production Platform (Recommended)
Starts the FastAPI backend and serves the compiled, production-ready React interface with automatic browser launch:

```bash
python run_dashboard.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### Option B: Development Mode
**Terminal 1 — Backend:**
```bash
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Frontend (Vite HMR):**
```bash
cd frontend
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** (automatically proxies API requests to port 8000).

---

## 6. Running the Automated Test Suite

All 178 unit and integration tests across data loading, pressure calculation, shrinkage, ML, behavioral dynamics, Scenario Lab, and the 2D Simulator can be verified via:

```bash
pytest tests/
```
*Expected Result:* `178 passed in ~115s`

---

## 7. Final Submission Documentation

The definitive, numerically reconciled competition deliverable is located at:
* **[docs/RR_EDGE_FINAL_SUBMISSION.md](file:///c:/HACKATHONS/77.%20RR%20SELECTOR%20-%20RAJASTHAN%20ROYALS/APP/rr-edge/docs/RR_EDGE_FINAL_SUBMISSION.md)**

It provides the complete consolidated methodology report, canonical Top 10 Batter and Bowler profiles, five-minute judge demonstration script, and final audit sign-off checklist.
