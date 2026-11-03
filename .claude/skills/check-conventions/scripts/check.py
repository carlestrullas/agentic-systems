#!/usr/bin/env python3
"""
Check the agentic-systems repo against its conventions and fix the mechanical drift.

Usage (from anywhere inside the repo):
    python3 .claude/skills/check-conventions/scripts/check.py          # report only
    python3 .claude/skills/check-conventions/scripts/check.py --fix    # report, fix, re-check
    python3 .claude/skills/check-conventions/scripts/check.py --json   # machine-readable

Each problem is printed as one line:
    [FIXED]  something the script repaired itself
    [TODO]   needs an edit that takes judgment (Claude does it, see SKILL.md)
    [ASK]    ambiguous or risky: needs the user's decision

Conventions checked (they come from the framework README, e.g. crew_ai/README.md):
  shared-file   llm.py identical in every example of a framework; knowledge_setup.py
                identical in every example that has one
  files         every example has README.md, .env.example, requirements.txt or pyproject.toml
  readme        example README has Setup, Run and "Ideas to extend it" sections and
                links to the framework README's "Choosing the model"
  env           every variable the code reads is listed in .env.example; no real-looking
                secrets in .env.example (placeholders must be REPLACE_ME)
  git           no .env or output/ files are tracked
  learning-path every example folder has a row in the framework's learning path, and
                every row points to a folder that exists
  root-count    the example count for each framework in the root README is right
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

SHARED_FILES = ("llm.py", "knowledge_setup.py")
PLACEHOLDER = "REPLACE_ME"
REQUIRED_SECTIONS = ("Setup", "Run", "Ideas to extend it")
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "output", "node_modules", ".claude"}

# Variables read by the code: os.getenv("X"), os.environ["X"], os.environ.get("X"), is_set("X")
ENV_READ = re.compile(
    r"""(?:getenv|environ\.get|environ\.setdefault|is_set)\(\s*["']([A-Z][A-Z0-9_]*)["']"""
    r"""|environ\[\s*["']([A-Z][A-Z0-9_]*)["']\s*\]"""
)
# Variables the code sets itself rather than reading from .env
INTERNAL_VARS = {"CREWAI_STORAGE_DIR"}
SECRET_NAME = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD)$")


@dataclass
class Problem:
    check: str
    status: str  # FIXED | TODO | ASK
    path: str
    message: str
    hint: str = ""


@dataclass
class Report:
    problems: list[Problem] = field(default_factory=list)

    def add(self, check, status, path, message, hint=""):
        self.problems.append(Problem(check, status, str(path), message, hint))


# ── helpers ──────────────────────────────────────────────────────────────────


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    if out.returncode != 0:
        raise SystemExit("Run this inside the agentic-systems git repository.")
    return Path(out.stdout.strip())


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True
    ).stdout


def digest(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def frameworks(root: Path) -> list[Path]:
    """Top-level folders whose README has a learning path table."""
    found = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and d.name not in SKIP_DIRS and not d.name.startswith("."):
            readme = d / "README.md"
            if readme.exists() and "## Learning path" in readme.read_text():
                found.append(d)
    return found


def is_example(d: Path) -> bool:
    return any((d / f).exists() for f in ("README.md", "requirements.txt", "pyproject.toml", ".env.example"))


def examples(framework: Path) -> list[Path]:
    """Direct children that look like examples, plus nested ones (e.g. flows/poem_flow)."""
    out = []
    for d in sorted(framework.iterdir()):
        if not d.is_dir() or d.name in SKIP_DIRS or d.name.startswith("."):
            continue
        if is_example(d):
            out.append(d)
            for sub in sorted(d.iterdir()):
                if sub.is_dir() and sub.name not in SKIP_DIRS and (sub / "pyproject.toml").exists():
                    out.append(sub)
    return out


def top_level_examples(framework: Path) -> list[Path]:
    return [e for e in examples(framework) if e.parent == framework]


def is_project(example: Path) -> bool:
    return (example / "pyproject.toml").exists()


def package_dir(example: Path) -> Path | None:
    src = example / "src"
    if not src.is_dir():
        return None
    pkgs = [p for p in src.iterdir() if p.is_dir() and (p / "__init__.py").exists()]
    return pkgs[0] if len(pkgs) == 1 else None


def code_dir(example: Path) -> Path:
    """Where llm.py & co. live: the package of a CrewAI project, else the example folder."""
    return (package_dir(example) or example) if is_project(example) else example


def python_files(example: Path, nested: list[Path]) -> list[Path]:
    files = []
    for p in example.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.relative_to(example).parts):
            continue
        if any(n != example and n in p.parents for n in nested):
            continue  # belongs to a nested example (flows/poem_flow)
        files.append(p)
    return files


