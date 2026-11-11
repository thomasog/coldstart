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

[How it works](#how-it-works) · [Install](#install) · [Use](#use) · [What it touches](#what-it-reads-writes-and-runs) · [Evidence](#evidence)

</div>

## Why

Every agent session starts cold. What the last one learned sits in its chat history, in an app's hidden data or in one person's head. coldstart puts it in the folder instead, where anyone can read it.

- **No lock-in.** Instructions and memory don't belong to one agent. Switch agents and keep working.
- **It all lives in the folder.** Nothing important is trapped in an account or in an app's hidden data.
- **It travels.** Copy, sync or zip the folder, and the context goes with it.
- **It lasts.** Plain text you can still read years from now, with no special tool.

It works for a code repo and just as well for a move, a trip or a year of tax paperwork.

## How it works

You run it once. It takes a few minutes and does five things:

1. **Looks, without reading.** It lists file names and opens only agent instructions and build manifests. Your documents stay closed.
2. **Asks once.** The goal, who is involved, the first task, which agents you use and how to tell the work is done.
3. **Shows the plan and waits.** Every file it will write, plus any command, URL, hook or MCP server found in old instructions, marked keep or drop. Nothing is written before your OK.
4. **Writes a few small files.** Nothing else in the folder changes.
5. **Checks and stops.** It doesn't start the project's work; that belongs to the next session.

The result:

```
<project>/
├── AGENTS.md              # instructions any agent can read
├── .ai/
│   ├── HANDOFF.md         # where we stopped and what comes next
│   └── memory/
│       └── MEMORY.md      # durable facts
├── .gitignore             # only if the folder is or will be in git
└── .claude/               # only if you use Claude Code
    ├── CLAUDE.md          # imports AGENTS.md, the handoff and the memory
    └── settings.json      # keeps plans and memory inside the folder
```

Later, agents keep what they make for themselves in `.ai/` too: plans, reusable scripts, archives and scratch work.

> [!TIP]
> **The one habit that makes it work:** agents read `.ai/HANDOFF.md` at the start of a session and rewrite it at the end. In Claude Code the reading is automatic; other agents follow the instruction in `AGENTS.md`.

## Install

> [!IMPORTANT]
> As with any skill, read [`SKILL.md`](plugin/skills/coldstart/SKILL.md) and [`scripts/`](plugin/skills/coldstart/scripts/) before you install it.

**Claude Code**, as a plugin:

```bash
claude plugin marketplace add thomasog/coldstart
```

```bash
claude plugin install coldstart@thomasog-plugins
```

Update it later with `claude plugin update coldstart@thomasog-plugins`.

**Codex, Cursor, Copilot, Gemini CLI and others**, as a skill:

```bash
npx skills add thomasog/coldstart
```

```bash
gh skill install thomasog/coldstart coldstart --agent codex --scope user
```

**Any agent**, by asking it:

```text
Install the agent skill in plugin/skills/coldstart from https://github.com/thomasog/coldstart, then tell me how to run it.
```

**By hand:** copy `plugin/skills/coldstart/` to `~/.claude/skills/` for Claude Code, `~/.gemini/config/skills/` for Antigravity, or `~/.agents/skills/` for Codex, Cursor, Copilot and Gemini CLI.

Python 3.9 or later makes setup faster, and git is optional. Without Python, the agent does the same steps by hand.

## Use

Ask for it by name. It never starts on its own.

| Agent | Command |
|---|---|
| Claude Code | `/coldstart` |
| Codex | `$coldstart` |
| Anything else | "run coldstart" |

Start your agent from the folder itself, not from a subfolder: without git, Codex finds `AGENTS.md` only there, and Claude Code asks before loading the adapter's imports from a subfolder. In a folder that is already set up, coldstart only checks the files and stops.

### Works with

| Agent | Status |
|---|---|
| Claude Code | Tested |
| Codex | Tested |
| Cursor, Copilot, Antigravity | Read `AGENTS.md` according to their documentation; not yet run |

### Model routing, if you want it

Setup asks once whether you want model routing. The default is no, and then nothing about it is written.

With a yes, `AGENTS.md` gets a short `Delegation` section that tells the agent to:

- give each piece of work to the lowest model tier that gets it right, and choose the effort;
- keep design, trade-offs and anything hard to undo for itself, and check what it delegated;
- redo a weak result one tier up, and ask a tier above its own when it is stuck.

The tiers are relative to whatever model is running, so the same text works with Opus one day and Sonnet the next, and in any agent that reads `AGENTS.md`. It names no model and writes no settings.

It is an instruction, so an agent can ignore it or delegate too much, and no eval measures that yet. Claude Code's built-in advisor sees the whole conversation but can't be turned on from `AGENTS.md`; run `/advisor` once per machine if you want it.

## What it reads, writes and runs

- **Reads:** file names, agent instruction and config files such as `CLAUDE.md` or `.mcp.json`, and build manifests such as `package.json`. It opens no other file, and it only checks whether a parent folder is a git repository.
- **Writes:** the files above, and nothing else. It moves `AGENTS.override.md`, and with Claude Code an old root `CLAUDE.md`, to `.ai/archive/` instead of deleting them.
- **Runs:** `coldstart.py`, a short Python script that uses only the standard library, launches no other program, makes no network calls and asks no questions. The agent runs `git init` if you ask for git.
- **In Claude Code:** `.claude/settings.json` turns off auto memory for that folder, keeps plans in `.ai/plans/`, and denies Claude's own Read and Edit tools access to `.env` files. Anything Claude had already saved for the folder stays in `~/.claude` and is no longer loaded there; copy what you want by hand. With the Bash sandbox on, the script can't write that file, so the agent writes it and Claude Code asks you first.

There are no hooks and no telemetry.

## Upgrading

coldstart never deletes what an earlier version wrote. In folders set up before 1.4.0 you can delete `.claude/agents/scout.md`; before 1.3.0, also `.claude/agents/advisor.md`, since Claude Code's built-in `/advisor` replaces it. See the [changelog](CHANGELOG.md) for everything else.

## Why not something else?

- **`/init`** writes an instruction file for a code repo. It doesn't set up a handoff or memory, and it isn't meant for personal folders.
- **Cowork Projects** are a good fit if you stay in Cowork. Their instructions and memory stay in the desktop app on one computer, not in the folder.
- **project-butler and project-continuity** give coding agents an ongoing memory workflow. coldstart runs once, works outside code too, and leaves plain files with nothing else to keep running.

## Evidence

The script has its own tests:

```bash
python -m unittest discover -s tests
```

The [`evals/`](evals/) folder holds fictional cases for `claude plugin eval`, among them a folder with a deadline in a filename and one with hostile old instructions. They need macOS, Linux or WSL2 and use your plan or API credits; [`evals/README.md`](evals/README.md) has the steps and the known limits.

```bash
claude plugin eval . --scaffold --ablation none --allow-tools Bash Write Edit --judge-model sonnet
```

**Last result, 1.4.0:** all 9 cases pass in 27 of 27 runs on Claude Code 2.1.321, and a run by hand in Codex sets up a folder and stops before writing when old instructions are hostile. Each release's result is in the [changelog](CHANGELOG.md).

The reasoning behind each choice is in [`rationale.md`](plugin/skills/coldstart/references/rationale.md), and what comes next is in the [roadmap](ROADMAP.md).

## License

[MIT](LICENSE)
