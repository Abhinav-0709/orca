# ORCA --- Development Phases & Living Project State

**Project:** ORCA --- Ocean Reasoning & Coordination Agent\
**Hackathon:** Fetch-A-Thon 3.0\
**Purpose:** Single living implementation-state document

> **Rule:** Do not create a separate phase-status file for every change.
> Update this document whenever the implementation meaningfully changes.

------------------------------------------------------------------------

# How To Use This File

This is the project's **living development log**.

At the end of every meaningful implementation step:

1.  Update the current phase.
2.  Record what was implemented.
3.  Record files changed.
4.  Record tests run.
5.  Record decisions.
6.  Record blockers.
7.  Record changes from the previous plan.
8.  Set the next phase.

Never rewrite history to make the project look cleaner. Preserve
important decisions and changes.

------------------------------------------------------------------------

# Project State

**Current Phase:** Phase 6 --- Decision Engine\
**Status:** IN PROGRESS

## Overall Progress

``` text
Phase 0  Foundation              [X] 
Phase 1  Marine Data Layer       [X]
Phase 2  Geospatial Safety       [X]
Phase 3  Specialist Agents       [X]
Phase 4  Evidence & Reliability  [X]
Phase 5  Commander & ACP         [X]
Phase 6  Decision Engine         [ ]
Phase 7  ASI:One Integration     [ ]
Phase 8  What-If / Cards         [ ]
Phase 9  Hardening & Demo        [ ]
```

------------------------------------------------------------------------

# Phase 0 --- Project Foundation

**Status:** COMPLETE

## Goal

Create a clean, reproducible backend project foundation with configuration, structured logging, core data models, and an automated test suite.

## Planned

- repository structure
- Python environment (uv / pyproject.toml)
- configuration with Pydantic Settings
- `.env.example`
- structured logging with trace/request_id support
- basic models (Mission, Contracts, CandidateZone, EvidenceItem, DecisionOutput)
- test framework (pytest)
- initial README
- documentation structure

## Completion

Phase 0 is complete when:

- project runs locally,
- tests execute,
- configuration works,
- secrets are externalized,
- repository structure is stable enough for Phase 1.

## Implemented

- Established full modular project layout across agents (`commander`, `ocean`, `weather`, `maritime`, `evidence`), `orchestration`, `data_sources` (`incois`, `imd`), `geospatial`, `decision`, `models`, `config`, and `logging`.
- Created `pyproject.toml` and `.gitignore`. Virtual environment initialized with `uv`.
- Built Pydantic Settings configuration (`orca/config/settings.py`) with support for environment variables and `.env`.
- Created complete `.env.example` for all operational sources (INCOIS, IMD), Agentverse/ACP, and LLM providers.
- Built context-aware structured logger (`orca/logging/logger.py`) with `ContextVar`-based `request_id` propagation for end-to-end multi-agent tracing.
- Implemented core domain models in `orca/models/`:
  - `Coordinate`, `TimeWindow`, and `StructuredMission` with strict validation.
  - `AgentRequest`, `AgentResponse`, `AgentStatus`, `AgentError`, and `AgentWarning` contracts.
  - `EvidenceItem` and `DataFreshness` tracking.
  - `CandidateZone`, `SafetyEvaluation`, and `DecisionOutput` models.
- Built automated test suite (`tests/test_config.py`, `tests/test_logger.py`, `tests/test_models.py`) with 14 passing unit tests covering validation, bounds, and serialization.
- Authored initial project `README.md`.

## Files Changed

- `pyproject.toml`
- `.gitignore`
- `.env.example`
- `README.md`
- `orca/__init__.py`
- `orca/config/__init__.py`
- `orca/config/settings.py`
- `orca/logging/__init__.py`
- `orca/logging/logger.py`
- `orca/models/__init__.py`
- `orca/models/mission.py`
- `orca/models/evidence.py`
- `orca/models/agent_contract.py`
- `orca/models/candidate.py`
- `orca/agents/__init__.py`
- `orca/agents/commander/__init__.py`
- `orca/agents/ocean/__init__.py`
- `orca/agents/weather/__init__.py`
- `orca/agents/maritime/__init__.py`
- `orca/agents/evidence/__init__.py`
- `orca/orchestration/__init__.py`
- `orca/data_sources/__init__.py`
- `orca/data_sources/incois/__init__.py`
- `orca/data_sources/imd/__init__.py`
- `orca/geospatial/__init__.py`
- `orca/decision/__init__.py`
- `tests/__init__.py`
- `tests/test_config.py`
- `tests/test_logger.py`
- `tests/test_models.py`
- `docs/ORCA_Phases.md`

