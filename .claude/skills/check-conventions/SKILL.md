---
name: check-conventions
description: Checks the agentic-systems repo against its own conventions and fixes any drift. Conventions covered include identical llm.py and knowledge_setup.py copies, the required files in each example, the README sections, .env.example coverage and placeholders, no tracked .env or output files, learning-path rows and the root README example counts. Use this whenever the user asks whether the repo is consistent, wants a sanity or convention check, or is about to commit. Also use it after they add, rename or delete an example, change llm.py or knowledge_setup.py in any example, add an environment variable or API key, or say something like "did I forget anything?". Use it even if they never say "conventions".
model: sonnet
---

# Check the repo's conventions

This repo is a set of self-contained teaching examples, and it stays readable only while every example follows the same rules. Those rules are written in each framework README (for example, `crew_ai/README.md` → *Conventions*). Most of them are easy to break by accident. Someone edits `llm.py` in one example and forgets the other 13 copies, or adds a folder and never adds its learning-path row. This skill finds that drift and fixes it.

The user wants drift **fixed, not just reported**. Fix everything you can derive from the repo itself. Then tell them clearly what changed and what still needs their eyes.

## 1. Run the checker with `--fix`

From the repo root:

```bash
python3 .claude/skills/check-conventions/scripts/check.py --fix
```

The script fixes the mechanical problems and prints one line per problem:

- `[FIXED]`: the script already repaired it (shared-file sync, a missing `llm.py`, a real-looking key replaced with `REPLACE_ME`, the root README count).
- `[TODO]`: needs an edit that takes judgment. Do these yourself (section 2).
- `[ASK]`: it can't tell what the right answer is. Ask the user (section 3).

Use the script rather than re-checking by hand. It already knows the details: which `llm.py` copy is canonical, where CrewAI projects keep their code (`src/<package>/`), and which variables are set internally and not read from `.env`.

**How it picks the canonical shared file.** If some copies of `llm.py` were edited in the working tree and all those edits agree, the edit is treated as the new version and copied everywhere. That is what the convention asks for ("when you change it, copy it to all of them"). Otherwise the majority version wins. Mention in your summary which version was propagated, because overwriting someone's edit with the old version would be the worst failure here.

## 2. Fix the TODOs

Base every fix on what is already in the repo. Read the example's code and README and copy the style of the neighbouring examples. Don't invent features or facts.

| Problem | How to fix it |
|---|---|
| Example has no learning-path row | Read the example's README and code. Add a row at the end of the table in the framework README with the next number, `` [`name`](name/) ``, the agent count in the same notation as the other rows (`1`, `2`, `1 + 3`, `–` for concept scripts) and *Introduces*: only the concepts it adds over earlier rows. If it introduces a new CrewAI concept, also add a *Core concepts* row. Then run the script again so the root count updates. |
| Row points to a missing folder | If the folder was renamed (look for a folder with a similar name, or check `git status`), fix the link and label. If it was deleted, remove the row and renumber the rows below it. |
| Variable read by the code but missing from `.env.example` | Add it at the end of `.env.example` as a section in the file's style: a `# ── Title ───` comment line, one or two lines saying what it is for and where to get a key, then `VAR=REPLACE_ME` for secrets or the default value for settings. Say whether it is optional, based on how the code reacts when it is unset. |
| README missing `Setup`, `Run` or `Ideas to extend it` | Write the section from the code: Setup lists only example-specific steps and links to the framework README's *Choosing the model* (the script gives the relative path). Run shows the real commands and flags from `main.py`/argparse. Ideas gives 3–5 concrete extensions. Copy the tone and length of a sibling example. |
| Missing `README.md`, `.env.example` or requirements | Write it from the code and the sibling examples. Use `.env.example` from another example as the template, and build requirements from the imports. |
| Tracked `.env` or `output/` file | `git rm --cached <path>`. This untracks the file but keeps it on disk, and `.gitignore` already covers it. For `.env`, tell the user to **rotate** any real key in it, because it stays in the git history. |
| Real-looking key replaced in `.env.example` | Already fixed by the script. Still tell the user to rotate that key if it was real. |

When you are done, run the script once more **without** `--fix`. It should report no problems, or only the `[ASK]` items you are leaving for the user.

## 3. ASK items

Show the user the conflicting versions (`git diff`, or `diff` between two copies) and ask which one to keep. Once they decide, copy that version into every example and re-run. Don't guess: picking the wrong `llm.py` silently throws away someone's work.

## 4. Report

Keep it short. Use three groups and leave out any that are empty:

- **Fixed:** one line per fix, naming the files.
- **Please review:** anything you wrote rather than copied (learning-path text, new README sections, new `.env.example` entries), so the user can check the wording. Include any key that needs rotating, in bold.
- **Needs your decision:** the ASK items.

Don't commit, unless the user asks you to. Leave the changes in the working tree so they can review them first.
