# SOC Optimization Framework — Contributor Guide

This guide explains how to contribute correctly to the SOC Optimization Framework.  
It includes the full contribution workflow, branch naming rules, modular coding standards, and PR requirements.

Maintainers: @Palo-Cortex/soc-framework-maintainers

---

# 1. Contribution Workflow

1. Fork the repository  
2. Clone your fork:

       git clone https://github.com/<your-username>/soc-optimization.git
       cd soc-optimization

3. Create a branch using the SOC Framework naming convention  
4. Make your changes following the Modular Coding Standards  
5. Commit and push your branch  
6. Open a Pull Request  
7. Tag reviewers: @Palo-Cortex/soc-framework-maintainers  
8. Maintainers review → validate → merge  

---

# 2. Branch Naming Convention (Required)

Branches also function as feature flags, so correct naming is mandatory.

Format:

       <type>/<module>/<component>/<slug>

## Types

       feat | fix | chore | docs | refactor

## SOC Framework Modules

       entrypoint
       upon-trigger
       hydration
       normalization
       enrichment
       containment
       eradication
       recovery
       communication
       data-modeling
       correlation
       playbooks
       lists
       common-utils
       dashboards
       project          ← for workflows, CI/CD, repo structure, governance

## Component

A sub-area within a module. Must be kebab-case.

Examples:

       entity-mapping
       artifact-extraction
       email
       endpoint
       crowdstrike
       case-init
       severity
       workflows
       ci
       docs
       maintenance

## Slug

Short, clear, kebab-case description of the change.

## Examples

       feat/upon-trigger/entity-mapping/auto-resolve-user
       fix/data-modeling/crowdstrike/fix-process-lineage
       feat/containment/endpoint/auto-isolate-host
       docs/playbooks/phishing/update-docs
       chore/project/workflows/update-branch-guard

---

# 3. Modular Coding Standards (Required)

All contributions must follow the SOC Framework’s modular architecture and FieldOps design principles.

## 3.1 Build “Lego Bricks”

Each contribution must be:

- Reusable  
- Composable  
- Self-contained  
- Single-purpose  
- Vendor-agnostic unless intentionally vendor-specific  
- Free of customer-specific data  

## 3.2 Place code in the correct SOC Framework layer

Primary architecture:

       Entry Point
         → Upon Trigger
             → Hydration
             → Normalization
             → Entity Mapping
             → Artifact Extraction
             → Severity / Priority
             → Ownership
         → Enrichment
         → Containment
         → Eradication
         → Recovery
         → Communication

Supporting modules:

       Data Modeling
       Correlation
       Playbooks
       Lists
       Dashboards
       Common Utils
       Project (for workflows, CI/CD, governance)

Your contribution must live in the correct directory for the module it supports.

## 3.3 Vendor Logic Must Be Isolated

Examples:

       data-modeling/crowdstrike/...
       data-modeling/microsoft/...
       data-modeling/trendmicro/...

Never mix core logic with vendor-specific code.

## 3.4 Never Include Customer-Specific Data

Do NOT commit:

- Customer usernames  
- Domains  
- IP addresses  
- Tenant identifiers  
- Integration instance names  

Always use variables, normalized fields, or lists.

## 3.5 Development Sequence: Normalize → Correlate → Playbook

The correct build order:

1. Model your fields  
2. Build correlation logic  
3. Develop playbooks that consume normalized context  

Never build playbooks on raw data.

## 3.6 Documentation Required

Each new module or component must include:

- Purpose  
- Inputs  
- Outputs  
- Dependencies  
- Example behavior  

---

# 4. Pull Request Requirements

Every PR must include:

## ✔ Proper branch name

       <type>/<module>/<component>/<slug>

## ✔ PR checklist completed
- Affected modules selected  
- Testing described  
- Dependencies listed  
- Documentation updated if needed  

## ✔ Maintainers tagged

       @Palo-Cortex/soc-framework-maintainers

## ✔ Clean commit messages

Examples:

       feat(upon-trigger/entity-mapping): improve user identity resolution
       fix(data-modeling/crowdstrike): correct process lineage parsing
       docs(playbooks/phishing): update flow and explanation
       chore(project/workflows): optimize validation workflow

---

# 5. Governance Summary

- Maintainers team is **visible**, role = **Maintain**
- Admin team is **private**, minimal membership
- All contributors use forks + PRs
- CODEOWNERS enforces mandatory review
- Branch naming validated automatically
- Feature flags generated from branch names

---

# 6. Need Help?

If you get stuck, tag:

       @Palo-Cortex/soc-framework-maintainers

We’re here to help guide contributors and maintain high standards for the SOC Optimization Framework.