def modified_in_worktree(root: Path, path: Path) -> bool:
    """True if the file differs from HEAD (an intentional, not yet propagated edit)."""
    tracked = git(root, "ls-files", "--", rel(root, path)).strip()
    if not tracked:
        # A copy in a brand-new example is usually copied from an older example,
        # possibly stale: never let it override the existing copies.
        return False
    return bool(git(root, "diff", "HEAD", "--name-only", "--", rel(root, path)).strip())


# ── checks ───────────────────────────────────────────────────────────────────


def check_shared_file(root: Path, fw: Path, name: str, fix: bool, report: Report) -> None:
    exs = examples(fw)
    copies = {e: code_dir(e) / name for e in exs}
    present = {e: p for e, p in copies.items() if p.exists()}
    if not present:
        return

    hashes = {e: digest(p) for e, p in present.items()}
    counts = Counter(hashes.values())

    # Which version is the canonical one?
    #  * if some copies were edited in the working tree and all those edits agree,
    #    that edit is the new canonical version (the convention says: change one,
    #    copy it everywhere), so propagate it;
    #  * otherwise the majority version wins;
    #  * a tie, or edits that disagree, is ambiguous: ask.
    edited = {hashes[e] for e, p in present.items() if modified_in_worktree(root, p)}
    canonical = None
    reason = ""
    if len(counts) == 1:
        canonical = next(iter(counts))
    elif len(edited) == 1:
        canonical = next(iter(edited))
        reason = "the version edited in the working tree"
    elif len(edited) > 1:
        report.add(
            "shared-file", "ASK", rel(root, fw),
            f"{name}: {len(edited)} different uncommitted edits in different examples, "
            "so it is unclear which one is the new version",
            "Show the diffs and ask which version to keep, then copy it to every example.",
        )
        return
    else:
        (top, n1), *rest = counts.most_common()
        if rest and rest[0][1] == n1:
            report.add(
                "shared-file", "ASK", rel(root, fw),
                f"{name}: no majority version ({dict(counts)})",
                "Show the diffs and ask which version to keep.",
            )
            return
        canonical, reason = top, f"the version shared by {n1} of {len(present)} examples"

    source = next(p for e, p in present.items() if hashes[e] == canonical)
    for e, p in present.items():
        if hashes[e] != canonical:
            msg = f"differs from {reason} ({rel(root, source)})"
            if fix:
                shutil.copyfile(source, p)
                report.add("shared-file", "FIXED", rel(root, p), msg + "; copied it over")
            else:
                report.add("shared-file", "TODO", rel(root, p), msg, "Run with --fix.")

    # llm.py is required in every example; knowledge_setup.py only where knowledge is used.
    for e, p in copies.items():
        if p.exists():
            continue
        needs = name == "llm.py" or (e / "knowledge").is_dir()
        if not needs:
            continue
        if is_project(e) and package_dir(e) is None:
            report.add("shared-file", "TODO", rel(root, e), f"{name} is missing and src/<package> was not found",
                       f"Copy {rel(root, source)} into the example's package.")
            continue
        if fix:
            shutil.copyfile(source, p)
            report.add("shared-file", "FIXED", rel(root, p), f"{name} was missing; copied {reason or 'the shared version'}")
        else:
            report.add("shared-file", "TODO", rel(root, p), f"{name} is missing", "Run with --fix.")


def check_files(root: Path, fw: Path, report: Report) -> None:
    for e in examples(fw):
        for f in ("README.md", ".env.example"):
            if not (e / f).exists():
                report.add("files", "TODO", rel(root, e / f), "missing",
                           "Write it following the other examples (see SKILL.md).")
        if not ((e / "requirements.txt").exists() or (e / "pyproject.toml").exists()):
            report.add("files", "TODO", rel(root, e), "has neither requirements.txt nor pyproject.toml",
                       "List the packages its imports need.")


