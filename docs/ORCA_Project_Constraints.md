# ORCA --- Project Constraints & Build Rules

**Project:** ORCA --- Ocean Reasoning & Coordination Agent\
**Hackathon:** Fetch-A-Thon 3.0 --- ASI:One Agent Challenge\
**Status:** LOCKED --- implementation guardrails

> **Core principle:** Data is fragmented. ORCA turns it into a decision.
>
> **Tagline:** "Don't read the ocean. Ask it."

------------------------------------------------------------------------

## 1. Purpose of This Document

This document is the **constraint layer for the ORCA build**.

It defines:

-   what we must build,
-   what we must not build,
-   how ORCA should behave,
-   how agents should interact,
-   how ASI:One must fit into the architecture,
-   what counts as a valid ORCA decision,
-   what to do when data is missing, stale, conflicting, or unsafe,
-   and which implementation shortcuts are explicitly forbidden.

These rules should be treated as **engineering constraints**, not
optional suggestions.

If a new feature conflicts with this document, **do not silently add
it**. Re-evaluate the scope first.

------------------------------------------------------------------------

# 2. ORCA's Core Identity

ORCA is **not** a marine chatbot.

ORCA is **not** a dashboard for displaying ocean data.

ORCA is **not** a generic RAG system over marine PDFs.

ORCA is a **marine decision-support agent**.

Its job is to transform a user's natural-language intent into an
evidence-backed, risk-aware recommendation using multiple specialized
agents and real data.

### The core question ORCA should answer

> **"Given what I want to do, where I want to do it, when I want to do
> it, and my constraints --- what is the best available decision?"**

For fishing, that becomes:

> **"Where is the best risk-adjusted fishing opportunity for me, at this
> time, within my constraints?"**

The word **risk-adjusted** is fundamental.

The system must never optimize fishing opportunity alone.

------------------------------------------------------------------------

# 3. Fetch-A-Thon Rules We Must Follow

The official Fetch-A-Thon 3.0 challenge requires the project to solve a
real-world problem, perform multi-step planning/reasoning/orchestration,
use tools/APIs/data/agents, register an agent on Agentverse, implement
ACP, be discoverable through ASI:One, and allow the primary workflow to
run entirely inside an ASI:One conversation.

These are **hard requirements** for ORCA.

## Mandatory Fetch requirements

### 3.1 Agentverse

At least one ORCA agent must be:

-   registered on Agentverse,
-   discoverable,
-   usable,
-   correctly described,
-   and demonstrable.

Specialist agents should be exposed through the architecture where
practical.

### 3.2 Agent Chat Protocol (ACP)

ORCA must use the required chat protocol correctly.

Do not create an arbitrary private communication format and call it ACP.

Messages between agents should have:

-   clear intent,
-   structured inputs,
-   structured outputs,
-   acknowledgement/error handling where required,
-   traceability.

### 3.3 ASI:One

ASI:One is not just a marketing badge.

It must be part of the actual user experience and orchestration path.

The primary workflow must be demonstrable directly inside an ASI:One
conversation.

**No custom frontend is required for the primary workflow.**

### 3.4 ASI1 / ASI:One must be meaningful

The hackathon specifically evaluates whether ASI1/ASI:One is used as a
core part of:

-   intent understanding,
-   reasoning,
-   decision-making,
-   orchestration,
-   or agent discovery.

Therefore:

**Do not build ORCA as a normal Python application and place ASI:One in
front of it only as a thin wrapper.**

ASI:One should meaningfully participate in understanding the user's
request and routing the work to ORCA.

### 3.5 Multi-agent orchestration must be real

Do not create multiple agents that merely repeat the same LLM prompt.

Each ORCA agent must own a distinct responsibility.

The collaboration must change the final decision.

------------------------------------------------------------------------

# 4. ORCA Architecture --- Locked

The conceptual architecture is:

``` text
USER
  ↓
ASI:One
  ↓
ORCA Commander / Entry Agent
  ↓
Intent → Structured Mission
  ↓
ACP
  ├── Ocean Intelligence Agent
  ├── Weather & Marine Forecast Agent
  ├── Maritime Safety Agent
  └── Evidence & Reliability Agent
  ↓
ORCA Reasoner
  ↓
Risk-Adjusted Decision
  ↓
Evidence + Confidence + Explanation
  ↓
ASI:One Response / Interactive Card
```

This is the default architecture.

Do not introduce additional agents simply to make the architecture look
more sophisticated.

------------------------------------------------------------------------

# 5. Agent Responsibility Rules

Every agent must have a **clear ownership boundary**.

## 5.1 ORCA Commander

Responsible for:

-   understanding the user's request,
-   creating structured intent,
-   identifying missing information,
-   deciding which specialist agents are required,
-   orchestrating the workflow,
-   collecting responses,
-   invoking reconciliation,
-   passing validated information to the reasoner,
-   returning the final result.

The Commander should **coordinate**, not pretend to know every domain.

### Commander must NOT:

-   invent ocean measurements,
-   invent weather conditions,
-   perform legal boundary interpretation through an LLM,
-   fabricate missing API results,
-   override specialist evidence without justification.

------------------------------------------------------------------------

# 6. Ocean Intelligence Agent

Owns **marine opportunity intelligence**.

Possible inputs:

-   Potential Fishing Zone (PFZ) information,
-   SST,
-   chlorophyll,
-   ocean productivity indicators,
-   currents,
-   other operational ocean observations.

Primary output should contain structured evidence such as:

``` json
{
  "candidate_zone": {
    "lat": 13.05,
    "lon": 80.55
  },
  "fishing_potential": 0.82,
  "observations": {
    "sst": "...",
    "chlorophyll": "..."
  },
  "source": "INCOIS",
  "observed_at": "...",
  "confidence": 0.86
}
```

### Rule

The Ocean Agent provides **opportunity evidence**.

It does not declare a location universally safe.

------------------------------------------------------------------------

# 7. Weather & Marine Forecast Agent

Owns **environmental operating risk**.

Possible signals:

-   significant wave height,
-   swell,
-   wind,
-   wave period,
-   currents,
-   SST,
-   coastal forecasts,
-   fishermen warnings,
-   sea-area bulletins,
-   cyclone information,
-   high-wave/swell alerts.

### Rule

Weather risk must be treated as an independent decision dimension.

A high fishing-potential zone can still be rejected.

Example:

``` text
Ocean Agent:
Fishing potential = HIGH

Weather Agent:
Wave risk = HIGH

ORCA:
Do NOT recommend the zone as the best option.
```

This disagreement is expected behavior.

------------------------------------------------------------------------

# 8. Maritime Safety Agent

Owns **geospatial constraints**.

It should evaluate:

-   maritime boundaries,
-   territorial-water geometry,
-   EEZ-related constraints,
-   protected/restricted zones,
-   route proximity,
-   candidate-zone intersections,
-   geofencing constraints.

Use deterministic geospatial computation wherever possible.

Recommended tools include:

-   PostGIS,
-   GeoPandas,
-   Shapely.

### Critical rule

Do not use an LLM to decide whether two coordinates are inside a
polygon.

Use actual geometry.

The LLM can explain the result.

It should not calculate the geometry.

### Legal disclaimer

ORCA is a decision-support prototype.

It is **not**:

-   a legal authority,
-   certified navigation software,
-   an autonomous navigation system,
-   an official maritime boundary authority,
-   or a replacement for government advisories.

------------------------------------------------------------------------

# 9. Evidence & Reliability Agent

This agent is one of ORCA's most important differentiators.

It owns:

-   source validation,
-   timestamp validation,
-   freshness,
-   missing data,
-   geographic coverage,
-   conflicting observations,
-   failed API detection,
-   evidence consistency,
-   confidence calculation.

Every important observation should ideally carry:

``` text
source
timestamp
data_age
geographic_coverage
confidence
```

## Reliability rule

**Missing data is not permission to hallucinate.**

If a critical source fails:

``` text
DO NOT:
“Conditions appear safe.”

DO:
“I cannot reliably assess sea risk because the required marine forecast data is unavailable.”
```

If two sources conflict:

``` text
DO NOT:
silently choose whichever supports the answer.

DO:
flag the disagreement and reduce confidence.
```

------------------------------------------------------------------------

# 10. The Decision Engine

ORCA's final decision should be based on multiple dimensions.

Conceptually:

``` text
Decision Quality
    =
Fishing Opportunity
×
Safety
×
Accessibility
×
Data Confidence
```

The exact weights are an implementation/calibration decision.

The principle is locked:

> **ORCA must optimize for risk-adjusted opportunity, not maximum
> opportunity.**

A zone with:

``` text
Fishing = 95
Safety = 30
Confidence = 90
```

should not automatically beat:

``` text
Fishing = 82
Safety = 88
Confidence = 94
```

The system should be able to explain why.

------------------------------------------------------------------------

# 11. Deterministic vs LLM Responsibilities

This is a critical engineering rule.

## Use deterministic code for:

-   distance calculations,
-   coordinate validation,
-   polygon intersection,
-   boundary checks,
-   timestamps,
-   freshness calculations,
-   numerical normalization,
-   candidate ranking,
-   threshold checks,
-   confidence calculations,
-   API response validation.

## Use ASI1 / LLM reasoning for:

-   natural-language intent understanding,
-   converting user intent into structured mission parameters,
-   deciding which capabilities are needed,
-   interpreting evidence,
-   resolving semantic ambiguity,
-   explaining trade-offs,
-   generating the final human-readable recommendation,
-   handling natural-language follow-up questions.

### Never do this

``` text
LLM:
“13.05, 80.55 is approximately 27 km away and outside the boundary.”
```

if the system can calculate it directly.

### Do this

``` text
Python/PostGIS:
distance = 26.7 km
polygon_intersection = false

LLM:
“Based on the verified geometry, this zone is 26.7 km away and does not intersect the configured restricted area.”
```

------------------------------------------------------------------------

# 12. What ORCA Must NOT Build

These are explicit scope exclusions.

## 12.1 No custom dashboard for V1

Do not spend hackathon time building:

-   maps dashboard,
-   analytics dashboard,
-   admin dashboard,
-   fancy React frontend,
-   separate mobile application.

The primary experience belongs inside ASI:One.

A small technical/debug UI is acceptable only if needed for development.

------------------------------------------------------------------------

## 12.2 No generic chatbot

Do not build:

> "Ask me anything about the ocean."

That destroys ORCA's product identity.

ORCA should be focused on **decisions and actions**, not general
conversation.

------------------------------------------------------------------------

## 12.3 No PDF chatbot

Do not turn ORCA into:

> "Upload a marine PDF and ask questions."

Documents can be evidence sources, but document Q&A is not the core
product.

------------------------------------------------------------------------

## 12.4 No raw-data dashboard

Do not simply expose:

-   SST maps,
-   chlorophyll maps,
-   wave charts,
-   satellite images,
-   weather feeds.

Displaying data is not the USP.

ORCA must **interpret and combine** the data into a decision.

------------------------------------------------------------------------

## 12.5 No fake multi-agent architecture

Do not create:

``` text
Agent 1 → asks Agent 2
Agent 2 → asks Agent 3
Agent 3 → repeats Agent 1
```

just for the sake of saying "multi-agent."

Every agent must contribute unique evidence or capability.

------------------------------------------------------------------------

## 12.6 No unnecessary agent explosion

Do not create:

-   12 agents,
-   20 agents,
-   separate agents for every API,
-   separate agents for every calculation.

More agents ≠ better architecture.

The current five-agent conceptual architecture is sufficient.

------------------------------------------------------------------------

