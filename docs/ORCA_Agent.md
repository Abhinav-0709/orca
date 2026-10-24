# ORCA --- Agent Development Instructions

**Project:** ORCA --- Ocean Reasoning & Coordination Agent\
**Hackathon:** Fetch-A-Thon 3.0\
**Primary UX:** ASI:One\
**Discovery/Deployment:** Agentverse\
**Agent Communication:** ACP\
**Status:** Living implementation document

------------------------------------------------------------------------

# 1. Purpose

This file is the **implementation guide for the ORCA coding
agent/developer**.

It explains:

-   what ORCA is,
-   what technologies and data sources we will use,
-   how the implementation will be phased,
-   how the project should evolve,
-   which documents must be consulted,
-   how progress must be recorded,
-   what completion means,
-   and how the system should be kept aligned with the ORCA product
    vision.

This is **not** the place for every product decision.

The project is governed by a small set of companion documents:

``` text
ORCA_Fetch_Athon_Core_Idea.md
        ↓
Product definition / architecture / scope

ORCA_Project_Constraints.md
        ↓
Rules / behavior / things we must not build

ORCA_Agent.md
        ↓
Implementation instructions

ORCA_Phases.md
        ↓
Living development state / phase progress
```

The agent must refer to the other documents instead of duplicating or
silently changing their decisions.

------------------------------------------------------------------------

# 2. Golden Development Rule

## We are NOT building ORCA in one go.

ORCA must be implemented **phase by phase**.

Each phase should produce a working increment.

Do not attempt to create:

-   all agents,
-   all APIs,
-   all reasoning,
-   all UI/cards,
-   all deployment configuration,

in a single pass.

Instead:

``` text
Plan
 ↓
Implement one phase
 ↓
Run / test
 ↓
Document result
 ↓
Update ORCA_Phases.md
 ↓
Lock what changed
 ↓
Move to next phase
```

The project should remain runnable at the end of every meaningful phase.

------------------------------------------------------------------------

# 3. Source of Truth

Before making a major implementation decision, refer to:

### 1. Core Idea

`ORCA_Fetch_Athon_Core_Idea.md`

Use it for:

-   product definition,
-   core workflow,
-   architecture,
-   data strategy,
-   USP,
-   MVP scope,
-   hackathon strategy.

### 2. Constraints

`ORCA_Project_Constraints.md`

Use it for:

-   prohibited scope,
-   behavior rules,
-   safety rules,
-   reliability requirements,
-   ASI:One rules,
-   deterministic vs LLM responsibilities,
-   failure handling,
-   Fetch requirements.

### 3. Phases

`ORCA_Phases.md`

Use it for:

-   current implementation phase,
-   completed work,
-   active work,
-   pending work,
-   decisions made during implementation,
-   known blockers,
-   next phase.

### Rule

**Do not silently change a locked product decision in code.**

If implementation reveals that a decision must change:

1.  explain why,
2.  record the change,
3.  update the relevant document,
4.  update `ORCA_Phases.md`,
5.  then implement the change.

------------------------------------------------------------------------

# 4. Core Technology Direction

The initial ORCA implementation should use a pragmatic backend-heavy
stack.

## Application

### Python

Primary backend/orchestration language.

Reason:

-   strong API ecosystem,
-   geospatial libraries,
-   data processing,
-   LLM integrations,
-   rapid agent development.

------------------------------------------------------------------------

# 5. Agent Framework

ORCA should remain compatible with Fetch's ecosystem.

Primary concepts:

-   Agentverse
-   ASI:One
-   ACP
-   Fetch/uAgents where appropriate

uAgents is preferred where it naturally simplifies Fetch-native agent
deployment.

However:

> Do not use uAgents merely because it is a Fetch technology.

If another supported framework provides a cleaner implementation for a
specific reasoning/orchestration component, it may be used, provided the
Fetch integration remains real.

------------------------------------------------------------------------

# 6. LLM / Reasoning Layer

The reasoning layer should be model-agnostic.

Potential models/providers:

-   ASI1 / ASI:One
-   Gemini
-   OpenAI
-   other compatible LLM providers where useful

The implementation should avoid hard-coding the entire system around one
model where unnecessary.

## LLM responsibilities

Use the LLM for:

-   intent interpretation,
-   structured mission extraction,
-   natural-language clarification,
-   agent selection/orchestration,
-   evidence interpretation,
-   trade-off explanation,
-   final response generation.

Do not use the LLM for:

-   distance calculations,
-   polygon intersection,
-   numeric scoring that can be deterministic,
-   timestamp arithmetic,
-   coordinate validation,
-   data freshness calculations.