def check_readme(root: Path, fw: Path, report: Report) -> None:
    for e in examples(fw):
        readme = e / "README.md"
        if not readme.exists():
            continue
        text = readme.read_text()
        headings = {h.strip() for h in re.findall(r"^## (.+)$", text, re.M)}
        for s in REQUIRED_SECTIONS:
            if s not in headings:
                report.add("readme", "TODO", rel(root, readme), f'missing the "## {s}" section')
        if "README.md#choosing-the-model" not in text:
            depth = len(e.relative_to(fw).parts)
            report.add("readme", "TODO", rel(root, readme),
                       "Setup does not link to the framework's model instructions",
                       f"Link to {'../' * depth}README.md#choosing-the-model in the Setup section.")


def env_example_vars(path: Path) -> dict[str, list[tuple[int, str, bool]]]:
    """VAR -> [(line number, value, commented out)]."""
    out: dict[str, list[tuple[int, str, bool]]] = {}
    for i, line in enumerate(path.read_text().splitlines(), 1):
        m = re.match(r"^\s*(#\s*)?([A-Z][A-Z0-9_]*)=(.*)$", line)
        if m:
            out.setdefault(m.group(2), []).append((i, m.group(3).strip(), bool(m.group(1))))
    return out


def check_env(root: Path, fw: Path, fix: bool, report: Report) -> None:
    exs = examples(fw)
    for e in exs:
        env = e / ".env.example"
        if not env.exists():
            continue
        listed = env_example_vars(env)

        read: dict[str, str] = {}
        for py in python_files(e, exs):
            if py.name in SHARED_FILES:
                continue  # llm.py reads every provider key; only the active one is needed
            for m in ENV_READ.finditer(py.read_text()):
                var = m.group(1) or m.group(2)
                if var not in INTERNAL_VARS:
                    read.setdefault(var, rel(root, py))
        for var in ("MODEL", "OLLAMA_BASE_URL"):
            read.setdefault(var, "llm.py")
        if (code_dir(e) / "knowledge_setup.py").exists():
            read.setdefault("EMBEDDER", "knowledge_setup.py")

        for var, where in sorted(read.items()):
            if var not in listed:
                report.add("env", "TODO", rel(root, env), f"{var} is read by {where} but is not listed",
                           f"Add a commented section with {var}={PLACEHOLDER} (or its default) explaining what it is for.")

        # Real-looking secrets: secret-named variables must hold the placeholder (or nothing).
        lines = env.read_text().splitlines(keepends=True)
        changed = False
        for var, entries in listed.items():
            if not SECRET_NAME.search(var):
                continue
            for lineno, value, commented in entries:
                if value in ("", PLACEHOLDER):
                    continue
                msg = f"line {lineno}: {var} holds a real-looking value instead of {PLACEHOLDER}"
                hint = "If this was a real key, it is in the git history: rotate it with the provider."
                if fix:
                    prefix = "# " if commented else ""
                    lines[lineno - 1] = f"{prefix}{var}={PLACEHOLDER}\n"
                    changed = True
                    report.add("env", "FIXED", rel(root, env), msg + "; replaced it", hint)
                else:
                    report.add("env", "TODO", rel(root, env), msg, hint)
        if changed:
            env.write_text("".join(lines))


def check_git(root: Path, report: Report) -> None:
    for f in git(root, "ls-files").splitlines():
        parts = Path(f).parts
        if Path(f).name == ".env":
            report.add("git", "TODO", f, "a .env file is committed",
                       "Untrack it with `git rm --cached` (the file stays on disk) and tell the user to "
                       "rotate any real key it holds: it is in the git history.")
        elif "output" in parts[:-1]:
            report.add("git", "TODO", f, "a generated output/ file is committed",
                       "Untrack it with `git rm --cached` (the file stays on disk).")


