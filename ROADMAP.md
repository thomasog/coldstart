# Roadmap

## Now: model routing is an opt-in section of AGENTS.md (1.4.0)

coldstart exists so that instructions, the handoff and memory travel with a folder. Which model does which work, and when to ask a stronger one, is closer to a personal working style, so setup asks once and the default is no.

A yes adds a `Delegation` section to `AGENTS.md`. It names tiers relative to the model running the session and no model by name, so it doesn't age and works in any agent. The `scout` agent file and every routing setting are gone from the folder.

## Next: measure it

- An eval that runs a task with and without the section and compares the result and the cost: does it delegate the right work, and does it delegate too much? Anthropic's guide for Fable 5.2 warns of the second.
- A run by hand in Codex, Gemini CLI and Cursor.

## Later: a home outside the folder

For people who want the same routing in every project, the folder is the wrong place. The notes below are for that.

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

## Other agents

Codex has no built-in advisor; a request for one is open and unanswered (https://github.com/openai/codex/issues/36837). It starts subagents only when asked or when `AGENTS.md` requests delegation, which the `Delegation` section does.
