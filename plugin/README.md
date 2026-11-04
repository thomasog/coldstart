# coldstart

Get any folder ready for AI agents, once. coldstart sets up a code repo or a personal project so the next agent can pick up where the last one stopped, on any machine, with no lock-in to one agent.

It lists the folder, asks a few questions, writes the files below, and stops. It doesn't open your documents or start the project's work.

- `AGENTS.md`: instructions any agent can read.
- `.ai/HANDOFF.md` and `.ai/memory/`: where you stopped and durable facts, in plain files inside the folder.
- `.claude/`: a small adapter, only if you use Claude Code.
- `.gitignore`: only if you ask for git.

## Use

Ask for it by name, for example `/coldstart`. It never starts on its own. In a folder that is already set up, it only checks the files and stops.

## What it reads, writes and runs

- **Reads:** file names, agent instruction files such as `CLAUDE.md`, and project manifests such as `package.json`. Nothing outside the folder.
- **Writes:** the files above. It moves an old root `CLAUDE.md` or `AGENTS.override.md` to `.ai/archive/` instead of deleting it, and shows you any command, URL or install step in old instructions first.
- **Runs:** `skills/coldstart/scripts/coldstart.py`, a short Python script with no dependencies, no network calls and no prompts. It runs `git init` only if you ask for git. Without Python, the agent does the same steps by hand.
- **Changes in Claude Code:** `.claude/settings.json` turns off auto memory for that folder, keeps plans in `.ai/plans/`, and denies Claude's own Read and Edit tools access to `.env` files. Anything Claude had already saved for the folder stays where it is and is no longer loaded there.

There are no hooks and no telemetry.

## License

MIT. Source and documentation: https://github.com/thomasog/coldstart

[Privacy](PRIVACY.md)