def learning_path_rows(readme: Path) -> list[tuple[int, str, str]]:
    """(line number, folder name, link target) for every row of the learning path table."""
    rows, inside = [], False
    for i, line in enumerate(readme.read_text().splitlines(), 1):
        if line.startswith("## "):
            inside = line.strip() == "## Learning path"
            continue
        if inside and line.startswith("|"):
            m = re.search(r"\[`?([^`\]]+)`?\]\(([^)]+)\)", line)
            if m:
                rows.append((i, m.group(1), m.group(2)))
    return rows


def check_learning_path(root: Path, fw: Path, report: Report) -> None:
    readme = fw / "README.md"
    rows = learning_path_rows(readme)
    linked = set()
    for lineno, name, target in rows:
        folder = (fw / target).resolve()
        linked.add(folder)
        if not folder.is_dir():
            report.add("learning-path", "TODO", rel(root, readme),
                       f"line {lineno}: row `{name}` links to {target}, which does not exist",
                       "Fix the link if the folder was renamed; remove the row (and renumber) if it was deleted.")
        elif folder.name != name:
            report.add("learning-path", "TODO", rel(root, readme),
                       f"line {lineno}: row is labelled `{name}` but links to {target}")
    for e in top_level_examples(fw):
        if e.resolve() not in linked:
            report.add("learning-path", "TODO", rel(root, readme),
                       f"example `{e.name}` has no row in the learning path",
                       "Add a row (number, link, agents, what it introduces) from the example's README; "
                       "add a Core concepts row too if it introduces a new idea.")


def check_root_count(root: Path, fw: Path, fix: bool, report: Report) -> None:
    readme = root / "README.md"
    if not readme.exists():
        return
    text = readme.read_text()
    pattern = re.compile(rf"^(\|\s*\[[^\]]+\]\({re.escape(fw.name)}/?\)\s*\|\s*)(\d+)(\s*\|)", re.M)
    m = pattern.search(text)
    actual = len(learning_path_rows(fw / "README.md")) or len(top_level_examples(fw))
    if not m:
        report.add("root-count", "TODO", "README.md", f"no row for the `{fw.name}` framework in the Frameworks table")
        return
    if int(m.group(2)) != actual:
        msg = f"says {fw.name} has {m.group(2)} examples, its learning path has {actual}"
        hint = "Also check that the 'What they cover' cell mentions any new topic."
        if fix:
            readme.write_text(pattern.sub(lambda mm: f"{mm.group(1)}{actual}{mm.group(3)}", text, count=1))
            report.add("root-count", "FIXED", "README.md", msg + "; updated the number", hint)
        else:
            report.add("root-count", "TODO", "README.md", msg, "Run with --fix.")


# ── main ─────────────────────────────────────────────────────────────────────


def run(root: Path, fix: bool) -> Report:
    report = Report()
    fws = frameworks(root)
    if not fws:
        report.add("files", "ASK", ".", "no framework folder with a '## Learning path' README was found")
    for fw in fws:
        for name in SHARED_FILES:
            check_shared_file(root, fw, name, fix, report)
        check_files(root, fw, report)
        check_readme(root, fw, report)
        check_env(root, fw, fix, report)
        # The learning path first, so the root count reflects the table as it is now.
        check_learning_path(root, fw, report)
        check_root_count(root, fw, fix, report)
    check_git(root, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--fix", action="store_true", help="apply the mechanical fixes")
    parser.add_argument("--json", action="store_true", help="print the problems as JSON")
    parser.add_argument("--root", type=Path, help="repository root (default: git toplevel)")
    args = parser.parse_args()

    root = (args.root or repo_root()).resolve()
    report = run(root, args.fix)

    if args.json:
        print(json.dumps([asdict(p) for p in report.problems], indent=2))
    else:
        if not report.problems:
            print("✅ No convention problems found.")
        for p in report.problems:
            print(f"[{p.status}] {p.check}: {p.path}: {p.message}")
            if p.hint:
                print(f"         → {p.hint}")
        counts = Counter(p.status for p in report.problems)
        if report.problems:
            print("\n" + ", ".join(f"{n} {s}" for s, n in sorted(counts.items())))
    sys.exit(1 if any(p.status != "FIXED" for p in report.problems) else 0)


if __name__ == "__main__":
    main()
