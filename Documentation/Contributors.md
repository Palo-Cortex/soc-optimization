# 🧩 SOC Optimization Framework — Contributor Guide

Welcome to the **SOC Optimization Framework** repository!  
This project provides reusable automations, playbooks, and models aligned with the NIST Incident Response lifecycle.  
Our goal is to keep content **modular, measurable, and easy to extend** by Domain Consultants (DCs), Professional Services (PS), partners, and customer contributors.

---

## 🚀 Getting Started

Follow these steps to contribute a new idea, feature, or improvement.

1. **Fork the Repository**  
   Click the **Fork** button at the top right of this page to create your own copy of the repository.

2. **Clone Your Fork**  
   Open a terminal and clone your fork locally, replacing `<your-username>` with your GitHub username:

       git clone https://github.com/<your-username>/soc-optimization.git
       cd soc-optimization

3. **Create a New Branch**  
   Each new idea or feature should be developed in its own branch.  
   Branches also act as **feature flags**, allowing us to automatically build and test your work.

   Use this naming format:

       <type>/<surface>/<phase>/<short-description>

   **Examples**

       feat/identity/containment/auto-disable-risky-users
       fix/core/trigger/alert-timestamp-normalization
       docs/core/communication/playbook-standards

   **Segment Definitions**

   | Segment | Examples | Description |
      |----------|-----------|-------------|
   | type | feat • fix • chore • docs • refactor | Type of change you’re making |
   | surface | data • network • identity • endpoint • cloud • email • core • playbooks | Which SOC domain or module is impacted |
   | phase | trigger • analysis • containment • eradication • recovery • communication | NIST phase or automation layer |
   | short-description | auto-disable-risky-users | A brief kebab-case name describing your feature |

---

## 🧱 Submitting Your Changes

1. **Make your edits or add new content**  
   Be sure to follow the existing folder structure and naming conventions.

2. **Commit your work**

       git add .
       git commit -m "feat(identity/containment): auto-disable risky users"

3. **Push your branch**

       git push origin <your-branch-name>

4. **Create a Pull Request (PR)**
    - Go to your fork on GitHub.
    - Click **Compare & Pull Request**.
    - Provide a clear description of what you added or changed.
    - The repository maintainers will review, test, and merge your changes.

---

## 🧩 Feature Flags in CI/CD

When you create a branch following the naming rules, the **branch name automatically becomes a feature flag** used by our build and validation pipelines.  
This allows isolated testing of new ideas without disrupting mainline content.

---

## ✅ Tips for New Contributors

- Keep branches small and focused — one idea per branch.
- Always pull the latest `main` before starting new work.
- Use meaningful commit messages (`feat`, `fix`, `docs`, etc.).
- Check existing content for examples before creating new files.
- Don’t worry about perfection — focus on clarity and modularity.

---

## 💬 Need Help?

If you’re new to GitHub:
- Ask your Domain Consultant or PS contact for assistance.
- Or open a GitHub Issue in this repo and tag **@Palo-Cortex/soc-framework-admins**.

We’re glad you’re contributing to the SOC Optimization Framework —  
together, we’re building the future of scalable, automated security operations!