## 12.7 No autonomous vessel control

ORCA must not:

-   control boats,
-   control engines,
-   control navigation systems,
-   issue autonomous route commands,
-   operate as an autopilot.

This is decision support.

------------------------------------------------------------------------

## 12.8 No fabricated official authority

Never claim:

-   "ISRO recommends this location."
-   "IMD guarantees this is safe."
-   "Government-approved fishing zone."
-   "Official legal maritime clearance."

ORCA may use government/official data sources, but its recommendation is
its own computed decision-support output.

------------------------------------------------------------------------

## 12.9 No pretending stale data is live

If data is:

-   stale,
-   cached,
-   unavailable,
-   outside geographic coverage,
-   partially missing,

ORCA must say so.

Never label old data as:

> "Current conditions."

------------------------------------------------------------------------

## 12.10 No overengineering the MVP

Do not add:

-   blockchain,
-   unnecessary vector databases,
-   Kubernetes,
-   microservices for every component,
-   complex event buses,
-   unnecessary Redis,
-   custom model training,
-   fine-tuning,
-   complicated frontend infrastructure.

Unless a feature directly improves the ORCA decision workflow, it should
be questioned.

------------------------------------------------------------------------

# 13. Data Source Rules

Primary sources should be operational and credible.

### Primary

-   INCOIS
-   IMD

### Secondary / optional

-   MOSDAC / ISRO
-   Marine Regions
-   other credible marine datasets where required

## Important rule

Do not make a fragile raw satellite-data pipeline the hard dependency
for the MVP if an operational product already provides the required
information.

For example:

> Use operational INCOIS PFZ information for fishing-zone intelligence
> instead of requiring ORCA to independently process raw satellite
> imagery.

Raw satellite processing can be a future enhancement.

------------------------------------------------------------------------

# 14. Data Freshness Rules

Every source should ideally expose:

``` text
source
retrieved_at
observed_at
forecast_valid_from
forecast_valid_to
age
```

ORCA should distinguish:

-   observation time,
-   forecast generation time,
-   forecast validity time,
-   retrieval time.

These are not interchangeable.

------------------------------------------------------------------------

# 15. Failure Behavior

Failure handling is part of ORCA's intelligence.

## API timeout

Do not fabricate.

Return:

``` text
Weather service unavailable.
Safety confidence cannot be established.
Recommendation withheld or downgraded.
```

## Partial failure

If Ocean Agent works but Weather Agent fails:

``` text
Fishing opportunity can be assessed.
Marine safety cannot be reliably assessed.
Final recommendation should be withheld or explicitly marked incomplete.
```

## Conflicting sources

Return:

``` text
Source disagreement detected.
Confidence reduced.
Reason for disagreement shown.
```

## No suitable zone

Do not force a recommendation.

Say:

> "No candidate currently satisfies your constraints."

This is a valid successful outcome.

------------------------------------------------------------------------

# 16. ORCA Must Explain Its Decisions

Every recommendation should answer:

### 1. What?

What location/time/action is recommended?

### 2. Why?

What evidence caused ORCA to choose it?

### 3. Why not the alternatives?

What caused other candidates to rank lower?

### 4. Risk?

What could make the recommendation unsafe or less attractive?

### 5. Confidence?

How reliable is the recommendation?

### 6. Data freshness?

How recent is the underlying evidence?

------------------------------------------------------------------------

# 17. Evidence-First Response Format

A strong ORCA response should conceptually look like:

``` text
RECOMMENDATION
Zone A — 26.7 km from origin

WHY
• High fishing potential
• Low wave risk
• No configured restricted-zone intersection
• Data confidence: 91%

TRADE-OFF
Zone B has slightly higher fishing potential,
but significantly higher wave risk.

DATA
Ocean: INCOIS — [timestamp]
Marine forecast: INCOIS — [timestamp]
Weather warning: IMD — [timestamp]
Geospatial layer: [dataset/version]

CONFIDENCE
High

IMPORTANT
Decision support only. Check official marine advisories
before departure.
```

