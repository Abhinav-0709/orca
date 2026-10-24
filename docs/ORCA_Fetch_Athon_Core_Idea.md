# ORCA --- Ocean Reasoning & Coordination Agent

## Fetch-A-Thon 3.0 --- Core Product Specification

**Working name:** ORCA\
**Full name:** Ocean Reasoning & Coordination Agent\
**Category:** Multi-Agent Marine Intelligence / Decision Support\
**Primary interface:** ASI:One\
**Deployment/discovery:** Agentverse\
**Primary communication:** Agent Chat Protocol (ACP)\
**Core approach:** Backend-heavy, evidence-driven multi-agent system\
**Target geography for V1:** Indian coastline

------------------------------------------------------------------------

# 1. Executive Idea

## ORCA turns fragmented ocean information into a single, evidence-based marine decision.

People operating small fishing boats or working in coastal environments
should not need to understand satellite maps, oceanographic datasets,
weather bulletins, maritime GIS layers, or multiple government portals
just to answer:

> **"Where should I go, when should I go, and is it safe?"**

ORCA accepts a natural-language request through **ASI:One**, decomposes
the intent, discovers/calls specialized marine agents, gathers live or
recently issued ocean/weather/maritime information, cross-checks the
evidence, and produces a concise risk-aware recommendation.

### Core product promise

> **Don't read the ocean. Ask it.**

### Technical positioning

ORCA is **not a marine chatbot**.

It is a **multi-agent marine intelligence and decision-support system**
that performs:

**Intent → Data acquisition → Spatial reasoning → Cross-agent evidence
reconciliation → Risk assessment → Actionable recommendation**

------------------------------------------------------------------------

# 2. The Problem

Marine information already exists, but it is fragmented.

A fisherman or coastal operator may need to combine:

-   Potential Fishing Zone advisories
-   Sea Surface Temperature
-   Chlorophyll / ocean productivity indicators
-   Wave height
-   Wind
-   Swell
-   Currents
-   Tide information
-   Cyclone warnings
-   Fishermen warnings
-   Maritime boundaries
-   Restricted/protected marine zones

The problem is therefore not simply lack of data.

## The real problem is:

> **The data exists, but the decision layer is missing.**

Existing systems primarily expose individual datasets, maps, bulletins,
or advisories.

ORCA creates the reasoning layer above them.

------------------------------------------------------------------------

# 3. Why ORCA Is Different

A normal marine application might answer:

> "Here is today's fishing zone."

ORCA asks:

> "Given your starting location, intended departure time, desired
> fishing range, weather conditions, marine restrictions, and available
> ocean indicators, what is the best risk-adjusted option?"

This creates a fundamentally different product.

## ORCA does not optimize for fishing potential alone.

It optimizes for:

**Opportunity + Safety + Accessibility + Data Confidence**

A zone with high fishing potential can still be rejected because:

-   wave conditions are unsafe,
-   a cyclone warning intersects the route,
-   the route approaches a maritime boundary,
-   the area intersects a restricted zone,
-   the relevant data is stale or contradictory.

------------------------------------------------------------------------

# 4. Core User Workflow

Example request:

> "I want to go fishing tomorrow morning. Find the best zone within 30
> km that has high fishing potential and low weather risk."

ORCA should execute:

``` text
User Intent
    ↓
ASI:One
    ↓
ORCA Entry Agent
    ↓
Intent Structuring
    ↓
Candidate Zone Discovery
    ↓
┌──────────────────────────────────────────┐
│ Ocean Intelligence Agent                 │
│ Weather & Marine Forecast Agent          │
│ Maritime Safety Agent                    │
└──────────────────────────────────────────┘
    ↓
Evidence Collection
    ↓
Evidence Validation
    ↓
Risk / Opportunity Scoring
    ↓
Candidate Ranking
    ↓
ORCA Decision
    ↓
ASI:One Response / Interactive Card
```

------------------------------------------------------------------------

# 5. The Multi-Agent Architecture