------------------------------------------------------------------------

# 7. Data Sources

## Primary operational sources

### INCOIS

Use for marine/ocean intelligence such as:

-   Potential Fishing Zone information,
-   ocean state forecasts,
-   wave height,
-   swell,
-   wind,
-   currents,
-   SST,
-   chlorophyll,
-   marine alerts where available.

Primary reference:

`https://www.incois.gov.in/`

### IMD

Use for meteorological and marine warnings such as:

-   fishermen warnings,
-   sea-area bulletins,
-   coastal bulletins,
-   cyclone information,
-   cyclone wind warnings,
-   other relevant warnings.

Primary reference:

`https://mausam.imd.gov.in/`

and API reference:

`https://api.imd.gov.in/public/api_reference.html`

------------------------------------------------------------------------

# 8. Secondary Data Sources

## MOSDAC / ISRO

Potential use:

-   satellite-derived ocean information,
-   additional remote-sensing evidence,
-   future advanced satellite processing.

Do not make raw satellite ingestion a hard MVP dependency unless the
implementation phase explicitly requires it.

## Marine Regions

Potential use:

-   EEZ geometry,
-   territorial sea geometry,
-   maritime spatial datasets.

Use for prototype geospatial decision support.

Do not represent it as legal maritime authority.

------------------------------------------------------------------------

# 9. Geospatial Stack

Use deterministic geospatial computation.

Potential stack:

``` text
GeoPandas
Shapely
PostGIS
```

The exact choice depends on the current phase.

## Rules

Use geometry libraries for:

-   distance,
-   polygon containment,
-   intersection,
-   proximity,
-   geofencing,
-   candidate filtering.

Do not ask the LLM to perform these calculations.

------------------------------------------------------------------------

# 10. Database

Initial preference:

### PostgreSQL

Use it for:

-   structured mission records,
-   candidate zones,
-   agent outputs,
-   evidence metadata,
-   audit/trace information,
-   configuration.

### PostGIS

Use when geospatial queries become substantial.

### pgvector

Use only if semantic/vector retrieval is actually required.

Do not add a vector database simply because the project contains AI.

------------------------------------------------------------------------

# 11. Caching / Infrastructure

Keep infrastructure minimal.

Redis is **not required for V1 by default**.

Only introduce Redis or similar infrastructure when a concrete
requirement appears, such as:

-   high-frequency caching,
-   distributed coordination,
-   rate limiting,
-   queueing,
-   real-time state.

Avoid infrastructure for infrastructure's sake.

------------------------------------------------------------------------

# 12. Core ORCA Agents

The conceptual agent system is:

``` text
1. ORCA Commander
2. Ocean Intelligence Agent
3. Weather & Marine Forecast Agent
4. Maritime Safety Agent
5. Evidence & Reliability Agent
```

A Reasoning/Decision layer coordinates the final decision.

Do not create additional agents unless a real capability boundary
requires them.

------------------------------------------------------------------------

# 13. Agent Responsibilities

## Commander

Owns:

-   user intent,
-   mission creation,
-   orchestration,
-   agent selection,
-   response aggregation,
-   final workflow coordination.

## Ocean Agent

Owns:

-   fishing opportunity,
-   PFZ,
-   SST,
-   chlorophyll,
-   ocean conditions.

## Weather Agent

Owns:

-   marine weather,
-   wave conditions,
-   wind,
-   swell,
-   marine warnings,
-   cyclone risk.

## Maritime Agent

Owns:

-   geospatial constraints,
-   boundaries,
-   restricted/protected zones,
-   candidate proximity/intersection.

## Evidence Agent

Owns:

-   freshness,
-   source quality,
-   completeness,
-   disagreement,
-   confidence,
-   failure detection.

------------------------------------------------------------------------

# 14. Standard Internal Data Flow

Every user request should conceptually follow:

``` text
Natural Language
      ↓
Intent Extraction
      ↓
Structured Mission
      ↓
Capability Selection
      ↓
Agent Calls
      ↓
Evidence Collection
      ↓
Validation / Reconciliation
      ↓
Candidate Generation
      ↓
Risk-Adjusted Ranking
      ↓
Decision
      ↓
Explanation
```

This flow should remain understandable in code.

------------------------------------------------------------------------

# 15. Structured Mission

Use a structured object similar to:

``` json
{
  "activity": "fishing",
  "origin": {
    "lat": 0,
    "lon": 0
  },
  "time_window": {
    "start": "",
    "end": ""
  },
  "max_distance_km": 30,
  "objective": "high_fishing_potential",
  "constraints": [
    "low_weather_risk",
    "avoid_restricted_zones"
  ]
}
```

