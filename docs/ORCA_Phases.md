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

**Current Phase:** Phase 0 --- Project Foundation\
**Status:** NOT STARTED

## Overall Progress

``` text
Phase 0  Foundation              [ ] 
Phase 1  Marine Data Layer       [ ]
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

**Status:** NOT STARTED

## Goal

Create a clean, reproducible backend project.

## Planned

-   repository structure
-   Python environment
-   configuration
-   `.env.example`
-   logging
-   basic models
-   test framework
-   initial README
-   documentation structure

## Completion

Phase 0 is complete when:

-   project runs locally,
-   tests execute,
-   configuration works,
-   secrets are externalized,
-   repository structure is stable enough for Phase 1.

## Implemented

*None yet.*

## Files Changed

*None yet.*

## Tests

*None yet.*

## Decisions

*None yet.*

## Problems / Blockers

*None yet.*

## Changes From Plan

*None yet.*

## Next Phase

Phase 1 --- Marine Data Layer

------------------------------------------------------------------------

# Phase 1 --- Marine Data Layer

**Status:** NOT STARTED

## Goal

Build reliable access to operational marine and weather data.

## Planned

-   INCOIS integration
-   IMD integration
-   normalized source models
-   timestamps
-   source metadata
-   error handling
-   data validation

## Completion

ORCA can retrieve real marine/weather evidence and normalize it into
internal models.

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