## 5.1 ORCA Entry / Commander Agent

This is the primary Agentverse agent.

Responsibilities:

-   Understand the user's request
-   Convert natural language into structured intent
-   Determine which specialist capabilities are required
-   Coordinate specialist agents
-   collect their outputs
-   trigger evidence reconciliation
-   produce the final recommendation
-   communicate the result back through ASI:One

Example structured intent:

``` json
{
  "activity": "fishing",
  "origin": {
    "lat": 13.08,
    "lon": 80.27
  },
  "time_window": {
    "start": "2026-10-25T05:00:00+05:30",
    "end": "2026-10-25T10:00:00+05:30"
  },
  "max_distance_km": 30,
  "objective": "high fishing potential",
  "constraints": [
    "low weather risk",
    "avoid restricted zones",
    "avoid maritime boundary approach"
  ]
}
```

------------------------------------------------------------------------

# 6. Specialist Agent 1 --- Ocean Intelligence Agent

## Purpose

Determine marine/fishing opportunity using oceanographic information.

### Inputs

-   geographic area
-   time window
-   fishing intent
-   candidate search radius

### Data considered

-   Potential Fishing Zone advisories
-   Sea Surface Temperature
-   Chlorophyll
-   ocean productivity indicators
-   currents where available
-   wind-driven movement considerations

### Output

``` json
{
  "candidate_zones": [
    {
      "id": "ORCA-Z17",
      "latitude": 13.21,
      "longitude": 80.61,
      "fishing_potential": 0.84,
      "sst": 28.4,
      "chlorophyll": 3.2,
      "source": "INCOIS",
      "timestamp": "..."
    }
  ]
}
```

### Important implementation decision

For the hackathon MVP, **do not depend on raw MOSDAC satellite downloads
as the only live source**.

INCOIS already operationalizes Potential Fishing Zone information using
SST and chlorophyll-derived ocean features and exposes PFZ maps/text.
This gives ORCA a practical operational fishing-intelligence input
without requiring us to build a complete satellite-processing pipeline.

INCOIS states that its PFZ advisories use SST and chlorophyll
information from multiple satellite sources and provide
latitude/longitude, depth, distance/direction from coastal reference
points, and multilingual advisories.

Source: https://www.incois.gov.in/MarineFisheries/PfzAdvisory

------------------------------------------------------------------------

# 7. Specialist Agent 2 --- Weather & Marine Forecast Agent

## Purpose

Determine whether ocean/weather conditions make a candidate zone
suitable for the intended time.

### Inputs

-   candidate coordinates
-   departure time
-   expected operating window

### Data considered

-   significant wave height
-   swell
-   swell period
-   wind
-   surface currents
-   sea surface temperature
-   coastal forecast
-   fishermen warnings
-   sea-area bulletins
-   cyclone information
-   high-wave/swell alerts

### Primary sources

INCOIS Ocean State Forecast provides ocean forecasts including waves,
winds, currents, water temperature and other ocean variables, with
forecasts issued at 3-hour intervals for the next 5--10 days.

Source: https://www.incois.gov.in/oceanservices/osfforecast.jsp

India Meteorological Department also exposes marine APIs including:

-   Port Warning
-   Sea Area Bulletin
-   Coastal Bulletin
-   Fishermen Warning
-   Cyclone Track
-   Cyclone Wind Warning
-   Cyclone Cone of Uncertainty

Source: https://api.imd.gov.in/public/api_reference.html

### Output

``` json
{
  "weather_risk": 0.22,
  "wave_height_m": 1.3,
  "wind_speed": 8.2,
  "cyclone_warning": false,
  "fishermen_warning": false,
  "forecast_confidence": 0.91,
  "timestamp": "..."
}
```

------------------------------------------------------------------------

# 8. Specialist Agent 3 --- Maritime Safety Agent

## Purpose

Determine whether the candidate zone or route creates
geographic/legal/safety concerns.

### Checks

