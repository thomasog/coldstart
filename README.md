<div align="center">

![coldstart icon](assets/icon.png)

# coldstart

**Get any folder ready for AI agents, once.**<br>
The next agent picks up where the last one stopped, on any machine.

[![CI](https://github.com/thomasog/coldstart/actions/workflows/ci.yml/badge.svg)](https://github.com/thomasog/coldstart/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/thomasog/coldstart)](https://github.com/thomasog/coldstart/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

![Animation of a folder of loose files. An agent runs coldstart, AGENTS.md and a .ai folder appear beside the unchanged files, and a later session resumes from the handoff.](assets/demo.gif)

<sub>An illustration of a typical run, not a screen recording.</sub>

</div>

## Why

- **No lock-in.** Your instructions and memory don't belong to one agent. Switch agents and keep working.
- **It all lives in the folder.** Nothing important is trapped in an account or in an app's hidden data.
- **It travels.** Copy, sync or zip the folder, and the context goes with it.
- **It lasts.** Plain text you can still read years from now, with no special tool.

## What it does

Run coldstart in a code repo or in a personal project such as a move, a trip or paperwork. It lists the folder, asks a few questions, writes the files below, and stops. It doesn't open your documents or start the project's work; that belongs to the next session.

```
<project>/
├── AGENTS.md              # instructions any agent can read
├── .ai/
│   ├── HANDOFF.md         # where we stopped and what comes next
│   └── memory/
│       └── MEMORY.md      # index of durable facts
├── .gitignore             # only if you want git
└── .claude/               # only if you use Claude Code
    ├── CLAUDE.md          # imports AGENTS.md, the handoff and the memory index
    ├── settings.json      # keeps plans and memory inside the folder
    └── agents/
        ├── scout.md       # fast and cheap: search, read, bulk vision
        └── advisor.md     # strong second opinion for hard calls
```

Later, agents keep what they make for themselves in `.ai/` too: plans, reusable scripts, archives and scratch work.

The habit that makes it work: agents read `.ai/HANDOFF.md` at the start of a session and rewrite it at the end.

## Works with

| Agent | Status |
|---|---|
| Claude Code | Tested |
| Codex | Tested |
| Cursor, Copilot, Antigravity | Read `AGENTS.md` according to their documentation; not yet run |

## Install

Paste this into your agent:

```text
Install the agent skill in plugin/skills/coldstart from https://github.com/thomasog/coldstart, then tell me how to run it.
```

Or use a command:

```bash
npx skills add thomasog/coldstart
```

```bash
gh skill install thomasog/coldstart coldstart --agent codex --scope user
```

**Claude Code plugin:**

```bash
claude plugin marketplace add thomasog/coldstart
```

```bash
claude plugin install coldstart@thomasog-plugins
```

**By hand:** copy `plugin/skills/coldstart/` to `~/.agents/skills/`, or to `~/.claude/skills/` for Claude Code.

Python 3.10 or later makes the setup faster, and git is optional. Without Python, the agent does the same steps by hand.

## Use

Ask for it by name: `/coldstart` in Claude Code, `$coldstart` in Codex, or "run coldstart" anywhere. It never starts on its own. In a folder that is already set up, it only checks the files and stops.

If you don't use git, start your agent from the folder itself, so it finds `AGENTS.md`.

## What it reads, writes and runs

- **Reads:** file names, agent instruction files such as `CLAUDE.md`, and project manifests such as `package.json`. Nothing outside the folder.
- **Writes:** the files above, and nothing else. It moves an old root `CLAUDE.md` or `AGENTS.override.md` to `.ai/archive/` instead of deleting it, and shows you any command, URL or install step in old instructions first.
- **Runs:** `coldstart.py`, a short Python script that uses only the standard library, makes no network calls and asks no questions. It runs `git init` only if you ask for git.
- **Changes in Claude Code:** `.claude/settings.json` turns off auto memory for that folder, keeps plans in `.ai/plans/`, and denies Claude's own Read and Edit tools access to `.env` files. Anything Claude had already saved for the folder stays in `~/.claude` and is no longer loaded there; copy what you want by hand.

There are no hooks and no telemetry.

## Why not something else?

- **`/init`** writes an instruction file for a code repo. It doesn't set up a handoff or memory, and it isn't meant for personal folders.
- **Cowork Projects** are a good fit if you stay in Cowork. Their state lives in your account, not in the folder.
- **project-butler and project-continuity** give coding agents an ongoing memory workflow. coldstart runs once, works outside code too, and leaves plain files with nothing else to keep running.

## Evidence

The [`evals/`](evals/) folder holds five fictional cases, including a folder with a deadline in a filename. In one run per case on Claude Code, all 29 checks pass. An earlier version without these limits failed every check on that folder: it opened the documents and started the project's work.

`python -m unittest discover -s tests` runs the script's tests. The reasoning behind each choice is in [`rationale.md`](plugin/skills/coldstart/references/rationale.md).

## License

[MIT](LICENSE)