The exact schema can evolve.

Changes must be recorded in `ORCA_Phases.md`.

------------------------------------------------------------------------

# 16. Agent Output Contract

Agents should return structured data.

Conceptual shape:

``` json
{
  "agent": "ocean",
  "status": "success",
  "request_id": "...",
  "data": {},
  "evidence": [],
  "warnings": [],
  "confidence": 0.0,
  "timestamp": "..."
}
```

Failure:

``` json
{
  "agent": "weather",
  "status": "failed",
  "request_id": "...",
  "error": {
    "type": "TIMEOUT",
    "message": "Marine forecast unavailable"
  },
  "retryable": true
}
```

Structured contracts are preferred over passing arbitrary prose between
agents.

------------------------------------------------------------------------

# 17. Decision Engine

The conceptual objective is:

``` text
Risk-Adjusted Decision
=
Opportunity
×
Safety
×
Accessibility
×
Data Confidence
```

The exact implementation must be documented and calibrated.

The system must be able to explain:

-   why candidate A won,
-   why candidate B lost,
-   which constraint mattered,
-   how confidence affected the result.

------------------------------------------------------------------------

# 18. What-If Engine

The signature ORCA capability is:

> Recompute the decision when the user's constraints change.

Examples:

``` text
“What if I go 15 km farther?”

“What if I leave at 5 AM?”

“What if I prioritize safety?”

“What if I accept moderate wave risk?”
```

The implementation should modify the structured mission and rerun
affected decision logic.

It must not simply generate a new explanation without recomputation.

------------------------------------------------------------------------

# 19. Reliability Requirements

Every external dependency must be treated as fallible.

Possible states:

``` text
SUCCESS
PARTIAL
STALE
TIMEOUT
UNAVAILABLE
INVALID
CONFLICTING
```

The system must never turn:

``` text
API failure
```

into:

``` text
assumed safe conditions
```

If critical information is unavailable, ORCA should:

-   lower confidence,
-   warn the user,
-   or withhold the recommendation.

------------------------------------------------------------------------

# 20. Testing Strategy

Testing should happen continuously.

## Unit tests

Test:

-   distance calculations,
-   geospatial functions,
-   score calculations,
-   freshness calculations,
-   input validation,
-   response schemas.

## Integration tests

Test:

-   INCOIS integration,
-   IMD integration,
-   agent communication,
-   ACP workflow,
-   database interaction.

## Agent tests

Test:

-   intent extraction,
-   routing,
-   structured output,
-   failure behavior,
-   disagreement handling.

## End-to-end tests

Test the complete path:

``` text
User intent
→ Commander
→ specialists
→ evidence
→ ranking
→ final recommendation
```

------------------------------------------------------------------------

# 21. Development Workflow

For every implementation task:

### Step 1 --- Understand

Read:

-   `ORCA_Fetch_Athon_Core_Idea.md`
-   `ORCA_Project_Constraints.md`
-   `ORCA_Phases.md`

### Step 2 --- Identify phase

Determine the current active phase.

### Step 3 --- Implement only the phase scope

Do not jump ahead.

### Step 4 --- Test

Run relevant tests.

### Step 5 --- Validate against constraints

Ask:

-   Did we violate scope?
-   Did we introduce unnecessary infrastructure?
-   Did we make the LLM responsible for deterministic work?
-   Did we preserve Fetch integration?
-   Did we create a fake agent capability?

### Step 6 --- Update phase document

Record:

-   what changed,
-   files added,
-   files modified,
-   tests,
-   decisions,
-   blockers,
-   next step.

### Step 7 --- Continue

Only after the current phase is stable.

------------------------------------------------------------------------

# 22. Required Phase Update Format

`ORCA_Phases.md` is a **living document**.

Whenever implementation changes meaningfully, update it.

Each phase should contain:

``` markdown
## Phase X — Name

Status: COMPLETE / IN PROGRESS / BLOCKED

### Goal

...

### Implemented

- ...
- ...

### Files

- ...

### APIs / Sources

- ...

### Tests

- ...

### Decisions

- ...

### Problems

- ...

### Changes from Previous Plan

- ...

### Current System State

...

### Next Phase

...
```

Do not create a new phase file for every change.

Keep one continuously updated:

``` text
ORCA_Phases.md
```

------------------------------------------------------------------------

# 23. Phase Planning

The implementation should follow progressive phases.

## Phase 0 --- Project Foundation

Goal:

-   repository structure,
-   environment,
-   configuration,
-   logging,
-   basic documentation,
-   test framework.