-   international maritime boundaries
-   territorial waters
-   EEZ boundaries
-   route proximity to boundaries
-   protected/restricted marine areas
-   geofencing
-   route intersection

### Data strategy

For the hackathon prototype, maritime boundary geometry can be
maintained as a geospatial dataset and queried locally using
PostGIS/GeoPandas/Shapely.

Marine Regions provides downloadable maritime-boundary datasets and WFS
services, including EEZ, territorial-sea and other maritime-zone
geometries.

Source: https://www.marineregions.org/downloads.php

WFS/API-style access: https://www.marineregions.org/webservices.php

### Output

``` json
{
  "boundary_distance_km": 12.4,
  "territorial_zone": false,
  "restricted_zone": false,
  "route_intersects_restricted_area": false,
  "navigation_risk": 0.06
}
```

### Important limitation

Boundary datasets should be presented as **decision-support geometry**,
not legal navigation certification. ORCA must not claim to replace
official navigation or maritime authorities.

------------------------------------------------------------------------

# 9. Specialist Agent 4 --- Evidence & Reliability Agent

This is a key ORCA differentiator.

The agent does not make the marine recommendation.

It checks whether the evidence used to make the recommendation is
trustworthy enough.

For every input:

``` json
{
  "source": "...",
  "observation": "...",
  "timestamp": "...",
  "age_minutes": 42,
  "confidence": 0.91
}
```

It checks:

-   source availability
-   timestamp freshness
-   conflicting observations
-   missing fields
-   stale forecasts
-   failed API calls
-   incompatible geographic coverage

### Example

If:

``` text
Ocean data: updated 30 min ago
Weather data: updated 2 hours ago
Marine warning: updated 7 hours ago
```

ORCA should not silently treat them as equally fresh.

It should say:

> "The recommendation has reduced confidence because the latest marine
> warning data is older than the other sources."

------------------------------------------------------------------------

# 10. ORCA Reasoning Layer

The reasoning layer combines structured outputs from all specialist
agents.

Example:

``` text
Zone A

Fishing Potential: 0.92
Weather Safety:    0.44
Maritime Safety:   0.96
Data Confidence:   0.90
```

versus:

``` text
Zone B

Fishing Potential: 0.81
Weather Safety:    0.88
Maritime Safety:   0.95
Data Confidence:   0.93
```

ORCA should prefer Zone B.

## Core principle

> **The highest-yield location is not necessarily the best decision.**

The scoring model should be deterministic/traceable where possible, with
the LLM assisting interpretation rather than inventing the measurement.

Example conceptual model:

``` text
Decision Score =
    Fishing Opportunity
  × Safety
  × Accessibility
  × Data Confidence
```

The exact weighting will be calibrated during implementation.

------------------------------------------------------------------------

# 11. Agent Disagreement Is a Feature

ORCA should explicitly support disagreement.

Example:

``` text
Ocean Agent:
High fishing potential.

Weather Agent:
Moderate-to-high wave risk.

Maritime Agent:
Route approaches boundary.

Evidence Agent:
All sources current.

ORCA:
REJECT CANDIDATE
```

The final response:

> "Zone C has high fishing potential, but I do not recommend it for the
> requested departure window because wave risk is elevated and the
> planned route approaches a maritime boundary."

This demonstrates genuine multi-agent reasoning rather than sequential
LLM summarization.

------------------------------------------------------------------------

# 12. The ORCA "What-If" Capability

This is a potential signature feature.

The user can modify a constraint after receiving a recommendation.

Example:

> "What if I go 15 km farther?"

ORCA recalculates:

``` text
Fishing potential      ↑
Travel distance        ↑
Fuel requirement       ↑
Wave exposure          ↑
Boundary proximity     ↓
Overall risk           ↑
```

Then:

> "Fishing potential may improve, but the additional route increases
> exposure to rougher sea conditions and reduces boundary clearance. The
> original zone remains the safer trade-off."

Another example:

> "What if I leave at 5 AM instead of 8 AM?"

ORCA re-evaluates the same candidate set against the new time window.

