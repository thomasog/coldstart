# coldstart

Get any folder ready for AI agents, once. coldstart sets up a code repo or a personal project so the next agent can pick up where the last one stopped, on any machine, with no lock-in to one agent.

It lists the folder, asks a few questions, writes the files below, and stops. It doesn't open your documents or start the project's work.

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

## What it reads, writes and runs

It reads file names and agent instruction and config files inside the folder, checks only whether a parent folder is a git repository, writes only the files above, and runs `skills/coldstart/scripts/coldstart.py`, which launches no other program and makes no network calls.

In Claude Code, `.claude/settings.json` turns off auto memory for that folder, keeps plans in `.ai/plans/`, and denies Claude's own Read and Edit tools access to `.env` files. Anything Claude had already saved for the folder stays where it is and is no longer loaded there. Folders set up before 1.3.0 can delete `.claude/agents/advisor.md`; Claude Code's built-in advisor replaces it.

If you say yes to model routing during setup, it also writes helper agents on cheaper models and turns on a stronger advisor. For agents other than Claude Code, the agent opens that tool's official documentation page on the web to get the current format and models. The default is no.

There are no hooks and no telemetry. Full details: https://github.com/thomasog/coldstart#what-it-reads-writes-and-runs

## License

MIT. Source and documentation: https://github.com/thomasog/coldstart

[Privacy](PRIVACY.md)
