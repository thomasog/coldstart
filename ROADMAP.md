# Roadmap

## Now: model routing is opt-in (1.4.0)

coldstart exists so that instructions, the handoff and memory travel with a folder. Which model does which work, and when to ask a stronger model for advice, is closer to a personal working style: it is much the same in every folder and it changes with each model generation.

So since 1.4.0 setup asks once, and the default is no. A yes writes config only: helper agents with a model and effort, and the advisor setting. No delegation prose goes into `AGENTS.md`.

Not tested yet:

- The path for Codex, Gemini CLI, Cursor and Copilot, which writes agent files from each tool's official page at setup. Run it by hand in each tool, then add an eval if one can run without the network.
- Whether the three helpers change results for the better. Measure with an eval before adding anything more.

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
- Whether a line telling the main session to delegate changes behavior for the better. Anthropic's guide for Fable 5.2 warns that such lines can cause more subagents than needed, so measure it with an eval first.

## Other agents

Codex has no built-in advisor. A request for one is open and unanswered (https://github.com/openai/codex/issues/36837), so there the advisor is a custom agent, and Codex starts custom agents only when asked. Its agent files and Gemini CLI's pin a versioned model name, which is why coldstart writes them at setup and records the name in memory.
