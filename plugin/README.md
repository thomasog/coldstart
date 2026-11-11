# coldstart

Get any folder ready for AI agents, once. coldstart sets up a code repo or a personal project so the next agent can pick up where the last one stopped, on any machine, with no lock-in to one agent.

It lists the folder, asks a few questions, shows you the plan and waits for your OK, writes the files below, and stops. It doesn't open your documents or start the project's work.

- `AGENTS.md`: instructions any agent can read.
- `.ai/HANDOFF.md` and `.ai/memory/`: where you stopped and durable facts, in plain files inside the folder.
- `.claude/`: a small adapter, only if you use Claude Code.
- `.gitignore`: only if the folder is or will be in git.

## Install

```bash
claude plugin marketplace add thomasog/coldstart
claude plugin install coldstart@thomasog-plugins
```

## Use

Ask for it by name, for example `/coldstart`. It never starts on its own. In a folder that is already set up, it only checks the files and stops.

Setup asks once whether you want model routing; the default is no. A yes adds a short `Delegation` section to `AGENTS.md` and writes no settings.

## What it reads, writes and runs

It reads file names and agent instruction and config files inside the folder, checks only whether a parent folder is a git repository, writes only the files above, and runs `skills/coldstart/scripts/coldstart.py`, which launches no other program and makes no network calls.

In Claude Code, `.claude/settings.json` turns off auto memory for that folder, keeps plans in `.ai/plans/`, and denies Claude's own Read and Edit tools access to `.env` files. Anything Claude had already saved for the folder stays where it is and is no longer loaded there. With the Bash sandbox on, the agent writes that file itself and Claude Code asks you first.

Folders set up before 1.4.0 can delete `.claude/agents/scout.md`, and before 1.3.0 also `.claude/agents/advisor.md`; nothing is removed for you.

There are no hooks and no telemetry. Full details: https://github.com/thomasog/coldstart#what-it-reads-writes-and-runs

## License

MIT. Source and documentation: https://github.com/thomasog/coldstart

[Privacy](PRIVACY.md)