The exact UI can evolve, but the information hierarchy should remain.

------------------------------------------------------------------------

# 18. What-If Simulation --- Signature Feature

ORCA should support follow-up changes such as:

> "What if I go 15 km farther?"

> "What if I leave at 5 AM instead?"

> "What if I want lower wave risk?"

> "What if I prioritize fishing potential over distance?"

ORCA must **recompute the decision**.

It should not merely generate a different paragraph.

### Required behavior

``` text
Original mission
       ↓
Change one constraint
       ↓
Re-run affected analysis
       ↓
Re-rank candidates
       ↓
Return changed recommendation
```

This demonstrates genuine agentic reasoning.

------------------------------------------------------------------------

# 19. Natural Language Intent → Structured Mission

The system should convert a request such as:

> "I want to go fishing tomorrow morning from Chennai. Find a good
> fishing zone within 30 km but keep the sea risk low."

into something similar to:

``` json
{
  "activity": "fishing",
  "origin": {
    "lat": "...",
    "lon": "..."
  },
  "time_window": {
    "start": "...",
    "end": "..."
  },
  "max_distance_km": 30,
  "objective": "high_fishing_potential",
  "constraints": [
    "low_weather_risk",
    "avoid_restricted_zones",
    "avoid_boundary_proximity"
  ]
}
```

The structured mission becomes the contract between orchestration and
specialist agents.

------------------------------------------------------------------------

# 20. Clarification Rules

ORCA should not ask unnecessary questions.

If the request contains enough information to produce a useful answer,
proceed.

If a missing parameter materially changes the result, ask.

Examples:

### Good clarification

> "What is your starting location?"

when location is essential and cannot be resolved.

### Bad clarification

Asking five questions before doing anything when reasonable defaults
could be used.

### Principle

> **Minimize user friction without inventing critical information.**

------------------------------------------------------------------------

# 21. Safety Hierarchy

When dimensions conflict, safety should dominate opportunity.

Conceptually:

``` text
Critical Safety Failure
        ↓
Reject Candidate

High Risk
        ↓
Strong penalty / warning

Moderate Risk
        ↓
Possible recommendation with warning

Low Risk
        ↓
Normal ranking
```

A high fishing score must never override a critical safety constraint.

------------------------------------------------------------------------

# 22. Maritime Boundary Behavior

Boundary-related information must be treated carefully.

ORCA should distinguish:

-   geometric proximity,
-   configured restricted zones,
-   dataset-derived maritime boundaries,
-   legal interpretation.

Never imply that a prototype geospatial dataset constitutes legal
maritime clearance.

The UI/response should communicate this clearly.

------------------------------------------------------------------------

# 23. Confidence Is Not a Feeling

Confidence must not simply be:

``` text
LLM says confidence = 92%
```

Confidence should be derived from measurable evidence such as:

-   source availability,
-   freshness,
-   completeness,
-   agreement,
-   geographic coverage,
-   forecast validity,
-   data quality.

The LLM can **explain** confidence.

It should not arbitrarily invent the confidence number.

------------------------------------------------------------------------

# 24. Agent Communication Contract

Every specialist response should be structured enough for the Commander
to consume.

Conceptually:

``` json
{
  "agent": "weather",
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

Do not pass unstructured prose between agents when a structured contract
is possible.

------------------------------------------------------------------------

# 25. Logging & Traceability

Every important ORCA decision should be traceable.

At minimum log:

``` text
request_id
user_intent
structured_mission
agents_called
tool_calls
source timestamps
agent responses
candidate zones
decision factors
final recommendation
confidence
failure/warning events
```

This is important for:

-   debugging,
-   demo credibility,
-   reliability,
-   judging,
-   future productionization.

Do not log secrets or sensitive credentials.

------------------------------------------------------------------------

# 26. Secrets & API Security

Never commit:

``` text
API keys
tokens
passwords
private keys
Agentverse credentials
```

to GitHub.

Use:

``` text
.env
environment variables
secret managers
```

and provide:

``` text
.env.example
```

with placeholder values.

------------------------------------------------------------------------

# 27. ASI:One UX Rules

The ASI:One conversation should feel like the natural home of ORCA.

The user should not need to understand:

-   Agentverse,
-   ACP,
-   APIs,
-   agent addresses,
-   internal architecture.

The user should simply be able to say:

> "Find me the best fishing area tomorrow morning within 30 km, but keep
> the sea conditions safe."

ORCA handles the complexity.

------------------------------------------------------------------------

# 28. Interactive Cards

If time permits, use ASI Interactive Cards for:

-   mission confirmation,
-   top candidate zones,
-   comparison,
-   evidence,
-   what-if controls,
-   confidence,
-   warnings.

Cards should reduce cognitive load.

Do not build cards merely for visual decoration.

------------------------------------------------------------------------

# 29. Demo Rules

The demo must show **real execution**.

Do not demo:

``` text
User → LLM → pretty paragraph
```

Demo:

``` text
User
 ↓
ASI:One
 ↓
ORCA Commander
 ↓
ACP
 ↓
Ocean Agent
Weather Agent
Maritime Agent
Evidence Agent
 ↓
Decision Engine
 ↓