Completion:

> Repository runs locally and has a clean foundation.

------------------------------------------------------------------------

## Phase 1 --- Marine Data Layer

Goal:

-   connect to INCOIS,
-   connect to IMD where required,
-   normalize responses,
-   record timestamps,
-   validate source data.

Completion:

> ORCA can retrieve and normalize real marine/weather evidence.

------------------------------------------------------------------------

## Phase 2 --- Geospatial Safety Layer

Goal:

-   maritime datasets,
-   coordinate handling,
-   distance,
-   boundary/restricted-zone checks.

Completion:

> ORCA can deterministically determine whether candidate locations
> violate configured geospatial constraints.

------------------------------------------------------------------------

## Phase 3 --- Specialist Agents

Goal:

-   Ocean Agent,
-   Weather Agent,
-   Maritime Agent,
-   structured outputs.

Completion:

> Each specialist independently provides useful, testable evidence.

------------------------------------------------------------------------

## Phase 4 --- Evidence & Reliability

Goal:

-   freshness,
-   source validation,
-   failure handling,
-   conflict detection,
-   confidence.

Completion:

> ORCA can recognize when evidence is incomplete, stale, unavailable, or
> conflicting.

------------------------------------------------------------------------

## Phase 5 --- Commander & Orchestration

Goal:

-   natural-language intent,
-   structured mission,
-   ACP communication,
-   multi-agent orchestration.

Completion:

> A single user request triggers a real multi-agent workflow.

------------------------------------------------------------------------

## Phase 6 --- Decision Engine

Goal:

-   candidate generation,
-   scoring,
-   risk adjustment,
-   explanation.

Completion:

> ORCA can produce a traceable risk-adjusted recommendation.

------------------------------------------------------------------------

## Phase 7 --- ASI:One Integration

Goal:

-   discoverability,
-   ASI:One interaction,
-   primary workflow,
-   Fetch-native experience.

Completion:

> A user can complete the core ORCA workflow inside ASI:One.

------------------------------------------------------------------------

## Phase 8 --- What-If + Interactive Experience

Goal:

-   what-if recomputation,
-   Interactive Cards if practical,
-   clearer evidence presentation.

Completion:

> A user can modify constraints and see the decision genuinely
> recomputed.

------------------------------------------------------------------------

## Phase 9 --- Hardening & Demo

Goal:

-   failure recovery,
-   security,
-   reproducibility,
-   GitHub instructions,
-   demo reliability.

Completion:

> ORCA can be demonstrated repeatedly without manual intervention or
> hidden steps.

------------------------------------------------------------------------

# 24. Completion Definition

ORCA V1 is complete when a judge can enter a request such as:

> "I want to go fishing tomorrow morning from Chennai. Find the best
> fishing zone within 30 km, keep the sea risk low, and avoid restricted
> areas."

and ORCA can:

1.  Understand the request.
2.  Create a structured mission.
3.  Orchestrate multiple specialist agents.
4.  Retrieve real marine/weather evidence.
5.  Check geospatial constraints deterministically.
6.  Validate evidence freshness.
7.  Detect failures/conflicts.
8.  Rank candidates using risk-adjusted logic.
9.  Explain the recommendation.
10. Show evidence and confidence.
11. Respond to a what-if request by recomputing the decision.
12. Complete the primary experience through ASI:One.
13. Use Agentverse and ACP correctly.
14. Run from a reproducible public repository.

That is the real definition of done.

------------------------------------------------------------------------

# 25. Repository Philosophy

The codebase should make the architecture obvious.

Suggested structure:

``` text
orca/
├── agents/
│   ├── commander/
│   ├── ocean/
│   ├── weather/
│   ├── maritime/
│   └── evidence/
│
├── orchestration/
│
├── data_sources/
│   ├── incois/
│   └── imd/
│
├── geospatial/
│
├── decision/
│
├── models/
│
├── tests/
│
├── config/
│
├── docs/
│
├── .env.example
├── README.md
└── ...
```

This is a starting structure, not a locked requirement.

Change it when implementation proves a better structure.

------------------------------------------------------------------------

# 26. Environment Configuration

All external configuration should be environment-driven.

Examples:

``` text
INCOIS_*
IMD_*
ASI1_*
DATABASE_URL
AGENTVERSE_*
ACP_*
```

Do not hard-code credentials.

Provide `.env.example`.

------------------------------------------------------------------------

# 27. Observability

The system should expose enough logs to understand:

``` text
Request
→ Agent
→ Tool/API
→ Result
→ Evidence
→ Decision
```

Each workflow should have a request/trace ID.