### USP

> **ORCA doesn't only answer marine questions. It evaluates the
> consequences of changing the decision.**

------------------------------------------------------------------------

# 13. Multilingual / Voice Interaction

The target user should not need technical marine terminology.

The intended experience is:

``` text
Voice / Natural Language
        ↓
ASI:One
        ↓
Intent extraction
        ↓
ORCA
        ↓
Marine reasoning
        ↓
Simple response
```

Supported MVP languages can begin with:

-   English
-   Hindi
-   Tamil
-   Bengali

The system should preserve the user's preferred language in the
response.

Important:

Multilingual support is a **delivery layer**, not the main intelligence
layer.

------------------------------------------------------------------------

# 14. Fetch.ai Integration

ORCA should be designed around the Fetch-A-Thon requirements from the
beginning.

## Fetch components

### Agentverse

Used for:

-   agent registration
-   agent discovery
-   agent deployment
-   public agent profiles

At least one ORCA agent must be registered on Agentverse.

### ACP

Used for agent interaction and ASI:One-compatible communication.

### ASI:One

Used as the primary user interface and intent/discovery layer.

The primary workflow should be demonstrable completely inside an ASI:One
conversation.

### ASI1

Should be a meaningful part of:

-   intent understanding
-   orchestration
-   reasoning/decision-making
-   final synthesis where appropriate

The deterministic data-processing agents should not force an LLM to
perform calculations that can be handled by normal code.

------------------------------------------------------------------------

# 15. Final Fetch-Native Architecture

``` text
                         USER
                           │
                           ▼
                       ASI:ONE
                           │
                    Intent / Discovery
                           │
                           ▼
                  ┌──────────────────┐
                  │  ORCA COMMANDER  │
                  │ Agentverse Agent │
                  └────────┬─────────┘
                           │
                          ACP
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
   OCEAN AGENT       WEATHER AGENT    MARITIME AGENT
          │                │                │
          ▼                ▼                ▼
       INCOIS           INCOIS/IMD     Geo datasets
       PFZ/OSF          Marine APIs     + spatial DB
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                  EVIDENCE AGENT
                           │
                           ▼
                    ORCA REASONER
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
             Decision          Confidence
                  │                 │
                  └────────┬────────┘
                           ▼
                     ASI:ONE CARD
```

------------------------------------------------------------------------

# 16. Data Source Strategy

## Tier 1 --- Primary / operational sources

### INCOIS

Use for:

-   Potential Fishing Zone
-   Ocean State Forecast
-   wave conditions
-   winds
-   currents
-   SST
-   chlorophyll-related marine information
-   high-wave/swell alerts
-   marine advisories

INCOIS is particularly important because its PFZ service already
combines satellite-derived ocean information into operational fishing
advisories.

PFZ: https://www.incois.gov.in/MarineFisheries/PfzAdvisory

PFZ WebGIS: https://www.incois.gov.in/MarineFisheries/PfzWebGis

OSF: https://www.incois.gov.in/oceanservices/osfforecast.jsp

------------------------------------------------------------------------

## Tier 2 --- Meteorological authority

### India Meteorological Department

Use for:

-   fishermen warnings
-   sea-area bulletins
-   coastal bulletins
-   cyclone track
-   cyclone wind warning
-   cyclone cone of uncertainty

API documentation: https://api.imd.gov.in/public/api_reference.html

------------------------------------------------------------------------

## Tier 3 --- Satellite/raw ocean data

### MOSDAC / ISRO

MOSDAC exposes ocean and satellite products including SST and
ocean-colour products. Its catalog contains current satellite products,
including OCM-derived products and other ocean layers.

MOSDAC PFZ: https://mosdac.gov.in/pfz/

Satellite catalog:
https://www.mosdac.gov.in/catalog/satellite?language=en

Important feasibility note:

Some MOSDAC datasets have registration/access constraints and usage
restrictions. Therefore, **raw MOSDAC data should not be a hard
dependency for the first live demo**.