## Tests

- 14/14 unit tests passed via `pytest`:
  - `tests/test_config.py`: 2 tests (defaults, environment overrides)
  - `tests/test_logger.py`: 4 tests (context var propagation, text formatting, JSON output, logger factory)
  - `tests/test_models.py`: 8 tests (coordinate bounds, time window validation, structured mission validation, distance bounds, success/failure agent contracts, candidate zone & decision outputs)

## Decisions

- **Pydantic v2 & Pydantic-Settings**: Selected for robust data validation, type safety, and automatic `.env` loading.
- **Context-Variable Trace IDs**: Standardized `request_id_ctx` in `orca/logging/logger.py` so every agent call within an asynchronous workflow automatically logs its trace identifier without passing it to every log call manually.
- **Shapely Included in Foundation**: Added `shapely` from Phase 0 to ensure deterministic geometric handling is available across all environments.

## Problems / Blockers

- None encountered. All dependencies installed and tests passed.

## Changes From Plan

- None.

## Current System State

Foundation is clean, reproducible, fully typed, tested, and ready for operational data source integrations.

## Next Phase

Phase 1 --- Marine Data Layer

------------------------------------------------------------------------

# Phase 1 --- Marine Data Layer

**Status:** COMPLETE

## Goal

Build reliable access to operational marine and weather data (INCOIS for ocean intelligence, Open-Meteo Marine API as primary weather feed, and optional IMD advisory bulletins) with normalized internal data models, timestamps, freshness evaluation, schema validation, and robust error recovery.

## Planned

- INCOIS integration (PFZ advisories & Ocean State Forecasts)
- Open-Meteo Marine API integration (waves, swell, wind, current, SST)
- Open-Meteo Data Validator & Data Adapter
- IMD integration (optional fishermen warnings & cyclone tracking)
- normalized source models
- timestamps & validity windows
- source metadata & provenance
- error handling & fallback resilience
- data validation

## Completion

ORCA can retrieve real marine/weather evidence and normalize it into internal models.

## Implemented

- Built `orca/data_sources/freshness.py`:
  - `evaluate_freshness`: Analyzes observation and validity expiration timestamps to classify into `LIVE`, `RECENT`, `STALE`, and `EXPIRED` with corresponding confidence multipliers.
- Built `orca/data_sources/models.py`:
  - `PFZAdvisory`: Normalized model for INCOIS Potential Fishing Zones (depth, distance, direction, landing center, SST, chlorophyll, potential score).
  - `OceanStateForecast`: Normalized model for wave height, swell height/period/direction, wind speed/direction, surface current, water temperature.
  - `MarineWarning`: Normalized model for IMD Fishermen Warnings, Coastal Bulletins, and Cyclone Bulletins with colour-coded severity (`GREEN`, `YELLOW`, `ORANGE`, `RED`).
  - `MarineDataPackage`: Aggregated bundle for candidate regions.
- Built `orca/data_sources/open_meteo/`:
  - `OpenMeteoValidator`: Validates schema, coordinate match, and physical ranges (waves, swell, wind, current, SST).
  - `OpenMeteoAdapter`: Matches requested target time to closest hourly forecast and converts into normalized `OceanStateForecast` with `OPEN_METEO_MARINE` evidence provenance.
  - `OpenMeteoClient`: Async client for Open-Meteo Marine API (no API key required) with validation and operational fallback.
- Built `orca/data_sources/incois/client.py`:
  - `IncoisClient`: Async client for INCOIS PFZ and OSF endpoints with timeout handling, response parsing, and operational fallback capability for Indian coastal waters (Chennai/Tamil Nadu coast).
- Built `orca/data_sources/imd/client.py`:
  - `ImdClient`: Async client for IMD Fishermen and Cyclone warnings with severity parsing, timeout recovery, and verified operational fallbacks.
