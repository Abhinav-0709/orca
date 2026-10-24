# 🌊 ORCA — Ocean Reasoning & Coordination Agent (Agentverse Hosted Agent)

![protocol : ACP v0.3.0](https://img.shields.io/badge/ACP-v0.3.0-blueviolet)
![platform : Agentverse](https://img.shields.io/badge/platform-Agentverse-orange)
![model : ASI%3AOne](https://img.shields.io/badge/model-ASI%3AOne-brightgreen)
![status : Live](https://img.shields.io/badge/status-Live%20on%20Almanac-brightgreen)

> **Fetch-A-Thon 3.0 — ASI:One Agent Challenge**  
> *"Don't read the ocean. Ask it."*

ORCA is an autonomous marine decision-support agent hosted 24/7 on **Agentverse** and directly indexed by **ASI:One**. It transforms fragmented oceanographic feeds into risk-adjusted operational recommendations for fishermen and coastal operators with **deterministic non-linear safety dominance** and live **What-If simulation recomputation**.

---

## 🌟 Live Agent Details

- **Agent Address:** `agent1q2q4wrsxn4jv8th8amtnkuv5m8qyuqlxq7x2g4wq24yx4r0wtvyhuwk0xzm`
- **Almanac Contract:** Registered on Almanac fast track
- **Discovery Protocol:** Official Agent Chat Protocol (`spec=chat_protocol_spec`, `publish_manifest=True`)
- **Direct Chat URL:** [https://asi1.ai](https://asi1.ai) (Search for `orca` or the agent address)

---

## 🌊 Architecture & Data Sources

```text
                  ┌──────────────────────────────┐
                  │      ASI:One / User Chat     │
                  └──────────────┬───────────────┘
                                 │ (ACP v0.3.0 ChatMessage)
                                 ▼
                  ┌──────────────────────────────┐
                  │   Agentverse Hosted Agent    │
                  │        (agent.py)            │
                  │                              │
                  │  • Immediate ChatAck Receipt │
                  │  • Intent & Hub Extraction   │
                  │  • Stateful User Sessions    │
                  │  • What-If Recomputation     │
                  │  • Interactive Card Prompts  │
                  └──────┬───────────────┬───────┘
                         │               │
         ┌───────────────▼─┐           ┌─▼───────────────┐
         │ INCOIS PFZ Feed │           │ Open-Meteo API  │
         │ Ocean Forecasts │           │ Real ECMWF Sea  │
         │ SST & Chloroph. │           │ Waves & Swells  │
         └─────────────────┘           └─────────────────┘
```

### Integrated Live Intelligence:
1. **INCOIS (Indian National Centre for Ocean Information Services):**
   - Potential Fishing Zones (PFZ) advisory coordinates.
   - Chlorophyll concentration and Sea Surface Temperature (SST) thermal fronts.
2. **Open-Meteo Marine API (Global ECMWF Model):**
   - Live Significant Wave Height (SWH) and wind waves.
   - Swell height, swell period, and swell direction.
   - Sea surface currents and water temperatures.
3. **Maritime GIS & Boundary Buffer Engine:**
   - Proximity evaluation to International Maritime Boundary Line (IMBL in Palk Bay / Gulf of Mannar).
   - EEZ boundary clearance and restricted marine sanctuaries.

---

## 🛡️ Risk-Adjusted Decision Formula

$$\text{Composite Score} = (\text{Opportunity} \times w_{\text{opp}} + \text{Accessibility} \times w_{\text{acc}}) \times \text{Safety Multiplier} \times \text{Confidence}$$

- **Safety Gate:** Wave heights > 2.0m or restricted international maritime buffer proximity automatically result in **disqualification** ($\text{Score} = 0.0$).
- **Safety strictly outranks opportunity** at all times.

---

## 🔄 Signature What-If Recomputation

Unlike ordinary conversational agents that produce static text descriptions, ORCA recomputes candidates upon user constraint adjustments:
- *"What if I travel 15 km farther?"* -> Expands operational radius, runs marine safety checks on deeper zones, and shows side-by-side metric deltas.
- *"What if I prioritize maximum safety?"* -> Re-weights the decision engine toward sheltered waters and calm sea states.
- *"What if I leave at 5:00 AM instead?"* -> Shifts operational window and checks forecast variations.

---

## 💬 Sample User Queries to Try on ASI:One

1. **Standard Recommendation:**
   > `@orca Find me the best fishing zone from Chennai within 30 km tomorrow morning`
2. **What-If Exploration:**
   > `What if I travel 15 km farther offshore?`
3. **Safety Mode Switch:**
   > `What if I prioritize maximum safety over catch volume?`
4. **Different Coastal Hubs:**
   > `Find me safe fishing zones near Kasimedu, Visakhapatnam, Kochi, or Rameswaram`
5. **Inland Location Clarification:**
   > `Find fishing near Roorkee` *(ORCA clarifies inland location and directs to coastal ports)*
6. **Capabilities & System Info:**
   > `Tell me what you were created to do`

---

## 🛠️ Local Development & Cloud Deployment

This hosted agent is synchronized with the Agentverse cloud using `avctl`:

```powershell
# Pull latest cloud version:
avctl hosting pull -a agent1q2q4wrsxn4jv8th8amtnkuv5m8qyuqlxq7x2g4wq24yx4r0wtvyhuwk0xzm

# Stop agent before pushing updates:
avctl hosting stop -a agent1q2q4wrsxn4jv8th8amtnkuv5m8qyuqlxq7x2g4wq24yx4r0wtvyhuwk0xzm

# Push local code:
avctl hosting push -a agent1q2q4wrsxn4jv8th8amtnkuv5m8qyuqlxq7x2g4wq24yx4r0wtvyhuwk0xzm

# Run agent on Agentverse:
avctl hosting run -a agent1q2q4wrsxn4jv8th8amtnkuv5m8qyuqlxq7x2g4wq24yx4r0wtvyhuwk0xzm

# View live cloud logs:
avctl hosting logs -a agent1q2q4wrsxn4jv8th8amtnkuv5m8qyuqlxq7x2g4wq24yx4r0wtvyhuwk0xzm
```

---

## ⚖️ Safety Disclaimer

ORCA is a decision-support prototype built for Fetch-A-Thon 3.0. Always verify official Indian Coast Guard, INCOIS, and IMD coastal bulletins before departing on any voyage.
