# 📘 Entry Point Playbooks in Cortex XSIAM

Entry Point (EP) playbooks are the foundational routing layer of the SOC Optimization Framework. They ensure scalable, modular, and safe execution of security response workflows in XSIAM.

---

## 🔑 Purpose

Entry Point playbooks serve as the **first step** in the execution chain. Their role is to:

- Trigger the correct **MITRE Tactic playbook**
- Support **blue/green deployment** logic
- Simplify DevOps-style staging, rollback, and promotion
- Provide a consistent routing interface regardless of alert source

---

## 🧠 How It Works

Each Entry Point playbook is named after a MITRE tactic and acts as a **router**.

```
EP_InitialAccess
EP_Execution
EP_Persistence
...
```

Each playbook includes logic to:
1. Query the `PlaybookDeploymentMatrix` list using its own name.
2. Dynamically call either the `prod` or `green` version of the tactic playbook.
3. Fail cleanly if no matching version is found or enabled.

---

## 🔁 Deployment State Logic

The `PlaybookDeploymentMatrix` list tracks:

| name             | enabled | prod                              | green                            |
|------------------|---------|------------------------------------|----------------------------------|
| EP_Execution      | true    | Execution - Response v1.0         | Execution - Response v1.1-dev    |
| EP_InitialAccess  | true    | Initial Access - Response v1.0    | Initial Access - Response v1.1   |

- `prod` is the current live version
- `green` is the staging version for safe rollout
- `enabled` gates deployment actions

---

## 🧪 Use Cases

| Use Case          | Entry Point          | Triggers From                      |
|-------------------|----------------------|------------------------------------|
| Phishing Email    | EP_InitialAccess     | Email gateway, Proofpoint, O365    |
| Malware Execution | EP_Execution         | EDRs like CrowdStrike or Cortex XDR|
| Credential Abuse  | EP_Impact            | Identity provider or SIEM alerts   |

---

## 🧭 Best Practices

- Always include an `enabled` check before executing a green playbook
- Fail safely if no green playbook is defined
- Use sub-playbooks for tactics so you can reuse and promote them independently
- Tags for Entry Points must match the `PlaybookDeploymentMatrix.name` exactly

---

## 📊 Integration with Value Metrics

All Entry Points should call the `setValueTags` script to update the `value_tags` lookup table with playbook execution metrics. This allows visibility into automation usage, time saved, and script-level actions.

👉 See [setValueTags Usage](https://github.com/Palo-Cortex/soc-optimization/blob/main/Documentation/setValueTags.md)

---

## 🛠️ Developer Workflow

1. Modify or create a new playbook (e.g., `Execution - Response v1.1-dev`)
2. Add it to the `green` field in the `PlaybookDeploymentMatrix`
3. Enable the Entry Point if not already
4. Promote to production by copying green to prod
5. Use `rollback` if needed

---

## 📦 Related Files

- `scripts/setValueTags.py` — Tracks execution metadata for dashboards
- `PlaybookDeploymentMatrix` — Lookup list used for blue/green routing
- Entry Point Playbooks:
  - `EP_InitialAccess`
  - `EP_Execution`
  - `EP_Persistence`
  - (One for each MITRE tactic)

---

## 🔒 Safety Controls

Entry Points also support:
- Shadow Mode gating
- Asset-based exclusions via lists
- Auto-retry logic for high-value alerts (optional)

These mechanisms make sure testing and production can safely coexist.

---

