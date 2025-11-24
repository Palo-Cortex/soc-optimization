# Editing Multiple Files in One Branch (GitHub Web GUI)

Most contributors will use the **GitHub Web interface**.  
This guide explains how to make **changes to more than one file** while staying in a **single branch**, without using Git or local tools.

---

## ⭐ Step 1 — Create Your Branch

1. Open **any file** you plan to change  
2. Click **✏️ Edit**  
3. GitHub will prompt you to create a branch  
4. Name your branch using this format:
   ```
   <type>/<area>-<short-description>
   ```
5. Click **Create branch and start editing**  
6. Make your first change and click **Commit changes**  
7. Make sure the option:
   ```
   Commit directly to the <your-branch-name> branch
   ```
   is selected

Your branch is now created, and your first edit is saved.

---

## ⭐ Step 2 — Edit Additional Files in the Same Branch

To edit another file:

1. Navigate to the next file you want to update  
2. Click **✏️ Edit**  
3. Make your changes  
4. Scroll down and click **Commit changes**  
5. Again, confirm **Commit directly to the <your-branch-name> branch**

Repeat this process for each file you want to update.

➡️ **Do NOT create a new branch for each file.**  
All related changes should stay in the same branch.

---

## ⭐ Step 3 — Open a Pull Request

When all your file changes are complete:

1. Click the **Pull requests** tab  
2. GitHub will show a banner such as:  
   **“You recently pushed branches…”**
3. Click **Compare & pull request**  
4. Add a short description of what you changed  
5. Tag the maintainers:
   ```
   @Palo-Cortex/soc-framework-maintainers
   ```
6. Submit the PR

---

## ⭐ Summary

- Create **one branch** for your set of changes  
- Edit as many files as needed  
- Commit all changes **directly to the same branch**  
- Then open a **single PR**  
- Maintainers will review and merge everything together

This workflow keeps contributions clean and easy to review.
