# Roadmap

## Next: model routing leaves the folder

coldstart exists so that instructions, the handoff and memory travel with a folder. Which model does which work, at what effort, and when to ask a stronger model for advice is a personal working style: it is the same in every folder, it belongs to one person, and it changes with each model generation. A folder set up once is never rewritten, so anything of that kind written into it goes stale there.

So in the next version the folder carries project truth only: `AGENTS.md`, `.ai/`, the Claude Code import adapter and the portability settings. Two things that 1.3.0 still ships come out:

- `.claude/agents/scout.md`;
- the closing line that suggests `/advisor`.

1.3.0 deliberately adds nothing more of this kind and writes no personal or global setting.

## Where the working style can live instead

Researched on 2026-11-11 against the Claude Code docs. Re-check before building.

- **Per machine, not synced by Anthropic:** `~/.claude/CLAUDE.md`, `~/.claude/settings.json` and `~/.claude/agents/`. https://code.claude.com/docs/en/settings
- **Synced through the claude.ai account:** skills and plugins turned on for the account load on every machine where the user signs in, and a synced plugin's subagents load too. A small separate plugin could carry the subagents. https://code.claude.com/docs/en/plugins/loading
- **Mechanisms that need no prose:**
  - `CLAUDE_CODE_SUBAGENT_MODEL` sets the default model for subagents that have none assigned. https://code.claude.com/docs/en/env-vars
  - An agent file sets `model` and `effort`, and its description is how Claude decides to delegate. https://code.claude.com/docs/en/sub-agents
  - `advisorModel`, set by `/advisor`, turns on the built-in advisor, which Claude calls on its own when stuck. https://code.claude.com/docs/en/advisor
- **What does need prose:** having the main session pick `model` and `effort` per call. The per-call effort needs Claude Code v2.1.292 or later.
- **Overriding the style in one project:**
  - Settings have a fixed order: `.claude/settings.local.json`, then `.claude/settings.json`, then the user file.
  - CLAUDE.md files are concatenated, user first and project last, and none overrides another. When two conflict, Claude may follow either, so a project exception has to be written as an explicit exception. https://code.claude.com/docs/en/memory

## To verify before building

- How a personal plugin gets turned on for a claude.ai account.
- Whether `CLAUDE_CODE_SUBAGENT_MODEL` reaches the built-in Explore agent.
- Whether a project agent overrides a user or plugin agent of the same name.
- How to tell users of folders that already have `scout.md` to remove it, since `init` never overwrites.
- Whether a line telling the main session to delegate changes behavior for the better. Anthropic's guide for Fable 5.2 warns that such lines can cause more subagents than needed, so measure it with an eval first.

## Other agents

Codex has no built-in advisor. A request for one is open and unanswered (https://github.com/openai/codex/issues/36837). Its custom agents pin a versioned model ID, which would age in a folder. Nothing for coldstart to write until that changes.