Instead:

**Use INCOIS operational services for the core live workflow and cite
MOSDAC/ISRO data as part of the scientific ecosystem.**

If an appropriate MOSDAC product is accessible during development, it
can become an additional evidence source.

------------------------------------------------------------------------

## Tier 4 --- Maritime geometry

Use:

-   Marine Regions EEZ datasets
-   territorial-sea geometry
-   other legally appropriate geospatial datasets

For V1, keep this dataset locally available for fast spatial queries.

------------------------------------------------------------------------

# 17. What We Will NOT Build

To keep the hackathon focused:

-   No full custom web application
-   No custom authentication system
-   No mobile application
-   No large user dashboard
-   No generic chatbot UI
-   No raw satellite image processing pipeline unless it directly
    improves the demo
-   No autonomous vessel control
-   No claim that ORCA replaces official marine/navigation authorities

The main experience should live in:

> **ASI:One**

------------------------------------------------------------------------

# 18. MVP Scope

The MVP should answer one strong question exceptionally well:

> **"Given my location, intended time, and fishing range, what is the
> best risk-adjusted fishing zone?"**

### Required inputs

-   origin/location
-   time window
-   maximum distance
-   activity/fishing intent

### Required outputs

-   top 3 candidate zones
-   fishing potential
-   weather/sea risk
-   maritime safety
-   confidence
-   evidence sources
-   explanation of why the top zone won

### Optional but high-value

-   what-if analysis
-   multilingual response
-   interactive cards
-   route warning
-   real-time warning check

------------------------------------------------------------------------

# 19. The Main Demo

## Demo scenario

User opens ASI:One and says:

> "I want to go fishing tomorrow morning from Chennai. Find the best
> fishing zone within 30 km with good fishing potential and low sea
> risk."

### ORCA execution

``` text
ASI:One
   ↓
ORCA discovered
   ↓
Intent parsed
   ↓
Ocean Agent
   ↓
Find PFZ candidates
   ↓
Weather Agent
   ↓
Check waves/wind/cyclone/fishermen warnings
   ↓
Maritime Agent
   ↓
Check restricted areas/boundaries
   ↓
Evidence Agent
   ↓
Validate freshness/conflicts
   ↓
ORCA Reasoner
   ↓
Rank candidates
   ↓
Recommendation
```

### Final response

Example:

> **Zone B is the best current option.**
>
> Fishing potential: High\
> Sea risk: Low--Moderate\
> Boundary/restriction risk: Low\
> Data confidence: 89%
>
> **Why:** Zone B has strong fishing indicators while avoiding the
> higher wave-risk area identified for your requested time window.
>
> **Note:** This is decision support based on available data and should
> not replace official marine warnings or navigation procedures.

------------------------------------------------------------------------

# 20. The "Wow" Moment

After the first recommendation, ask:

> **"What if I go 15 km farther?"**

ORCA should visibly re-run the relevant agents.

Then show:

``` text
                 ORIGINAL       +15 KM
Fishing            81%            88%
Sea Safety         88%            64%
Boundary Risk       5%            21%
Confidence          93%            91%
------------------------------------------------
Decision          RECOMMEND      NOT RECOMMENDED
```

Then:

> "The additional distance increases fishing potential, but the safety
> and boundary risks make the original zone preferable."

This demonstrates:

**Agents + real data + reasoning + constraints + action-oriented
decision making.**

------------------------------------------------------------------------

# 21. Reliability / Failure Handling

ORCA must never fabricate a marine safety conclusion when critical data
is unavailable.

### Scenario

Weather API fails.

Bad behavior:

> "Weather looks safe."

Correct behavior:

> "I could not retrieve current marine weather data. I cannot provide a
> reliable low-risk recommendation for this request."

### Scenario

Data sources disagree.

ORCA should say:

> "Ocean and weather datasets are currently inconsistent. Recommendation
> confidence has been reduced."

### Scenario

Data is stale.

ORCA should surface:

> "Marine forecast data is older than the configured freshness
> threshold."

