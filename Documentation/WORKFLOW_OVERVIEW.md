# Workflow Overview (Internal)

This explains the internal branch flow used to promote content across environments.

Most contributors do **not** need this.

---

## Branch Flow

```
feature → dev → staging → main
```

### dev
- Integration branch  
- New features land here first  

### staging
- Demo-ready  
- Used for POVs and validation  

### main
- Production baseline  
- Releases are generated from here  

---

## Release Process
1. Merge `dev` → `staging` after validation  
2. Validate in staging  
3. Merge `staging` → `main`  
4. Package content using `xsoar_config.json`  
5. Deploy to target tenant  

This ensures safe promotion and clean release history.
