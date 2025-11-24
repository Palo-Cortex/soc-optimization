# Contributing to the SOC Optimization Framework

Most contributors will use the **GitHub Web interface**.

You do **not** need Git, the command line, or SDK tools to make basic changes.  
This guide explains the simplest way to contribute using the GitHub GUI.  
More advanced options are linked at the bottom.

---

## ⭐ How to Make a Simple Change (GitHub Web GUI)

Use this when you want to update an existing file (playbook, rule, script, modeling rule, installer, documentation, etc.).

1. Open the file you want to change in GitHub  
2. Click the **✏️ Edit** button  
3. GitHub will prompt you to create a new branch  
4. Enter a branch name using this format:
   ```
   <type>/<area>-<short-description>
   ```
   Examples:
   ```
   feat/email-improve-phishing-flow
   fix/core-normalizer-hash-bug
   docs/core-update-readme
   ```
5. Click **Create branch and start editing**  
6. Make your changes in the editor  
7. Scroll down and click **Commit changes**  
8. On the next screen, click **Create pull request**  
9. In the PR description, briefly describe what you changed  
10. Tag the maintainers:
    ```
    @Palo-Cortex/soc-framework-maintainers
    ```

The maintainers will review your changes and follow up if anything else is needed.

---

## ⭐ How to Upload or Replace a File (From XSIAM → GitHub)

Use this flow when you exported a file from XSIAM and want to update it in the repository.

1. Navigate to the folder where the file belongs  
2. Click **Add file → Upload files**  
3. Drag your exported file into the upload area  
4. If GitHub shows a message about replacing an existing file with the same name, confirm the replacement  
5. In the commit section:
   - Make sure **“Commit directly to the `<your-branch-name>` branch”** is selected  
   - Add a short commit message  
   - Click **Commit changes**  
6. If you haven’t opened a Pull Request yet, click **Compare & pull request**, or use the **Pull requests** tab  
7. Describe what you uploaded and why  
8. Tag the maintainers

If you're unsure where a file belongs, upload it in the PR and mention it — we will help place it correctly.

---

## ⭐ Branch Naming (Required)

Use this pattern:

```
<type>/<area>-<short-description>
```

**Types:**

- `feat` – new feature or behavior  
- `fix` – bug fix  
- `docs` – documentation changes  
- `chore` – maintenance or cleanup  
- `refactor` – internal restructuring without changing behavior  

**Areas:**

- `core`  
- `endpoint`  
- `email`  
- `identity`  
- `network`  
- `pov`  
- `tooling`  

**Examples:**

```
feat/core-add-file-artifact
fix/endpoint-containment-timeout
docs/email-update-phishing-docs
chore/tooling-update-ci-workflow
```

More details:  
➡️ `docs/BRANCH_NAMING.md`

---

## ⭐ What Is a Pull Request? (Short Version)

A **Pull Request (PR)** is simply a request to merge your changes into the main project.

When you open a PR:

- Maintainners can review your changes  
- They can comment and suggest improvements  
- When everything looks good, they approve and merge your branch  

You do not need to know how Git works behind the scenes.

More details:  
➡️ `docs/WHAT_IS_A_PR.md`

---

## ⭐ Additional Helpful Guides (Optional)

These are **optional** and meant for contributors who want to go deeper:

- ➡️ `docs/MULTI_FILE_EDITS.md` – How to edit multiple files in one branch using the GUI  
- ➡️ `docs/CONTRIBUTING_ADVANCED.md` – Forking, local development, validation tools  
- ➡️ `docs/COMPONENT_DESIGN_GUIDE.md` – How to describe the purpose, inputs, outputs, and test strategy of your component  
- ➡️ `docs/WORKFLOW_OVERVIEW.md` – Internal `dev → staging → main` promotion model  

Most contributors can ignore these.

---

## ⭐ Need Help?

If you’re unsure at any point, open a Pull Request and add:

```
@Palo-Cortex/soc-framework-maintainers
```

We’re here to help contributors of all experience levels.
