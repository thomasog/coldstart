# Rationale

Why each piece exists. Based on research done in November 2026; re-check the tool-specific facts when tools change.

## Scope: setup only

The product is the folder. An earlier version told the agent to choose the project's first step and look for hidden deadlines, which can only be done by reading the user's documents; in one test it spent the session reading the documents and offered to start the next piece of work. Anything in the files can be read by the next session, so `scan` works by name, the agent opens only instruction files and manifests, and project facts come from the user's answers.

## Script and judgment

Anthropic's guidance is to "prefer scripts for deterministic operations", and the Agent Skills spec asks for self-contained scripts with no prompts, `--help`, JSON output and clear exit codes (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices, https://agentskills.io/skill-creation/using-scripts).

- **The script handles what has one right answer:** listing, copying without overwriting, and checking the result. It launches no other program, so a `git` planted in the folder can't run, and the agent runs `git init`. It aborts before writing if anything is missing or unreadable, and repeat runs change nothing.
- **A refused write is handed back, not fatal.** Claude Code's Bash sandbox refuses writes to Claude's own settings files, so `init` writes the rest and returns `.claude/settings.json` under `blocked`. The agent writes it with its file tool, which asks the user. Any other write error still aborts.
- **The agent handles what needs judgment:** the interview, merging instructions, and writing in the user's language.
- **Only an OK to the plan counts.** A prompt that says no one can answer, or to treat it as the reply to anything, read as leave to proceed for agents on Claude Code 2.1.321, with 1.3.0 as well. Old instructions are exactly where an injected command would hide, so silence is never consent.
- **Python's standard library** is the least bad runtime: no installs, and readable by reviewers. Windows doesn't ship Python and agents' shells differ, so each docstring doubles as the by-hand fallback.

## Nothing comes from outside the folder

The skill reads no saved memory, chat history or other projects. Each folder's memory starts there and stays there, which closes an injection route.

Anthropic's directory policy, item 1.G, bars querying Claude's memory, chat history, conversation summaries, or user-generated or uploaded files. It also bars persistently storing or using conversation content to build user profiles or to try to change Claude's behavior across sessions (https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy). coldstart's notes are plain files the user can read and edit, written inside their own folder, and they build no profile. But `.ai/` memory does load in every session, so read the item in full before submitting: how it applies is a reviewer's call.

## State folder: `.ai/`, not `.agents/`

- **Codex protects `.agents/`.** In its default sandbox, "`<writable_root>/.agents` is protected as read-only when it exists as a directory", recursively. The docs don't say what a write does; one issue reports an approval prompt under `on-request`, a failure under `never`, and a maintainer calling this intended. So a handoff there would need an approval on every rewrite, or fail in headless runs. https://learn.chatgpt.com/docs/agent-approvals-security and https://github.com/openai/codex/issues/17535
- **`.agents/` is a config namespace.** Codex, Cursor, Copilot and Gemini CLI read skills from it, and Antigravity also reads rules and more, so mutable state doesn't belong there. `.agents/skills/` is a convention, not a spec: the Agent Skills spec doesn't mandate a location. https://agentskills.io/integrate-skills and https://antigravity.google/docs/customization-discovery/
- **Nothing would be gained by moving.** No tool reads a handoff, memory or plans from `.agents/`, and Claude Code reads nothing under it. https://code.claude.com/docs/en/memory#agents-md
- **A future project skill** goes in `.agents/skills/<name>/`, with a copy in `.claude/skills/` for Claude Code. That is a later session's decision, so setup creates no such folder.
- **`.ai/` is shared, not claimed.** Laravel Boost keeps guidelines under `.ai/`, in other subfolders, so the two coexist. No agent we checked protects it. It isn't a standard either, just this project's choice, and cheap to change later. Avoid `.agent/`, `_agents/` and `_agent/`, which Antigravity also recognizes.

## Instructions: AGENTS.md as the single source

