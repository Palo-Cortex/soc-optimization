# ⚙️ Upon Trigger Foundation – XSIAM SOC Automation

The **“Upon Trigger”** foundation playbook is the starting point for any **entry point playbook** — triggered by specific alerts in XSIAM. It establishes the core automation logic for handling alerts consistently and intelligently from the moment they enter the system.

![When to Use the 'Upon Trigger' Foundation](/images/When_To_Use_Upon_Trigger.png)

---

## ✅ When to Use the “Upon Trigger” Foundation

Use the `Upon Trigger` playbook **as the first task** in:

- Any alert-level **entry point** playbook.
- Any automation flow that begins **immediately upon alert ingestion**.
- Use cases where **alert triage, enrichment, and auto-remediation** need a consistent launch point.
- Scenarios where you want to drive **low-to-no-touch response**, while maintaining flexibility and oversight.

> This ensures every triggered playbook begins with clean, enriched, and normalized alert data — enabling safe automation and smart escalation.

---

## 📦 What It Provides

| **Stage**                 | **Value Delivered**                                                       |
|---------------------------|----------------------------------------------------------------------------|
| **Alert Triage**          | Normalize and deduplicate raw alerts                                      |
| **Enrichment**            | Add context: user, host, domain, file, etc.                               |
| **Auto Remediation**      | Evaluate and execute remediation if safe and in scope                     |
| **Assessment & Escalation** | Adjust severity, flag for analyst review, notify SOC if critical       |

---

## 🧩 Where and How to Add To It

You can extend `Upon Trigger` to suit your specific use cases:

### 🔹 Add Custom Enrichment
- Geo-IP history
- Threat intel lookups (e.g., VirusTotal, Recorded Future)

### 🔹 Plug in Decision Gates
- Branch by alert **source**, **asset type**, or **user role**

### 🔹 Connect Specialized Remediation
- Host isolation
- User disablement
- Session token revocation

### 🔹 Adjust Escalation Flow
- Route differently by **business unit**, **time of day**, or **incident type**

---

## 🧭 FieldOps Tie-In

| **FieldOps Phase** | **Who** | **Where It Fits**                                                         |
|--------------------|---------|----------------------------------------------------------------------------|
| **PoV**            | DC      | Starts alert-level automation; builds trust in triage and enrichment      |
| **Post-Sales**     | PS      | Becomes reusable foundation for tenant-specific scaling                   |
| **Pre-Sales**      | SC      | Used in BYOS Lab to show high-fidelity alert automation                   |

---

## 📝 Suggested Narrative

> “Every alert that triggers automation in XSIAM starts with the same foundation — the ‘Upon Trigger’ playbook. It ensures we’re working with clean, enriched data before making any decisions. From deduplication to environment detection, it’s the runway for everything we automate. And because it's modular, we can add custom logic or remediation tailored to each use case, without rebuilding from scratch. It’s our first step toward measurable automation.”

---

## 📁 File Structure Suggestion (Optional)
/playbooks/
├── upon_trigger_base.yml
├── enrichment_modules/
├── remediation_modules/
└── escalation_flows/
