# ⚙️ SOC Optimization Framework for Cortex XSIAM

This repository outlines a scalable SOC optimization approach tailored for Palo Alto Networks Cortex XSIAM. The goal is to reduce analyst fatigue, improve response time, and enable data-driven visibility into automation value. The solution is based on three core patterns and enhanced by modular design and operational safeguards.

---

## 🔁 Core Patterns

### 1. **Auto-Triage for Non-Starred Incidents**
- Incidents that are not marked with a star are automatically triaged using `JOB_-_Triage_Incidents.yml`.
- Ensures that high-volume, low-risk alerts are handled without manual intervention.

### 2. **Modular Playbooking via `Upon Trigger`**
- The `Upon Trigger` playbook is the engine of modular decision-making.
- It divides alert processing into four logical stages:
  - **Alert Triage**
  - **Enrichment**
  - **Auto Remediation**
  - **Assessment and Escalation**
- This playbook dynamically decides whether to run in **Shadow Mode** (safe/test) or **Full Mode** (production) using contextual data.

### 3. **Value Metrics for Automation Efficiency**
- The `JOB_-_Store_Playbook_Metrics_in_Dataset.yml` playbook collects key metrics and stores them in a dataset.
- Combined with the `value_tags` lookup table, metrics enable dashboards to measure:
  - ⏱️ **Time saved** by XSIAM automations.
  - 📊 **Time spent** by category (triage, enrichment, remediation, etc.).
  - 🔌 **Vendor product usage** across automations.
  - 🛠️ **Custom scripting vs. out-of-the-box content**.
  - 📈 **Alert metrics per data source**:
    - Alert volume
    - Grouping effectiveness
    - Auto-remediation success rate
    - Analyst review backlog

---

## 🧩 Playbook Structure

### Main Playbooks:
- **Upon Trigger** – Modular logic engine for alert decisioning
- **Emergency Resolver** – Escalation logic for critical alert closures

### Job Playbooks:
- **JOB_-_Triage_Incidents.yml** – Auto-triages non-starred incidents
- **JOB_-_Store_Playbook_Metrics_in_Dataset.yml** – Stores value metrics

---

## ⚙️ Configuration and Lists

This framework uses system-level lists for dynamic context:

- **`SOCOptimizationConfig`**  
  Stores runtime configuration flags, such as enabling/disabling Shadow Mode.

- **`AssetTypes`**  
  Documents high-value or administrative assets to influence alert escalation.

- **`ProductionAssets`**  
  Controls which assets bypass Shadow Mode and receive live remediation.

- **`JobUtilityBulkAlertCloserIDList`**  
  Used by the Emergency Resolver to safely close large volumes of alerts within thresholds.

---

## 🧪 Shadow Mode Logic

Shadow Mode is a key safety mechanism. It ensures actions like `isolate_endpoint` or `disable_user` are logged but **not executed** in test scenarios. Shadow Mode decisions are:
- Made in the `Upon Trigger` playbook.
- Stored in the incident’s data context.
- Controlled via `ProductionAssets` and `SOCOptimizationConfig` lists.

---

## 📊 Metrics and Dashboards

The metrics collected are designed to demonstrate **operational value**:

| Metric Type         | Description                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| Time Saved          | Total analyst time replaced by automation                                   |
| Time Spent          | Time breakdown across enrichment, triage, remediation, etc.                 |
| Vendor Usage        | How often and where each vendor’s integration is leveraged                  |
| Custom Content Use  | Measures reliance on custom scripts vs out-of-the-box playbooks             |
| Alert Source Metrics| Insight per data source: volume, grouping, remediation, and leftovers       |

---

## 📷 Visual Overview

![SOC Automation Foundation - Upon Trigger](./images/UponTrigger.png)

> *Diagram illustrates the four-stage logic inside the Upon Trigger playbook: Alert Triage, Enrichment, Auto Remediation, and Assessment & Escalation.*