Recommendation
```

Then perform the signature follow-up:

> "What if I go 15 km farther?"

and show that the system actually recomputes.

------------------------------------------------------------------------

# 30. The Golden Demo Scenario

Use one strong scenario and make it reliable.

Example:

> "I want to go fishing tomorrow morning from Chennai. Find the best
> fishing zone within 30 km, avoid high sea risk, and keep me away from
> restricted areas."

Then show:

1.  Intent extraction.
2.  Agent orchestration.
3.  Live/operational marine data retrieval.
4.  Weather analysis.
5.  Maritime geometry check.
6.  Evidence reconciliation.
7.  Candidate ranking.
8.  Final recommendation.
9.  Evidence + confidence.
10. What-if change.
11. Recomputed recommendation.

The demo should be understandable even to a judge who knows nothing
about marine science.

------------------------------------------------------------------------

# 31. Product Behavior Rules

ORCA should behave like:

### A decision-maker

Not merely an information retriever.

### A coordinator

Not a monolithic model.

### Evidence-first

Not hallucination-first.

### Risk-aware

Not opportunity-maximizing.

### Honest about uncertainty

Not artificially confident.

### Action-oriented

Not dashboard-oriented.

### Explainable

Not black-box.

### Minimal

Not feature-heavy.

------------------------------------------------------------------------

# 32. "Do Not Fake Intelligence" Rule

Never manufacture complexity.

If a deterministic function can solve something better:

**use the deterministic function.**

If an API provides the authoritative data:

**use the API.**

If an agent has no meaningful role:

**do not create the agent.**

If the system cannot determine something reliably:

**say that it cannot determine it.**

This is a core ORCA engineering principle.

------------------------------------------------------------------------

# 33. "No Silent Failure" Rule

Never allow a failed component to silently produce a normal-looking
answer.

Bad:

``` text
Weather API failed
↓
LLM guesses weather
↓
“Low risk”
```

Good:

``` text
Weather API failed
↓
Evidence Agent detects failure
↓
Confidence reduced / recommendation withheld
↓
User informed
```

------------------------------------------------------------------------

# 34. "No Silent Override" Rule

No single agent should silently override another specialist.

If:

``` text
Ocean Agent → HIGH opportunity
Weather Agent → HIGH risk
Maritime Agent → SAFE
```

the Commander/Reasoner must explicitly reconcile the conflict.

The disagreement itself is valuable evidence.

------------------------------------------------------------------------

# 35. Scope Priority

When development time becomes limited, prioritize in this order:

### P0 --- Must work

-   ASI:One interaction
-   Agentverse deployment
-   ACP
-   Commander
-   Ocean Agent
-   Weather Agent
-   Maritime Safety Agent
-   Evidence/Reliability
-   real data
-   deterministic decision engine
-   final recommendation

### P1 --- Strong differentiators

-   What-if simulation
-   Interactive Cards
-   detailed evidence trace
-   multilingual natural language

### P2 --- Optional

-   Payment Protocol
-   advanced satellite processing
-   additional marine datasets
-   voice
-   historical analytics
-   long-term personalization

### P3 --- Do not build for hackathon MVP

-   custom dashboard
-   mobile app
-   autonomous vessel control
-   full navigation system
-   complex enterprise platform

------------------------------------------------------------------------

# 36. Definition of Done

ORCA is not "done" because the agents run.

The MVP is done when:

-   [ ] Agent is registered on Agentverse.
-   [ ] Agent is discoverable through ASI:One.
-   [ ] ACP works correctly.
-   [ ] User can start from natural language.
-   [ ] Intent becomes structured mission data.
-   [ ] Commander orchestrates multiple specialists.
-   [ ] Ocean data is retrieved.
-   [ ] Weather/marine data is retrieved.
-   [ ] Maritime constraints are checked deterministically.
-   [ ] Evidence freshness is checked.
-   [ ] Failures are handled.
-   [ ] Candidates are ranked using risk-adjusted logic.
-   [ ] Final answer includes evidence and confidence.
-   [ ] The primary workflow completes inside ASI:One.
-   [ ] What-if simulation works, if included in the committed MVP.
-   [ ] GitHub contains reproducible run/test instructions.
-   [ ] No secrets are committed.
-   [ ] Demo can be repeated reliably.

------------------------------------------------------------------------

# 37. Final Non-Negotiable Rules

These are the rules to remember during implementation:

1.  **ORCA is a decision engine, not a chatbot.**
2.  **ASI:One is part of the product, not decoration.**
3.  **Agentverse + ACP must be real, not claimed.**
4.  **Every agent must have a meaningful responsibility.**
5.  **Use deterministic code for deterministic facts.**
6.  **Use LLM reasoning for interpretation and orchestration.**
7.  **Never hallucinate missing marine or weather data.**
8.  **Never silently ignore conflicting evidence.**
9.  **Safety outranks fishing opportunity.**
10. **Confidence must be evidence-derived.**
11. **Every important recommendation should be explainable.**
12. **The primary workflow must work inside ASI:One.**
13. **Do not build a custom frontend unless it directly supports
    development/testing.**
14. **Do not add features that dilute the core use case.**
15. **What-if changes must trigger actual recomputation.**
16. **No agent exists merely to increase the agent count.**
17. **No source should be represented as an official recommendation
    unless it actually is one.**
18. **If ORCA cannot reliably decide, ORCA must say so.**
19. **The system should be simpler internally than it appears
    externally.**
20. **Build the smallest system that demonstrates genuine agentic
    intelligence.**

------------------------------------------------------------------------

# 38. The ORCA North Star

Every engineering decision should be tested against one question:

> **Does this help ORCA turn a user's marine intent into a safer,
> evidence-backed, risk-adjusted decision?**

If **yes**, consider it.

If **no**, defer it.

If it makes the architecture more complex without improving the
decision, **do not build it.**

------------------------------------------------------------------------

## Fetch-A-Thon Compliance Reference

The current Fetch-A-Thon 3.0 hackpack states that the challenge requires
an agent that solves a real-world problem, performs multi-step
reasoning/orchestration, uses tools/APIs/data/agents, is registered on
Agentverse, implements ACP, is discoverable through ASI:One, and can
complete the primary workflow inside an ASI:One conversation. The
hackpack also identifies Interactive Cards, Payment Protocol,
reliability/error recovery, real-time data, and post-hackathon viability
as bonus opportunities.

Official reference:

https://www.fetch.ai/events/hackathons/fetch-a-thon-3/hackpack