Reliability is part of the product, not an afterthought.

------------------------------------------------------------------------

# 22. Product USP

## Primary USP

> **ORCA combines fishing opportunity, marine weather, and maritime
> safety into one risk-aware decision instead of showing users
> disconnected data layers.**

## Stronger technical USP

> **ORCA uses specialized marine agents that independently gather
> evidence and then reconcile conflicting conditions before producing a
> decision.**

## Signature USP

> **ORCA can simulate how a decision changes when the user changes a
> constraint.**

Example:

> "What if I go farther?"

> "What if I leave earlier?"

> "What if I have only 20 km of range?"

The system recalculates rather than simply generating a new explanation.

------------------------------------------------------------------------

# 23. Why Fetch.ai Is Essential to ORCA

ORCA is not using Fetch.ai as a decorative integration.

Fetch provides the agent-centric interaction layer:

``` text
User Intent
    ↓
ASI:One
    ↓
Agent Discovery
    ↓
Agentverse
    ↓
ORCA + Specialist Agents
    ↓
ACP Communication
    ↓
Real-world data/tool execution
    ↓
Decision
    ↓
ASI:One
```

This makes ORCA a natural demonstration of:

-   Agentverse discovery
-   ASI:One intent routing
-   ACP communication
-   multi-agent collaboration
-   real-time external data
-   agent reasoning
-   reliability/recovery
-   Interactive Cards

------------------------------------------------------------------------

# 24. Hackathon Fit

Fetch-A-Thon 3.0 requires the project to:

-   solve a clearly defined real-world problem
-   perform multi-step planning/reasoning/orchestration
-   use tools, APIs, external services, data, MCP or other agents
-   register at least one agent on Agentverse
-   implement ACP
-   be directly usable through ASI:One
-   complete the primary workflow inside an ASI:One conversation
-   provide a public GitHub repository

ORCA is designed around these requirements rather than adapting to them
later.

Reference:
https://www.fetch.ai/events/hackathons/fetch-a-thon-3/hackpack

------------------------------------------------------------------------

# 25. Judging Strategy

## Functionality & Technical Implementation --- 25%

Demonstrate:

-   real API/data calls
-   real multi-agent communication
-   structured evidence
-   geospatial computation
-   deterministic scoring
-   failure handling

## Fetch.ai Technology --- 20%

Demonstrate:

-   Agentverse registration
-   ACP
-   ASI:One discovery
-   ASI1 participation in intent/reasoning
-   multiple agents
-   Interactive Cards

## Originality

Position ORCA as:

> **Marine decision intelligence rather than marine information
> retrieval.**

## Real-world Impact --- 20%

Focus on:

-   fishermen
-   small boat operators
-   coastal workers
-   coastal safety support

## UX & Presentation --- 15%

Keep the UI simple because the main experience is ASI:One.

------------------------------------------------------------------------

# 26. V1 Technical Stack

## Agent layer

-   Python
-   uAgents where useful for native Fetch integration
-   ACP
-   Agentverse
-   ASI:One

## Orchestration

Potential options:

-   lightweight Python orchestration
-   LangGraph only if it materially improves coordination
-   avoid unnecessary framework complexity

## Data processing

-   Python
-   requests/httpx
-   Pydantic
-   GeoPandas
-   Shapely
-   optional PostGIS for persistent spatial queries

## Data

Primary:

-   INCOIS
-   IMD

Secondary:

-   MOSDAC / ISRO
-   Marine Regions

## Storage

For MVP:

-   local/static geospatial data
-   lightweight PostgreSQL/PostGIS if required
-   Redis is not necessary for the first version

## LLM

Use ASI1 where it provides clear value:

-   intent interpretation
-   orchestration
-   natural-language synthesis
-   explanation

Do not use LLMs for:

-   distance calculations
-   polygon intersection
-   numeric scoring
-   timestamp validation
-   coordinate geometry

------------------------------------------------------------------------

# 27. Important Scientific/Product Boundary