- Built test suites:
  - `tests/test_freshness.py`: 5 tests covering live data, recent decay, stale penalties, expiration checks, and unknown timestamps.
  - `tests/test_open_meteo.py`: 5 tests covering payload validation, missing schema errors, physical range warnings, hourly selection, and client fallback.
  - `tests/test_incois.py`: 4 tests covering PFZ retrieval, radius filtering, OSF forecasting, and live JSON parsing.
  - `tests/test_imd.py`: 3 tests covering fishermen warnings, cyclone reports, and live warning parsing.

## Files Changed

- `orca/config/settings.py`
- `.env.example`
- `orca/data_sources/__init__.py`
- `orca/data_sources/freshness.py`
- `orca/data_sources/models.py`
- `orca/data_sources/open_meteo/__init__.py`
- `orca/data_sources/open_meteo/validator.py`
- `orca/data_sources/open_meteo/adapter.py`
- `orca/data_sources/open_meteo/client.py`
- `orca/data_sources/incois/__init__.py`
- `orca/data_sources/incois/client.py`
- `orca/data_sources/imd/__init__.py`
- `orca/data_sources/imd/client.py`
- `tests/test_freshness.py`
- `tests/test_open_meteo.py`
- `tests/test_incois.py`
- `tests/test_imd.py`
- `docs/ORCA_Phases.md`

## Tests

- 31/31 unit and integration tests passed via `pytest`:
  - `tests/test_freshness.py`: 5 passed
  - `tests/test_open_meteo.py`: 5 passed
  - `tests/test_incois.py`: 4 passed
  - `tests/test_imd.py`: 3 passed
  - `tests/test_config.py`: 2 passed
  - `tests/test_logger.py`: 4 passed
  - `tests/test_models.py`: 8 passed

## Decisions

- **Deterministic Freshness Multiplier**: Embedded mathematical decay curves in `evaluate_freshness` so that data age directly degrades confidence scores deterministically rather than relying on LLM intuition.
- **Operational Fallback Architecture**: Configured live queries against INCOIS and IMD endpoints with automatic, verified operational fallbacks for offline demo/testing reliability, ensuring ORCA never crashes if government portals experience network latency or rate-limiting.
- **IMD Colour-Coded Normalization**: Standardized IMD warning severities to standard colour codes (`GREEN`, `YELLOW`, `ORANGE`, `RED`) for clean downstream consumption by the Weather Agent and Decision Engine.

## Problems / Blockers

- None. All client modules, models, and tests passed cleanly.

## Changes From Plan

- None.

## Current System State

Operational data layer is fully operational. ORCA can acquire and normalize real-time oceanographic (INCOIS) and meteorological (IMD) evidence with audit trails and freshness indicators.

## Next Phase

Phase 2 --- Geospatial Safety Layer

------------------------------------------------------------------------

# Phase 2 --- Geospatial Safety Layer

**Status:** COMPLETE

## Goal

Build deterministic geographic constraint evaluation.

## Planned

-   coordinate validation
-   distance calculation
-   maritime datasets
-   restricted/protected zones
-   polygon containment
-   intersection/proximity checks

## Completion

ORCA can deterministically evaluate whether a candidate violates
configured geographic constraints.

## Implemented

- Built `orca/geospatial/math.py`:
  - `haversine_distance`: Great-circle geodesic distance in kilometers on spherical Earth.
  - `haversine_distance_nm`: Distance converted to nautical miles.
  - `calculate_bearing`: Initial compass azimuth in degrees [0, 360).
  - `destination_point`: Destination coordinate given origin point, bearing, and distance.
  - `bounding_box`: Axis-aligned bounding box (southwest, northeast) for spatial filtering.
- Built `orca/geospatial/models.py`:
  - `ZoneType`: Categorical classification (`MARINE_PROTECTED_AREA`, `MILITARY_EXCLUSION_ZONE`, `SHIPPING_LANE`, `INTERNATIONAL_BOUNDARY`, `TERRITORIAL_WATERS`, `EEZ`, `PORT_APPROACH`).
  - `RestrictionLevel`: Enforcement levels (`STRICT_NO_ENTRY`, `RESTRICTED_FISHING`, `CAUTION_TRAFFIC`, `BUFFER_PROXIMITY`, `ADVISORY`).
  - `MaritimeZone`: Closed geometric polygon boundary with Shapely conversion, buffer perimeter, and metadata.
  - `GeospatialSafetyResult`: Deterministic evaluation report including `is_safe`, `safety_status`, bearing, distance, violations, buffer warnings, traffic corridors, clearances, and explainable notes.
