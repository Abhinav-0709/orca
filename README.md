# ORCA — Ocean Reasoning & Coordination Agent

> **Fetch-A-Thon 3.0 — ASI:One Agent Challenge**  
> *"Don't read the ocean. Ask it."*

ORCA is an evidence-backed, risk-adjusted marine decision-support system built for the Fetch.ai ecosystem. It transforms fragmented oceanographic data (**INCOIS** Potential Fishing Zones, **Open-Meteo Marine API** high-resolution weather, **Marine Regions GIS** maritime boundaries, and official **IMD** coastal advisories) into explainable recommendations with deterministic non-linear safety dominance and live **What-If simulation recomputation**.

---

## 🌟 Live on Agentverse & ASI:One

ORCA is deployed 24/7 as a hosted agent on the Agentverse cloud and registered on the Almanac fast track:

- **Agent Address:** `agent1q2q4wrsxn4jv8th8amtnkuv5m8qyuqlxq7x2g4wq24yx4r0wtvyhuwk0xzm`
- **Protocol:** Agent Chat Protocol (`ACP v0.3.0`, `chat_protocol_spec`) with `publish_manifest=True`
- **ASI:One Integration:** Search for ORCA or start a session at [asi1.ai](https://asi1.ai)
- **Response Latency:** < 800 ms with live Open-Meteo marine conditions and INCOIS PFZ scoring

---

## 🌊 Core Architectural Pillars

```text
                                  +-----------------------+
                                  |   ASI:One / User      |
                                  +-----------+-----------+
                                              | (ACP Chat Protocol)
                                              v
                                  +-----------------------+
                                  |     ORCA Commander    |
                                  |  (Intent Extractor)   |
                                  +-----------+-----------+
                                              |
                   +--------------------------+--------------------------+
                   |                          |                          |
                   v                          v                          v
       +-----------------------+  +-----------------------+  +-----------------------+
       |      Ocean Agent      |  |     Weather Agent     |  | Maritime Safety Agent |
       |     (INCOIS PFZ)      |  | (Open-Meteo Marine API|  |  (Spatial Boundaries  |
       |  Chlorophyll & SST    |  |  Waves, Swell, Wind)  |  |    & Safety Buffers)  |
       +-----------+-----------+  +-----------+-----------+  +-----------+-----------+
                   |                          |                          |
                   +--------------------------+--------------------------+
                                              |
                                              v
                                  +-----------------------+
                                  |    Evidence Agent     |
                                  |  (Provenance, Decay,  |
                                  |    Conflict, Conf.)   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |    Decision Engine    |
                                  |   (Risk-Adjusted)     |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |    What-If Simulator  |
                                  |  (Dynamic Recomputing|
                                  |   & Interactive Cards)|
                                  +-----------------------+
```

### 1. Risk-Adjusted Decision Formula
Safety strictly outranks raw fishing opportunity. Disqualified zones receive a composite score of 0.0:
$$\text{Composite Score} = (\text{Opportunity} \times w_{\text{opp}} + \text{Accessibility} \times w_{\text{acc}}) \times \text{Safety Multiplier} \times \text{Confidence}$$

- **Safety Gate:** Any zone with wave height > 2.0m, restricted maritime buffer proximity (e.g. IMBL near Palk Bay), or safety score < 50.0 is disqualified from top ranking.
- **Dynamic Objectives:**
  - `high_fishing_potential`: $w_{\text{opp}} = 0.70, w_{\text{acc}} = 0.30$
  - `safest`: $w_{\text{opp}} = 0.35, w_{\text{acc}} = 0.65$ with amplified safety penalty exponent
  - `balanced`: $w_{\text{opp}} = 0.50, w_{\text{acc}} = 0.50$

### 2. Signature What-If Recomputation
When the user asks *"What if I travel 15 km farther?"* or *"What if I prioritize safety?"*, ORCA does **not** generate cosmetic filler. It:
1. Mutates the originating `StructuredMission` contract.
2. Re-runs multi-agent orchestration and spatial checks across new candidate boundaries.
3. Reranks all candidates deterministically.
4. Generates a side-by-side **Comparative Decision Delta** (`Δ Composite`, `Δ Fishing`, `Δ Safety`, `Δ Distance`).
5. Returns actionable follow-up card buttons (`[Expand Range]`, `[Switch to Max Safety]`, `[Early Morning Departure]`).

---

## 🚀 Quick Start

### 1. Clone & Setup Environment
```bash
git clone https://github.com/Abhinav-0709/orca.git
cd orca

# Create virtual environment with uv or python
uv venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install package and test dependencies
uv pip install -e ".[dev]"

# Configure environment variables
cp .env.example .env
```

### 2. Run the Full Test Suite (83 Tests)
```bash
pytest -q
```
*Output: 83 passed in ~20s.*

### 3. Run the Golden Demo Script
```bash
python scripts/demo_orca.py
```
This script executes four full end-to-end scenarios:
- **Scenario 1:** Standard fishing query from Chennai (`Kasimedu Harbour`) within 30 km.
- **Scenario 2:** Non-linear safety dominance & IMBL boundary gate at Rameswaram / Palk Bay.
- **Scenario 3:** What-If distance expansion (+15 km) with side-by-side metric comparison.
- **Scenario 4:** Interactive card generation and live Agentverse hosted status check.

---

## 💬 Interacting with ORCA on ASI:One

Once connected to ORCA on [asi1.ai](https://asi1.ai):

1. **Initial Recommendation:**
   > *"I want to go fishing tomorrow morning from Chennai within 30 km. Find a safe zone."*
2. **What-If Constraint Exploration:**
   > *"What if I travel 15 km farther offshore?"*
   - ORCA recomputes candidates, highlights unlocked deeper PFZs, and shows the exact fuel vs catch trade-off.
3. **Safety Priority Shift:**
   > *"What if I prioritize maximum safety over catch volume?"*
   - ORCA shifts candidate weights toward calmer sheltered inshore waters.

---

## 📁 Repository Structure

```text
orca/
├── agents/            # Specialist domain agents
│   ├── commander/     # Entrypoint & ACP coordinator (with simulate_what_if)
│   ├── ocean/         # Marine & fishing opportunity (INCOIS PFZ / OSF)
│   ├── weather/       # Marine weather (Open-Meteo Marine API, IMD bulletins)
│   ├── maritime/      # Boundaries & spatial safety (Marine Regions GIS)
│   └── evidence/      # Provenance, freshness decay, conflict detection
├── config/            # Pydantic environment configuration (.env validation)
├── data_sources/      # External clients (INCOIS, Open-Meteo, IMD, freshness)
├── decision/          # Risk-adjusted ranking formula & explainer
├── geospatial/        # Deterministic Haversine, polygons, & buffer checks
├── logging/           # Structured logging with request trace ID tracking
├── models/            # Pydantic contracts (StructuredMission, CandidateZone)
├── orchestration/     # IntentExtractor, ACPRouter, and WhatIfEngine
agent/                 # Agentverse Hosted Agent workspace (avctl synced)
scripts/
└── demo_orca.py       # Standalone automated golden demo script
tests/                 # 83 comprehensive unit and integration tests
```

---

## 📜 Development Status

All implementation phases tracked in [docs/ORCA_Phases.md](docs/ORCA_Phases.md) are **COMPLETE**:

- **Phase 0 — Project Foundation:** **COMPLETE** ✅
- **Phase 1 — Marine Data Layer (Open-Meteo + INCOIS):** **COMPLETE** ✅
- **Phase 2 — Geospatial Safety Layer (Boundaries & Buffers):** **COMPLETE** ✅
- **Phase 3 — Specialist Agents (Ocean, Weather, Maritime):** **COMPLETE** ✅
- **Phase 4 — Evidence & Reliability (Decay & Conflicts):** **COMPLETE** ✅
- **Phase 5 — Commander & ACP (Intent Extraction & Dispatch):** **COMPLETE** ✅
- **Phase 6 — Decision Engine (Risk-Adjusted Ranking):** **COMPLETE** ✅
- **Phase 7 — ASI:One Integration (Agentverse Hosted Agent Live):** **COMPLETE** ✅
- **Phase 8 — What-If Engine & Interactive Cards:** **COMPLETE** ✅
- **Phase 9 — Hardening, Secret Review & Golden Demo:** **COMPLETE** ✅

---

## ⚖️ Safety Disclaimer

ORCA is a decision-support prototype built for Fetch-A-Thon 3.0. Always verify official Indian Coast Guard, INCOIS, and IMD coastal bulletins before departing on any voyage.