This is particularly important for debugging multi-agent failures.

------------------------------------------------------------------------

# 28. Documentation Rule

When code behavior changes, documentation must change.

When architecture changes:

-   update architecture docs,
-   update `ORCA_Phases.md`,
-   update relevant constraints if necessary.

When an API changes:

-   update data-source documentation,
-   update environment requirements,
-   update tests.

Documentation is part of implementation, not a final-day task.

------------------------------------------------------------------------

# 29. Business / Product Awareness

Even though ORCA is being built for a hackathon, implementation should
preserve a potential business.

The product is not:

> "An AI demo that analyzes ocean data."

The potential product is:

> **A decision-intelligence layer for people and organizations operating
> on the ocean.**

Potential users can eventually include:

-   fishermen,
-   fishing cooperatives,
-   coastal operators,
-   marine logistics,
-   aquaculture operators,
-   coastal safety teams,
-   research organizations,
-   marine insurers,
-   other ocean-economy businesses.

Do not build all of these in V1.

The hackathon MVP should prove the underlying decision engine.

------------------------------------------------------------------------

# 30. USP

ORCA's strongest differentiator is:

> **It does not merely tell you what the ocean data says. It reasons
> across opportunity, safety, constraints and confidence to tell you
> what decision makes sense.**

The strongest product loop is:

``` text
Intent
 ↓
Live/operational evidence
 ↓
Multiple specialist opinions
 ↓
Conflict detection
 ↓
Risk-adjusted reasoning
 ↓
Decision
 ↓
“What if?”
 ↓
Recomputed decision
```

That is the product.

------------------------------------------------------------------------

# 31. Business Positioning

### Category

Marine Decision Intelligence

### Product

ORCA

### Promise

> Turn fragmented marine intelligence into an actionable,
> evidence-backed decision.

### Differentiator

Traditional systems expose:

``` text
Data
Maps
Warnings
Forecasts
```

ORCA combines them into:

``` text
Decision
Reason
Risk
Confidence
Alternative
```

### Long-term business direction

The core technology can eventually become a decision layer/API for
ocean-economy applications.

Potential monetization directions:

-   professional marine intelligence subscriptions,
-   cooperative/fleet plans,
-   API access,
-   enterprise integrations,
-   risk intelligence,
-   specialized vertical modules.

These are future directions, not V1 requirements.

------------------------------------------------------------------------

# 32. Business Rule

Never let the business vision distort the hackathon MVP.

Do not build:

``` text
billing
subscription management
enterprise dashboard
CRM
fleet management
```

just to make ORCA look like a company.

Instead:

> Build a technically impressive decision engine that has a believable
> path to becoming a product.

------------------------------------------------------------------------

# 33. Hackathon Winning Logic

ORCA should demonstrate four things clearly:

### 1. Real problem

Marine operators face fragmented information.

### 2. Real agentic workflow

Multiple specialized agents collaborate.

### 3. Real Fetch integration

Agentverse + ACP + ASI:One are genuinely used.

### 4. Real decision value

The output is better than any single data source.

The judge should understand:

> "I could not get this decision by asking one API or one normal
> chatbot."

That is the desired reaction.

------------------------------------------------------------------------

# 34. Anti-Pattern Checklist

Before accepting a feature, ask:

### Does it make ORCA more like a dashboard?

If yes → probably reject.

### Does it make ORCA more like a generic chatbot?

If yes → reject.

### Does it add an agent without a unique capability?

If yes → reject.

### Does it move deterministic computation into the LLM?

If yes → reject.

### Does it hide missing data?

If yes → reject.

### Does it make ASI:One less important?

If yes → reject.

### Does it add infrastructure without product value?

If yes → reject.

### Does it improve the core decision?

If no → defer.

------------------------------------------------------------------------

# 35. Agent Operating Principle

The coding agent working on ORCA should behave as:

> **An implementation engineer following a product contract --- not an
> autonomous product manager inventing features.**

Before adding something, verify the documents.

When uncertain:

-   inspect the current phase,
-   inspect constraints,
-   inspect the core idea,
-   then make the smallest justified change.

------------------------------------------------------------------------

# 36. Final Rule

Do not try to make ORCA impressive by making it large.

Make ORCA impressive by making it:

-   correct,
-   reliable,
-   explainable,
-   agentic,
-   Fetch-native,
-   data-driven,
-   risk-aware,
-   and genuinely useful.

The final system should feel simple to the user:

> **"I ask ORCA a question. It figures out what matters, checks the
> ocean, checks the risk, checks the constraints, and gives me the best
> decision it can justify."**

That is what we are building.