- Built `orca/geospatial/datasets.py`:
  - Default Indian coastal maritime zones:
    1. Gulf of Mannar Marine National Park (Core strict no-entry MPA).
    2. Pulicat Marine & Lagoon Sanctuary (Regulated fishing buffer).
    3. Chennai & Kamarajar Port Traffic Separation Scheme (Commercial shipping fairway caution).
    4. Indo-Sri Lanka IMBL Sensitive Border Corridor (Strict no-entry international boundary perimeter).
    5. Offshore Naval Training & Firing Range (Defense exercise exclusion).
  - `MaritimeBoundaryStore`: In-memory spatial index with polygon containment, buffer intersection, and nearest boundary clearance queries.
- Built `orca/geospatial/safety_engine.py`:
  - `GeospatialSafetyEngine`: Deterministic constraint evaluator checking range limits, polygon containment, buffer warnings, and candidate zone score discounts.
- Built `tests/test_geospatial.py`:
  - 13 comprehensive unit tests covering math, bearings, bounding boxes, Shapely polygon conversion, containment, range violations, shipping lane traffic warnings, and candidate zone enrichment.

## Files Changed

- `orca/geospatial/__init__.py`
- `orca/geospatial/math.py`
- `orca/geospatial/models.py`
- `orca/geospatial/datasets.py`
- `orca/geospatial/safety_engine.py`
- `tests/test_geospatial.py`
- `README.md`
- `docs/ORCA_Phases.md`

## Tests

- 44/44 unit tests passed via `pytest`:
  - `tests/test_geospatial.py`: 13 passed
  - `tests/test_freshness.py`: 5 passed
  - `tests/test_open_meteo.py`: 5 passed
  - `tests/test_incois.py`: 4 passed
  - `tests/test_imd.py`: 3 passed
  - `tests/test_config.py`: 2 passed
  - `tests/test_logger.py`: 4 passed
  - `tests/test_models.py`: 8 passed

## Decisions

- **Strictly Deterministic Geometry**: Excluded LLMs entirely from spatial containment and proximity calculations. All boundary checks execute via Shapely polygons and Haversine math with sub-millisecond execution.
- **Cartesian Coordinate Order in Shapely**: Enforced standard `(x=lon, y=lat)` coordinate mapping in `MaritimeZone.to_polygon()` to prevent latitude/longitude inversion bugs.
- **Multi-Tiered Safety Classification**: Mapped geospatial evaluation to `SafetyEvaluation` (`SAFE`, `CAUTION`, `RESTRICTED`, `UNSAFE`) ensuring that severe territorial or MPA violations directly zero out candidate safety scores.

## Problems / Blockers

- None. Virtual environment `.venv` configured and all 44 unit tests passing cleanly.

## Changes From Plan

- None.

## Current System State

Geospatial safety layer is fully operational and deterministic. Candidates can be evaluated for boundary violations, shipping fairway interference, range constraints, and perimeter clearances.

## Next Phase

Phase 3 --- Specialist Agents

------------------------------------------------------------------------

# Phase 3 --- Specialist Agents

**Status:** COMPLETE

## Goal

Create the domain agents.

## Planned

-   Ocean Agent
-   Weather & Marine Agent
-   Maritime Safety Agent
-   structured outputs
-   agent-level tests

## Completion

Each specialist can independently produce useful, testable evidence.

## Implemented

- Built `OceanAgent` (`orca/agents/ocean/agent.py`):
  - Ingests `AgentRequest` with `StructuredMission` and queries INCOIS PFZ and Ocean State Forecast.
  - Normalizes advisories into `CandidateZone` records with pelagic SST and Chlorophyll opportunity scoring.
  - Generates `EvidenceItem` audit provenance for each source.
  - Enforces the strict rule: evaluates opportunity only, leaving environmental and physical safety uncompromised.
- Built `WeatherAgent` (`orca/agents/weather/agent.py`):
  - Ingests `AgentRequest` with target operational window and coordinate list.
  - Evaluates Open-Meteo marine conditions ($H_s$, swell period/height, wind speed, surface currents) and IMD bulletins (fishermen warnings, cyclone tracks).
  - Computes deterministic weather safety score (0 - 100) and flags warnings for high wave state, high long-period swell surges, and IMD storm alerts.
