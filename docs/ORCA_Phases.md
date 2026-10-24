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

**Current Phase:** Phase 2 --- Geospatial Safety Layer\
**Status:** IN PROGRESS

## Overall Progress

``` text
Phase 0  Foundation              [X] 
Phase 1  Marine Data Layer       [X]
Phase 2  Geospatial Safety       [ ]
Phase 3  Specialist Agents       [ ]
Phase 4  Evidence & Reliability  [ ]
Phase 5  Commander & ACP         [ ]
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

**Status:** NOT STARTED

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

Phase 3 --- Specialist Agents

------------------------------------------------------------------------

# Phase 3 --- Specialist Agents

**Status:** NOT STARTED

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

Phase 4 --- Evidence & Reliability

------------------------------------------------------------------------

# Phase 4 --- Evidence & Reliability

**Status:** NOT STARTED

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

Phase 5 --- Commander & ACP

------------------------------------------------------------------------

# Phase 5 --- Commander & ACP

**Status:** NOT STARTED

## Goal

Turn the specialist agents into a real multi-agent workflow.

## Planned

-   natural-language intent extraction
-   structured mission
-   Commander
-   ACP communication
-   capability routing
-   response aggregation

## Completion

A single user request triggers a real multi-agent workflow through the
Fetch ecosystem.

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
