                        ┌────────────────────────────┐
                        │  Incoming Alert / Issue    │
                        └─────────────┬──────────────┘
                                      │
                             Severity ≥ Medium ?
                                      │
                        ┌─────────────┴──────────────┐
                        │                            │
                      No│                            │Yes
                        │                            ▼
                        │              ┌──────────────────────────────┐
                        │              │ Initial Normalization        │
                        │              │  - Run EP_NIST_IR_(800-61)   │
                        │              │  - SOC_NormalizeContext      │
                        │              └─────────────┬────────────────┘
                        │                            │
                        │                    MITRE Tactic Found?
                        │                            │
                        │            ┌───────────────┴───────────────┐
                        │            │                               │
                        │          No│                               │Yes
                        │            │                               │
                        ▼            ▼                               ▼
             ┌────────────────┐   ┌────────────────────┐   ┌────────────────────┐
             │ Not Starred    │   │  Auto-Starred      │   │  Auto-Starred      │
             │ (Low Fidelity) │   │  (High Fidelity)   │   │  (Analyst Manual)  │
             └──────┬─────────┘   └──────────┬─────────┘   └──────────┬─────────┘
                    │                      │                        │
                    │                      ▼                        ▼
           ┌────────▼─────────┐  ┌───────────────────────────────┐  ┌────────────────────┐
           │  Queue for 6 hrs │  │ Run SOC_NIST_IR_(800-61)     │  │ Run SOC_NIST_IR_(800-61) │
           │  (Auto-Triage)   │  │ (Full IR, response, comms)   │  │ (Manual escalation) │
           └────────┬─────────┘  └──────────────┬────────────────┘  └──────────┬─────────┘
                    │                           │                         │
        Unstarred after 6 hrs?                  │                         │
                    │                           │                         │
          ┌─────────┴─────────┐                 │                         │
          │ Auto-Close        │                 │                         │
          │ Low-Fidelity Case │                 │                         │
          └───────────────────┘                 ▼                         ▼
                                       Alert Processed / Resolved   Alert Processed / Resolved
