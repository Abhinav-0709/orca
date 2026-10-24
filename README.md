# ORCA — Ocean Reasoning & Coordination Agent

> **Fetch-A-Thon 3.0 — ASI:One Agent Challenge**  
> *"Don't read the ocean. Ask it."*

ORCA is a multi-agent marine decision-support system that turns fragmented marine data (INCOIS, IMD, maritime GIS boundaries) into explainable, risk-adjusted operational recommendations for coastal operators and fishermen.

---

## 🌊 Core Philosophy

- **Risk-Adjusted Decision-Making:** `Decision Quality = Opportunity × Safety × Accessibility × Data Confidence`. Safety strictly outranks opportunity.
- **Strict Multi-Agent Separation:**
  - **ORCA Commander:** User intent conversion, structured mission creation, ACP orchestration, response synthesis.
  - **Ocean Intelligence Agent:** Marine productivity (INCOIS PFZ, SST, Chlorophyll).
  - **Weather & Marine Forecast Agent:** Marine risk (wave height, swell, wind, IMD warnings, cyclone tracks).
  - **Maritime Safety Agent:** Deterministic boundary, buffer, and restricted zone spatial analysis.
  - **Evidence & Reliability Agent:** Data provenance, freshness evaluation, conflict detection, quantifiable confidence.
  - **Decision & What-If Engine:** Traceable ranking and live recomputation upon constraint modification.
- **Fetch Native:** Discoverable on Agentverse, connected via ACP, with primary interactions in ASI:One.

---

## 🛠️ Repository Structure

```text
orca/
├── agents/            # Specialist domain agents
│   ├── commander/     # Entrypoint & ACP coordinator
│   ├── ocean/         # Marine & fishing opportunity
│   ├── weather/       # Marine weather & risk bulletins
│   ├── maritime/      # Boundaries & spatial safety
│   └── evidence/      # Provenance, freshness, confidence
├── config/            # Pydantic environment configuration
├── data_sources/      # External integrations (INCOIS, IMD)
├── decision/          # Risk-adjusted ranking & what-if engine
├── geospatial/        # Deterministic spatial computations
├── logging/           # Structured logging with trace ID tracking
├── models/            # Pydantic contracts & structured missions
├── orchestration/     # Multi-agent coordination pipelines
└── tests/             # Unit and integration test suites
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd fecth_ai
   ```

2. **Create and activate a virtual environment:**
   ```bash
   uv venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   uv pip install -e ".[dev]"
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   ```

5. **Run test suite:**
   ```bash
   pytest
   ```

---

## 📜 Development Status

Development is managed in phased increments. See [ORCA_Phases.md](docs/ORCA_Phases.md) for the active status and decision log.

- **Phase 0 — Project Foundation:** **COMPLETE** ✅
- **Phase 1 — Marine Data Layer:** **NEXT** ⏳