ORCA is a prototype decision-support system.

It is **not**:

-   a certified navigation system
-   an official government advisory
-   a vessel autopilot
-   a replacement for IMD/INCOIS warnings
-   a guarantee of fishing yield
-   a legal authority on maritime boundaries

The system should always surface official-source warnings when relevant.

------------------------------------------------------------------------

# 28. Core Product Statement

## ORCA

> **Ocean Reasoning & Coordination Agent**

### Tagline

> **Don't read the ocean. Ask it.**

### One-sentence pitch

> **ORCA is a Fetch.ai-native multi-agent marine intelligence system
> that combines ocean, weather and maritime data to turn a fisherman's
> natural-language intent into an evidence-backed, risk-aware
> decision.**

### Technical pitch

> **ORCA uses ASI:One for intent and discovery, Agentverse/ACP for agent
> interaction, and specialized marine agents to fuse operational ocean
> forecasts, fishing-zone advisories, meteorological warnings and
> geospatial constraints into a traceable decision.**

------------------------------------------------------------------------

# 29. Build Priority

## P0 --- Must work

1.  ORCA entry agent
2.  Agentverse deployment
3.  ACP
4.  ASI:One discovery
5.  INCOIS PFZ integration
6.  INCOIS/IMD marine weather integration
7.  Maritime spatial check
8.  Evidence model
9.  Risk-aware ranking
10. ASI:One final response

## P1 --- Strong differentiators

11. Interactive Cards
12. What-if analysis
13. multilingual response
14. confidence scoring
15. failure/recovery behavior

## P2 --- Only if time remains

16. voice interaction
17. additional satellite layers
18. route visualization
19. historical trend analysis
20. autonomous recurring monitoring

------------------------------------------------------------------------

# 30. Final Product Decision

## LOCKED

We are building:

> **ORCA --- Ocean Reasoning & Coordination Agent**

A backend-heavy, Fetch.ai-native multi-agent marine decision-support
system.

### Primary user experience

**ASI:One**

### Primary deployment

**Agentverse**

### Communication

**ACP**

### Core agents

1.  ORCA Commander
2.  Ocean Intelligence Agent
3.  Weather & Marine Forecast Agent
4.  Maritime Safety Agent
5.  Evidence & Reliability Agent

### Primary data strategy

**INCOIS + IMD first**

**MOSDAC/ISRO as secondary/optional satellite data source**

### Core decision

> **Find the best risk-adjusted marine opportunity for a user's
> requested activity, location, time and constraints.**

### Signature feature

> **What-if decision simulation**

### Product philosophy

> **Data is fragmented. ORCA turns it into a decision.**

------------------------------------------------------------------------

# 31. Research Sources

-   Fetch-A-Thon 3.0 Hackpack:
    https://www.fetch.ai/events/hackathons/fetch-a-thon-3/hackpack
-   Fetch-A-Thon 3.0: https://www.fetch.ai/events/fetch-a-thon-3
-   INCOIS Potential Fishing Zone Advisory:
    https://www.incois.gov.in/MarineFisheries/PfzAdvisory
-   INCOIS PFZ WebGIS:
    https://www.incois.gov.in/MarineFisheries/PfzWebGis
-   INCOIS Ocean State Forecast:
    https://www.incois.gov.in/oceanservices/osfforecast.jsp
-   INCOIS High Wave/Swell Advisories:
    https://iioe-2.incois.gov.in/site/services/hwa.jsp
-   IMD API Reference: https://api.imd.gov.in/public/api_reference.html
-   IMD Marine Forecast:
    https://mausam.imd.gov.in/responsive/marine_forecast.php
-   MOSDAC PFZ: https://mosdac.gov.in/pfz/
-   MOSDAC Satellite Catalog:
    https://www.mosdac.gov.in/catalog/satellite?language=en
-   Marine Regions Downloads:
    https://www.marineregions.org/downloads.php
-   Marine Regions Web Services:
    https://www.marineregions.org/webservices.php
