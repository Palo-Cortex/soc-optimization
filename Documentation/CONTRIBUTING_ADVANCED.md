# Advanced Contributor Guide

Use this guide if you want to work locally, run validation tools, or contribute larger changes.

Most contributors only need the GUI workflow described in the main CONTRIBUTING.md.

---

## Forking & Local Setup

1. Click **Fork** at the top of the repo  
2. Clone your fork:
   ```
   git clone https://github.com/<your-username>/soc-optimization
   cd soc-optimization
   ```
3. Create a branch:
   ```
   git checkout -b feat/core-normalizer-update
   ```

---

## Local Validation (Optional)

If working with YAML or rules:

```
demisto-sdk validate -a
```

Other tools may live in `tools/`:
```
python tools/xsiam_schema_sync.py
```

---

## Push & Open a PR

```
git push --set-upstream origin <branch-name>
```

Then open a Pull Request and tag:
```
@Palo-Cortex/soc-framework-maintainers
```

Advanced users can also help with:
- CI/CD
- automation scripts
- repo structure improvements