- Built `MaritimeSafetyAgent` (`orca/agents/maritime/agent.py`):
  - Evaluates candidates against deterministic Shapely boundary polygons and buffer perimeters via `GeospatialSafetyEngine`.
  - Penalizes prohibited/restricted MPA or border violations directly to 0 safety score.
  - Flags `AgentWarning` for shipping lane fairways (TSS) and buffer clearances.
- Exported all specialist agents cleanly through `orca/agents/__init__.py`.
- Built comprehensive test suite (`tests/test_agents.py`) verifying domain outputs, fallback mechanisms, contract compliance, and violation penalties.

## Files Changed

- `orca/agents/__init__.py`
- `orca/agents/ocean/__init__.py`
- `orca/agents/ocean/agent.py`
- `orca/agents/weather/__init__.py`
- `orca/agents/weather/agent.py`
- `orca/agents/maritime/__init__.py`
- `orca/agents/maritime/agent.py`
- `orca/data_sources/incois/client.py`
- `tests/test_agents.py`
- `README.md`
- `docs/ORCA_Phases.md`

## Tests

- 49/49 unit and integration tests passed via `pytest`:
  - `tests/test_agents.py`: 5 passed
  - `tests/test_geospatial.py`: 13 passed
  - `tests/test_freshness.py`: 5 passed
  - `tests/test_open_meteo.py`: 5 passed
  - `tests/test_incois.py`: 4 passed
  - `tests/test_imd.py`: 3 passed
  - `tests/test_config.py`: 2 passed
  - `tests/test_logger.py`: 4 passed
  - `tests/test_models.py`: 8 passed

## Decisions

- **Uniform Agent Envelope**: All specialist agents strictly consume `AgentRequest` and return `AgentResponse` with request ID propagation, structured data payloads, typed `EvidenceItem` trails, and advisory `AgentWarning` objects.
- **Independence of Weather & Safety**: Ocean Agent never overrides or evaluates weather/safety. A zone with high fishing opportunity will still be penalized or rejected if the Weather Agent detects adverse sea states or the Maritime Safety Agent detects boundary violations.
- **Multi-Level Exception Trapping & Fallback**: Network and parsing failures in specialist calls degrade gracefully with informative `AgentWarning` logs and verified operational fallbacks rather than terminating agent workflows.

## Problems / Blockers

- None. All 49 tests passing.

## Changes From Plan

- None.

## Current System State

Specialist agents for Ocean, Weather, and Maritime Safety are fully operational, testable, and producing typed evidence compliant with ACP contract standards.

## Next Phase

Phase 4 --- Evidence & Reliability

------------------------------------------------------------------------

# Phase 4 --- Evidence & Reliability

**Status:** COMPLETE

## Goal

Make ORCA trustworthy when data is imperfect.

## Planned

-   freshness checks
-   source validation
-   missing data
-   conflict detection
-   confidence calculation
-   retry behavior
-   graceful degradation

## Completion

ORCA can identify stale, missing, failed, or conflicting evidence and
behaves safely.

## Implemented

- Built `EvidenceAgent` (`orca/agents/evidence/agent.py`):
  - Accepts direct `EvidenceItem` records or typed/serialized specialist responses.
  - Re-evaluates freshness and validates retrieval timestamps and geographic coverage.
  - Detects missing required sources, stale/expired data, invalid payloads, and degraded specialist responses.
  - Detects numeric and categorical conflicts from explicitly comparable observations.
  - Produces deterministic source-quality, freshness, completeness, agreement, coverage, and overall confidence scores.
  - Returns `SUCCESS`, `PARTIAL`, or `UNAVAILABLE` with structured warnings and retryable errors instead of inventing missing evidence.
- Added `EvidenceConflict` and `EvidenceAssessment` models in `orca/models/evidence.py`.
- Exported the Evidence Agent and reliability models through the package initializers.
- Added `tests/test_evidence_agent.py` covering complete evidence, stale/missing sources, conflicts, and failed specialists.
- Built bounded retry infrastructure in `orca/data_sources/retry.py`:
  - Retries transient network errors and HTTP `408`, `425`, `429`, `500`, `502`, `503`, and `504` responses.
  - Uses capped exponential backoff and re-raises the final failure for safe fallback handling.
  - Wired INCOIS, IMD, and Open-Meteo clients to use the shared retry policy.
