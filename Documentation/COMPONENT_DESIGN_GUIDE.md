# Component Design Guide

When adding a new component (playbook, rule, script, modeling rule, installer logic), include a short description of what it does.

Use the template below in your PR or in a `.notes.md` file.

---

## Component Notes Template

### Component Name
Short, clear name.

### Purpose
What is this component supposed to do?  
1–3 sentences.

### SOC Framework Stage
Where it fits:
- Trigger  
- Hydration  
- Normalization  
- Artifacts / Entity Mapping  
- Enrichment  
- Containment  
- Eradication  
- Recovery  
- Communication  
- Modeling  
- Correlation  
- Utilities  

### Inputs
Key fields, artifacts, or context required.

### Outputs
What this component produces for the next stage.

### Dependencies
Lists, datasets, commands, or normalizers required.

### Vendor Scope
Core or vendor-specific.

### Test Strategy
How someone should verify it works.

---

This guide ensures content stays modular, readable, and easy to test.