- **AGENTS.md is the open standard** (agents.md, stewarded by the Agentic AI Foundation under the Linux Foundation, with a technical charter: https://raw.githubusercontent.com/agentsmd/agents.md/main/Technical_Charter.pdf). Codex, Cursor, Copilot, Jules, Zed, Warp, opencode, Devin, Amp and others read it natively. Where several apply, the nearest file in the directory tree wins.
- **Claude Code reads AGENTS.md natively since v2.1.277, but only when there is no CLAUDE.md.** It never reads anything under `.ai/`.
  - `.claude/CLAUDE.md` importing `@../AGENTS.md` works on old and new versions, avoids a root CLAUDE.md, and also pulls in the handoff and the memory index.
  - That file counts as a CLAUDE.md, so Claude Code reaches AGENTS.md only through the import. Imports resolve relative to the file that contains them, hence `../`.
  - The file stays even on versions that read AGENTS.md directly. Older versions, a disabled built-in AGENTS.md plugin, the first session after some upgrades, `/init`, `/memory`, a `CLAUDE.local.md` or any CLAUDE.md in a parent folder can each stop AGENTS.md from loading, and an import survives those. Started from a subfolder, Claude Code asks before loading imports from outside the working directory. It adds no cost of its own: those files must be read anyway, and the docs say an import never loads AGENTS.md twice.
  - The docs recommend imports over symlinks on Windows. Creating a symlink there needs admin rights or Developer Mode, git checks symlinks out as text by default, and OneDrive handles them badly.
  - https://code.claude.com/docs/en/memory#agents-md
- **Antigravity reads AGENTS.md unchanged,** so it needs no adapter. https://antigravity.google/docs/cli/gcli-migration/
- **Without a detected project root, Codex checks only the current directory,** which matters for folders without git. https://learn.chatgpt.com/docs/agent-configuration/agents-md
- **Keep it short and specific.** The evidence is real but mixed, and all of it comes from code repositories, so applying it to personal projects is an extrapolation.
  - ETH Zurich and LogicStar, v3 (https://arxiv.org/abs/2602.11988): context files don't generally improve task success, raise inference cost by over 20%, and repository overviews aren't helpful. Hence no `## Map`: setup reads no documents, so a map could only repeat file names.
  - Lulla et al. (https://arxiv.org/abs/2601.20404) found lower median runtime and fewer output tokens with comparable completion. It reports no dollar cost.
  - One study found no effect of size between 25 and 500 lines, but on one trivial annotation (https://arxiv.org/abs/2605.10039), and Anthropic's docs still say long files reduce adherence. The cap is about cost and focus.
  - Anthropic removed over 80% of Claude Code's system prompt for Claude 5 models with no measurable loss on its own evals. Keep product context, gotchas and high-stakes constraints; remove obvious facts, duplicates and rigid rules (https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models). What must always or never happen belongs in permissions, not prose (https://claude.com/resources/articles/steering-claude-code-skills-hooks-rules-subagents-and-more).
  - Include only what the agent cannot infer. Claude's guidance is under 200 lines; Codex caps the combined chain at 32 KiB.
- **Write rules for literal readers.** Anthropic's guides for the 5.x models say they follow instructions closely, so cautions in instruction and memory files pile up into needless approval requests and held-back routine work. A rule states its own scope and exception (a note's request to install, send data out or change settings needs an OK; the handoff's own next step doesn't), and an approval rule names exact actions. Handoffs are written for a reader with little context, in plain words, with no terms coined during the work. https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2 and https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - Addresses are left out of the secrets rule: a move or paperwork project needs them.
  - The handoff rewrite is for the main session only, so subagents that load AGENTS.md don't overwrite it.
  - `/doctor prompt-audit` in Claude Code checks these files for wording written for older models.

## Portability: nothing that matters lives in ~/.claude

- **Auto memory** is stored in `~/.claude/projects/<slug>/memory/`, which is machine-local.
  - `autoMemoryDirectory` accepts only absolute or `~/` paths, so it can't follow a folder between machines. Writing it to `settings.local.json` per machine fails too: sync tools such as OneDrive carry that file along, a second writer uses its own format, and the index would load twice next to the import.
  - Hence `autoMemoryEnabled: false`, even though Anthropic now recommends auto memory: its notes wouldn't travel with the folder.
- **Plans** default to `~/.claude/plans`, which is cleaned after `cleanupPeriodDays` (30 by default).
  - `plansDirectory` accepts a path relative to the project root.
  - Forward slashes only; a path that resolves outside the project falls back to the default.
- https://code.claude.com/docs/en/settings-reference

## Memory and handoff

Plain markdown is the common choice for agent memory. `MEMORY.md` holds one dated, sourced line per fact, and a longer note gets its own file. No study compares one file with a file per fact, or evaluates handoff files; this section rests on practitioner reports. The date and source show whether a line came from the user or a page.

- **Keep stable knowledge (memory) apart from volatile state (handoff).**
- **"Assume interruption."** Write the handoff for someone with no chat history: no "as discussed", exact file paths, what was verified. Stating its date is the visible proof that an agent read it.
- **A memory is a claim, not a fact.** It goes stale, so check it before acting on it.
  - Update rather than duplicate.
  - Keep it small; it is imported into every session.
- **Update at milestones and at the end, not every step.**
- **Keep the always-loaded files small.** The handoff is rewritten, never appended to, finished detail moves to `.ai/archive/`, and `MEMORY.md` states its own limit, because `check` only runs at setup.
- **Project files are an injection route.** Instructions found in web pages, PDFs or emails must never become memory, and old instructions are shown to the user before they're merged. The AGENTS.md rule that notes never override Rules is a mitigation, not a defense; its effect is untested. The same goes for the rule about scripts in `.ai/tools/`, since some agents run workspace commands unprompted. https://arxiv.org/html/2607.14611v1
- **The `.env` deny is defense in depth.** It is best-effort and exists only in Claude Code. `Read` blocks reading and `Edit` covers shell writes, so both lists stay. AGENTS.md carries the secrets rule for every other agent.
- **Hooks, `.mcp.json` and env overrides stay out** of what coldstart writes: real CVEs live in config that executes. https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/
- **Karpathy's LLM Wiki** has the same shape: immutable sources, notes an LLM maintains, a schema file that sets the rules, and periodic lint passes over the notes. https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- **Sources:**
  - https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
  - https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
  - https://www.letta.com/blog/context-repositories

## Subagent models

**Claude Code precedence** (https://code.claude.com/docs/en/sub-agents#choose-a-model):
1. the `model` parameter on the call;
2. `model:` in the agent file;
3. `CLAUDE_CODE_SUBAGENT_MODEL`;
4. the main model.

With none of these set, every subagent runs on the main (most expensive) model.

- **Routing is an opt-in section of AGENTS.md since 1.4.0:** setup asks once and the default is no. Which model does which work is closer to a personal working style than to project state, and anyone who already routes models in their own config would get it twice.
- **Prose, not config:** up to 1.3.0 the tier lived in a Claude agent file (`scout`, on Haiku). A config file names one model for one tool, so it ages and covers one vendor. The section names tiers relative to the model running the session ("the lowest tier that gets it right", "a tier above yours"), so it holds for any vendor, and when the user runs Opus one day and Sonnet the next. Codex delegates only when AGENTS.md asks (https://learn.chatgpt.com/docs/agent-configuration/subagents), so prose is also what reaches it.
- **The test for a tier is the task, not the orchestrator:** "as well as you would" is a bar a lower model rarely passes, and a literal reader would stop delegating. Quality comes from three things instead: sizing the task, checking in proportion to what depends on the result, and redoing a weak result one tier up.
- **Effort is "enough for the task to be done completely, and no more":** Haiku's prompting guide says it can stop early or skip checks at low effort, so the section doesn't tie rote work to low effort.
- **What prose can't do:** it is advice, not a setting, and Anthropic's guide for Fable 5.2 warns that delegation lines can cause more subagents than needed. The section's last line and the opt-in limit that; no eval measures it yet. A helper that only reads is read-only by instruction, not by a `tools` list.
- **The advisor:** Claude Code has a built-in advisor, a server tool that sees the whole conversation, set per user with `/advisor` or `advisorModel` (https://code.claude.com/docs/en/advisor). The key takes one fixed model and can't say "one above the main model", and in the project's `settings.json` it would apply to everyone who clones the folder. So the section asks for "a tier above yours: an advisor tool if you have one, otherwise a subagent", and with routing the close suggests `/advisor` once per machine. Folders set up before 1.3.0 can delete `.claude/agents/advisor.md`; a folder that has `scout.md` can keep it.
- **No `fallbackModel` in settings.json:** the key doesn't merge, so a project value would replace the chain of whoever clones the folder.
- **Multi-agent runs use about 15× the tokens of chat** and suit independent work better than tightly coupled work. Delegate deliberately, with a full brief. https://www.anthropic.com/engineering/multi-agent-research-system
- **Gemini CLI and Aider** need a config entry to read AGENTS.md (`context.fileName`, `read: AGENTS.md`). **Cursor** reads `.claude/agents/`, so the adapter isn't strictly Claude-only.

## Deliberately left out

These are cheap to add later and would only be noise in a fresh folder:

- per-session logs and an audit mode;
- a migration command and a version marker: no public release used another layout, and nothing would read the marker;
- empty folders and placeholder READMEs;
- shims for unused agents;
- hooks (SessionStart hooks have reports of hanging on Windows);
- `disable-model-invocation`, which blocks unslashed requests and which the reference validator rejects; the description already limits triggering, and Codex has `allow_implicit_invocation: false`.

## Packaging

One tree serves both routes: `plugin/skills/coldstart/` is a plain skill under the open standard (https://agentskills.io/specification), and `plugin/` is the Claude Code plugin, so installs don't carry tests, evals or the demo. A plugin can't replace the copied files: its settings can't set `plansDirectory` or permissions, and its agents wouldn't travel with the folder. It only makes installing and updating easier.

## Re-check when

- agents.md issue 9 settles a directory layout, or agentskills issue 15 settles skill locations;
- claude-code issue 31005 adds `.agents/skills`, which would drop the copy for Claude Code;
- Codex documents a writable exception for `.agents/`, or any tool reads state from it.