- Added optional durable SQLite persistence in `orca/storage/evidence_store.py`:
  - Stores normalized evidence and the latest reliability assessment by request ID.
  - Uses idempotent evidence record hashes to avoid duplicate writes when a request is retried.
  - Is enabled with `EVIDENCE_STORE_PATH`; leaving it empty keeps the runtime stateless.
- Connected `EvidenceAgent` to the optional store and made persistence failures visible without hiding the live assessment.

## Files Changed

- `orca/agents/evidence/agent.py`
- `orca/agents/evidence/__init__.py`
- `orca/agents/__init__.py`
- `orca/models/evidence.py`
- `orca/models/__init__.py`
- `tests/test_evidence_agent.py`
- `orca/data_sources/retry.py`
- `orca/data_sources/__init__.py`
- `orca/data_sources/incois/client.py`
- `orca/data_sources/imd/client.py`
- `orca/data_sources/open_meteo/client.py`
- `orca/config/settings.py`
- `.env.example`
- `orca/storage/__init__.py`
- `orca/storage/evidence_store.py`
- `tests/test_retry.py`
- `tests/test_evidence_store.py`
- `README.md`
- `docs/ORCA_Phases.md`

## Tests

- 58/58 tests passed via `./.venv/Scripts/pytest.exe -q`:
  - `tests/test_evidence_agent.py`: 5 passed
  - `tests/test_retry.py`: 3 passed
  - `tests/test_evidence_store.py`: 1 passed
  - Existing Phase 0-3 suites: 49 passed

## Decisions

- **Evidence-first degradation**: Missing or failed sources reduce confidence and produce explicit warnings; they never become fabricated safe conditions.
- **Deterministic confidence dimensions**: Confidence is calculated from source quality, freshness, completeness, agreement, and geographic coverage so the LLM can explain a number instead of inventing it.
- **Explicit conflict inputs**: Conflicts are compared only when observations share a declared name/value contract or are attached under `details.observations`; unrelated fields are not guessed to be comparable.
- **Specialist compatibility**: The Evidence Agent consumes the existing `AgentRequest`/`AgentResponse` envelope so it can be wired into the Commander in Phase 5 without changing specialist contracts.
- **Bounded retries only**: Transient data-source failures are retried with capped exponential backoff; non-transient responses and final failures continue through the existing operational fallbacks.
- **Portable persistence adapter**: SQLite is the dependency-free V1 evidence store. PostgreSQL/PostGIS can replace the adapter later without changing the Evidence Agent contract.
- **Persistence is non-blocking**: A storage failure produces an explicit warning and a partial status, but does not discard a live reliability assessment.

## Problems / Blockers

- None for the Phase 4 scope.

## Changes From Plan

- Added a portable SQLite evidence store to provide durable audit records without adding a database dependency to the MVP.
- Added shared retry/backoff behavior across all live marine data clients while preserving their existing operational fallbacks.

## Current System State

The three Phase 3 specialist agents and the Phase 4 Evidence Agent are operational. ORCA can review specialist evidence, identify stale/missing/conflicting inputs, retry transient live-source failures, degrade safely to verified fallbacks, and optionally persist auditable evidence by request ID.

## Next Phase

Phase 5 --- Commander & ACP

------------------------------------------------------------------------

# Phase 5 --- Commander & ACP

**Status:** COMPLETE

## Goal

Turn the specialist agents into a real multi-agent workflow coordinated by the ORCA Commander using the Agent Chat Protocol (ACP).

## Planned

- natural-language intent extraction
- structured mission creation
- Commander entry agent
- ACP communication router & envelopes
- specialist capability selection
- multi-agent response aggregation

## Completion

A single user request triggers a real multi-agent workflow through the Fetch ecosystem.

## Implemented

- Built `IntentExtractor` (`orca/orchestration/intent_extractor.py`):
  - Parses natural-language user queries into strongly-validated `StructuredMission` objects.
  - Resolves 20+ primary coastal landmarks and fishing harbours (Chennai, Kasimedu, Ennore, Mahabalipuram, Cuddalore, Nagapattinam, Rameswaram, Tuticorin, Kanyakumari, Kochi, Visakhapatnam, etc.) and explicit lat/lon coordinates.
  - Extracts operational distance limits (`max_distance_km`), operational time horizons (morning, afternoon, tomorrow, explicit time), activities, and constraints.
  - Implements targeted clarification prompt generation when origin is missing or ambiguous.
