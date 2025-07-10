# CIA Alignment for Auto-Triage Usage

While the Auto-Triage playbook enforces clean pipelines and automation hygiene, its behavior should **respect the business priorities** of the industry it's deployed in. These priorities are often expressed through the **CIA Triad**: Confidentiality, Integrity, and Availability.

This document provides **industry-centric guidance** on how to adjust Auto-Triage logic and settings based on dominant CIA concerns.

---

## 🎯 Why Align CIA to Auto-Triage?

Not all false positives are equal. An auto-closed incident on an MRI system is more dangerous in healthcare than retail. Similarly, alerting too aggressively on uptime issues in a finance org may be less useful than catching data exfiltration attempts.

**Auto-Triage logic must reflect what the business values most.**

---

## 🏭 CIA Tuning by Industry

| Industry             | CIA Priority   | Auto-Triage Recommendations                                         |
|----------------------|----------------|---------------------------------------------------------------------|
| **Healthcare**       | **A > I > C**   | ✅ Shorten delay to 2h for availability alerts. 🚫 Never auto-close alerts about patient record systems or connected devices. |
| **Finance**          | **C > I > A**   | 🚫 Never auto-close anything involving PII, DLP, or data classification tags. ✅ Star high-severity data access anomalies. |
| **Manufacturing**    | **I > A > C**   | 🚫 Disable auto-triage entirely in OT environments. ✅ Require human review for control system alerts. |
| **Retail**           | **C > A > I**   | ✅ Auto-close low-severity availability alerts. 🚫 Preserve data theft alerts for manual review. |
| **SaaS / Tech**      | **I > C > A**   | ✅ Auto-close uptime blips. 🚫 Elevate integrity violations (e.g., binary modification, code injection). |

---

## 🧠 Best Practices for CIA-Aware Auto-Triage

- 🛠️ **Tune the 6-Hour Window:**
  Adjust per industry pace. For example:
    - Healthcare: `2-4h`
    - Finance: `6-12h`
    - Manufacturing: `Manual review only`

- 🧩 **Layer with Tags or Scores:**
  Use data classification, MITRE tactic, or custom tags to exempt incidents from auto-triage if they involve sensitive areas.

- ⚙️ **Make It Configurable:**
  Use the `SOCOptimizationConfig` list in  
  **Settings → Configurations → Object Setup → Lists**  
  to dynamically adjust:
    - Wait time
    - Minimum alert severity
    - Allowlist/denylist of alert types

- 🔁 **Feedback Loop:**
  Review auto-closed incidents by industry segment quarterly. Refine starring and scoring policies based on:
    - Business false negatives
    - Missed SLA targets
    - Analyst feedback

---