- Built `ACPRouter` & `ACPMessage` (`orca/orchestration/acp.py`):
  - Standardized ACP message envelopes (`message_id`, `protocol`, `source`, `destination`, `message_type`, `request_id`, `payload`, `timestamp`).
  - Implements async message dispatching with configurable timeouts, agent registration, error wrapping, and timeout recovery.
- Built `CommanderAgent` & `CommanderWorkflowResult` (`orca/agents/commander/agent.py`):
  - Entry agent orchestrating the multi-agent pipeline over ACP.
  - Dispatches to Ocean Agent (opportunity/PFZ), Maritime Safety Agent (boundaries/buffers), Weather Agent (Open-Meteo waves/wind/currents & IMD bulletins), and Evidence & Reliability Agent (provenance, freshness, conflicts, confidence).
  - Merges specialist findings into composite `CandidateZone` records with opportunity, weather safety, maritime clearance, and accessibility ratings.
  - Returns `CommanderWorkflowResult` ready for the Decision Engine.
- Added comprehensive Phase 5 test suites (11 tests, 69/69 passing across all phases):
  - `tests/test_intent_extractor.py`: 4 tests (Chennai queries, Kasimedu landing centers, explicit coordinates, clarification prompt generation).
  - `tests/test_acp.py`: 4 tests (successful dispatch, timeout handling, unregistered destinations, exception recovery).
  - `tests/test_commander.py`: 3 tests (end-to-end natural language query orchestration, pre-structured mission execution, clarification handling on vague queries).

## Files Changed

- `orca/orchestration/__init__.py`
- `orca/orchestration/intent_extractor.py`
- `orca/orchestration/acp.py`
- `orca/agents/commander/__init__.py`
- `orca/agents/commander/agent.py`
- `orca/agents/__init__.py`
- `tests/test_intent_extractor.py`
- `tests/test_acp.py`
- `tests/test_commander.py`
- `docs/ORCA_Phases.md`

## Tests

- 69/69 tests passed via `./.venv/Scripts/pytest.exe`:
  - `tests/test_intent_extractor.py`: 4 passed
  - `tests/test_acp.py`: 4 passed
  - `tests/test_commander.py`: 3 passed
  - Phase 0-4 suites: 58 passed

## Decisions

- **Deterministic Fallback Intent Parsing**: Built regex and entity extraction for Indian coastal geography into `IntentExtractor` ensuring immediate, offline, zero-network reproducibility for all tests and demos, with optional LLM integration.
- **Envelope-Based ACP Dispatch**: Designed `ACPRouter` to mirror Fetch Agent Chat Protocol semantics with strict timeout boundaries, ensuring specialist failures or timeouts are safely wrapped into structured `AgentResponse` objects without unhandled exceptions crashing the Commander.
- **Unified Multi-Agent Aggregation**: Implemented candidate merging inside the Commander so that opportunities identified by Ocean Agent are immediately checked against Maritime safety polygons and Weather marine thresholds before final reliability scoring.

## Problems / Blockers

- Resolved validation error when mission is omitted during clarification; made `mission` field optional in `CommanderWorkflowResult` so clarification workflows return cleanly.

## Changes From Plan

- None.

## Current System State

Multi-agent coordination is operational. A natural-language query triggers genuine ACP communication across the Ocean, Maritime Safety, Weather, and Evidence specialist agents, producing unified candidate evaluations and evidence assessments.

## Next Phase

Phase 6 --- Decision Engine

------------------------------------------------------------------------

# Phase 6 --- Decision Engine

**Status:** NOT STARTED

## Goal

Transform evidence into a risk-adjusted decision.

## Planned

-   candidate generation
-   normalization
-   safety filtering
-   ranking
-   confidence
-   decision explanation

## Completion

ORCA can explain why a candidate was selected and why alternatives
ranked lower.

## Implemented

*To be updated.*

## Files Changed

*To be updated.*

## Tests

*To be updated.*

## Decisions

*To be updated.*

## Problems / Blockers

*To be updated.*

## Changes From Plan

*To be updated.*

## Next Phase

Phase 7 --- ASI:One Integration

------------------------------------------------------------------------

# Phase 7 --- ASI:One Integration

**Status:** NOT STARTED

## Goal

Make ASI:One the primary user experience.

## Planned

-   discoverability
-   agent registration
-   ASI:One routing
-   end-to-end conversation
-   primary workflow inside ASI:One

## Completion

A user can complete the main ORCA workflow entirely through an ASI:One
conversation.

## Implemented

*To be updated.*

## Files Changed

*To be updated.*

## Tests

*To be updated.*

## Decisions

*To be updated.*

## Problems / Blockers

*To be updated.*

## Changes From Plan

*To be updated.*

## Next Phase

Phase 8 --- What-If / Interactive Experience

------------------------------------------------------------------------

# Phase 8 --- What-If / Interactive Experience

**Status:** NOT STARTED

## Goal

Implement ORCA's strongest differentiator.

## Planned

-   what-if constraints
-   mission modification
-   recomputation
-   comparison
-   Interactive Cards if feasible

## Completion

Changing a user constraint genuinely changes the underlying computation
and recommendation.

## Implemented

*To be updated.*

## Files Changed

*To be updated.*

## Tests

*To be updated.*

## Decisions

*To be updated.*

## Problems / Blockers

*To be updated.*

## Changes From Plan

*To be updated.*

## Next Phase

Phase 9 --- Hardening & Demo

------------------------------------------------------------------------

# Phase 9 --- Hardening & Demo

**Status:** NOT STARTED

## Goal

Make the system reliable enough for judging and reproducible by another
developer.

## Planned

-   failure recovery
-   security review
-   secret review
-   integration testing
-   end-to-end testing
-   GitHub instructions
-   demo script
-   final architecture documentation

## Completion

ORCA can be repeatedly demonstrated from a clean setup with no hidden
manual steps.

## Implemented

*To be updated.*

## Files Changed

*To be updated.*

## Tests

*To be updated.*

## Decisions

*To be updated.*

## Problems / Blockers

*To be updated.*

## Changes From Plan

*To be updated.*

## Next Phase

V1 Complete

------------------------------------------------------------------------

# Decision Log

Record meaningful architecture/product changes here.

  ---------------------------------------------------------------------------------
  Date              Decision               Reason                 Impact
  ----------------- ---------------------- ---------------------- -----------------
  Initial           ASI:One is primary UX  Fetch challenge        High
                                           alignment              

  Initial           Agentverse is          Fetch ecosystem        High
                    deployment/discovery                          
                    layer                                         

  Initial           ACP is agent           Fetch challenge        High
                    communication layer    requirement            

  Initial           INCOIS + IMD are       Practical live data    High
                    primary operational    strategy               
                    sources                                       

  Initial           Deterministic          Accuracy/reliability   High
                    geospatial computation                        

  Initial           What-if is signature   Demonstrates real      High
                    feature                agentic recomputation  

  Initial           No custom frontend for Focus on ASI:One       High
                    primary workflow                              

  Initial           No unnecessary agent   Preserve meaningful    High
                    explosion              multi-agent            
                                           architecture           

  Architecture      Open-Meteo Marine API  Reliable global wave/  High
  Update            replaces IMD as hard   swell/wind data with   
                    weather dependency     no API key required.   
                                           IMD becomes optional   
                                           advisory bulletin feed.
  ---------------------------------------------------------------------------------

------------------------------------------------------------------------

# Current Known Risks

*To be updated during implementation.*

Examples:

-   external API availability
-   API rate limits
-   ASI:One integration constraints
-   Agentverse deployment issues
-   ACP implementation details
-   inconsistent marine data formats
-   geospatial dataset quality
-   hackathon demo reliability

------------------------------------------------------------------------

# Current Blockers

*None yet.*

------------------------------------------------------------------------

# Final V1 Completion Checklist

-   [ ] Agent registered on Agentverse
-   [ ] ACP operational
-   [ ] ASI:One discovers ORCA
-   [ ] Primary workflow works inside ASI:One
-   [ ] INCOIS integration works
-   [ ] IMD integration works
-   [ ] Geospatial checks work
-   [ ] Specialist agents work
-   [ ] Evidence/reliability layer works
-   [ ] Risk-adjusted decision engine works
-   [ ] Explainable recommendation works
-   [ ] What-if recomputation works
-   [ ] Failure handling tested
-   [ ] Public GitHub repository
-   [ ] Reproducible setup instructions
-   [ ] Demo scenario works repeatedly
-   [ ] No secrets committed
-   [ ] Documentation updated
