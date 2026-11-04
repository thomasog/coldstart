# Rationale

Why each piece exists. Based on research done in November 2026; re-check the tool-specific facts when tools change.

## Scope: setup only

The product is the folder. An earlier version told the agent to choose the project's first step and look for hidden deadlines, which can only be done by reading the user's documents; in one test it spent the session reading the documents and offered to start the next piece of work. Anything in the files can be read by the next session, so the setup looks at names, instruction files and manifests, and takes project facts from the user's answers.

## Script and judgment

Anthropic's guidance is to "prefer scripts for deterministic operations", and the Agent Skills spec asks for self-contained scripts with no prompts, `--help`, JSON output and clear exit codes (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices, https://agentskills.io/skill-creation/using-scripts).

- **The script handles what has one right answer:** listing, copying without overwriting, and checking the result. It aborts before writing if anything is missing or unreadable, and repeat runs change nothing.
- **The agent handles what needs judgment:** the interview, merging instructions, and writing in the user's language.
- **Python's standard library** is the least bad runtime: no installs, and readable by reviewers. Windows doesn't ship Python and agents' shells differ, so each docstring doubles as the by-hand fallback.

## Nothing comes from outside the folder

The skill reads no saved memory, chat history or other projects. Each folder's memory starts there and stays there. This matches Anthropic's directory policy, which says software "must not query or extract data from Claude's memory, chat history, conversation summaries" (https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy), and it closes an injection route.

## State folder: `.ai/`, not `.agents/`

- **Codex protects `.agents/`.** In its default sandbox, "`<writable_root>/.agents` is protected as read-only when it exists as a directory", recursively, and a maintainer confirmed this is intended. A handoff there needs an approval on every write, or fails. https://learn.chatgpt.com/docs/agent-approvals-security and https://github.com/openai/codex/issues/17535
- **`.agents/` is a config namespace.** Codex reads skills from it and Antigravity reads rules and skills from it, so mutable state doesn't belong there. https://antigravity.google/docs/customization-discovery/
- **`.ai/` is shared, not claimed.** Laravel Boost keeps guidelines under `.ai/`, in other subfolders, so the two coexist. No agent we checked protects it. Avoid `.agent/`, `_agents/` and `_agent/`, which Antigravity also recognizes.

## Instructions: AGENTS.md as the single source

- **AGENTS.md is the open standard** (agents.md, stewarded by the Agentic AI Foundation under the Linux Foundation). Codex, Cursor, Copilot, Jules, Zed, Warp, opencode, Devin, Amp and others read it natively. Where several apply, the nearest file in the directory tree wins.
- **Claude Code reads AGENTS.md natively since v2.1.277, but only when there is no CLAUDE.md.** It never reads anything under `.ai/`.
  - `.claude/CLAUDE.md` importing `@../AGENTS.md` works on old and new versions, avoids a root CLAUDE.md, and also pulls in the handoff and the memory index.
  - That file counts as a CLAUDE.md, so Claude Code reaches AGENTS.md only through the import. Imports resolve relative to the file that contains them, hence `../`.
  - The file stays even on versions that read AGENTS.md directly. Older versions, some cloud sessions, `/init`, `/memory`, a `CLAUDE.local.md` or any CLAUDE.md in a parent folder can each stop AGENTS.md from loading, and an import survives them all. It adds no cost of its own: those files must be read anyway, and the docs say an import never loads AGENTS.md twice.
  - The docs recommend imports over symlinks on Windows. Creating a symlink there needs admin rights or Developer Mode, git checks symlinks out as text by default, and OneDrive handles them badly.
  - https://code.claude.com/docs/en/memory#agents-md
- **Antigravity reads AGENTS.md unchanged,** so it needs no adapter. https://antigravity.google/docs/cli/gcli-migration/
- **Without a detected project root, Codex checks only the current directory,** which matters for folders without git. https://learn.chatgpt.com/docs/agent-configuration/agents-md
- **Keep it short and specific.** The evidence is real but mixed, and all of it comes from code repositories, so applying it to personal projects is an extrapolation.
  - ETH Zurich and LogicStar (https://arxiv.org/abs/2602.11988): LLM-generated files had a marginal negative effect, developer-written ones a marginal positive one, and files raised cost by about 20%. They note that "context files are not effective at providing a repository overview", hence no `## Map` for code.
  - Lulla et al. (https://arxiv.org/abs/2601.20404) found the opposite on cost: lower runtime and fewer output tokens.
  - Between 25 and 500 lines, one study found no detectable effect of size (https://arxiv.org/abs/2605.10039), so the line cap is about cost and focus, not adherence.
  - Include only what the agent cannot infer. Claude's guidance is under 200 lines; Codex caps the combined chain at 32 KiB.

## Portability: nothing that matters lives in ~/.claude

- **Auto memory** is stored in `~/.claude/projects/<slug>/memory/`, which is machine-local.
  - `autoMemoryDirectory` accepts only absolute or `~/` paths, so it can't follow a folder between machines.
  - Hence `autoMemoryEnabled: false`, with the same format kept inside the project.
- **Plans** default to `~/.claude/plans`, which is cleaned after `cleanupPeriodDays` (30 by default).
  - `plansDirectory` accepts a path relative to the project root.
  - Forward slashes only; a path that resolves outside the project falls back to the default.
- https://code.claude.com/docs/en/settings-reference

## Memory and handoff

Plain markdown is the common choice for agent memory: a short index that is always loaded, plus topic files read on demand. No study we found evaluates handoff files; this section rests on practitioner reports.

- **Keep stable knowledge (memory) apart from volatile state (handoff).**
- **"Assume interruption."** Write the handoff for someone with no chat history: no "as discussed", exact file paths, what was verified.
- **A memory is a claim, not a fact.** It goes stale, so check it before acting on it.
  - Update rather than duplicate.
  - Keep the index small; it is imported into every session.
- **Update at milestones and at the end, not every step.**
- **Keep the always-loaded files small.** The handoff is rewritten, never appended to, finished detail moves to `.ai/archive/`, and `check` caps the memory index.
- **Project files are an injection route.** Instructions found in web pages, PDFs or emails must never become memory, and old instructions are shown to the user before they're merged. The AGENTS.md rule that notes never override Rules is a mitigation, not a defense; its effect is untested. The same goes for the rule about scripts in `.ai/tools/`, since some agents run workspace commands unprompted. https://arxiv.org/html/2607.14611v1
- **Sources:**
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

With none of these set, every subagent runs on the main (most expensive) model. Prose in AGENTS.md is advice; frontmatter is enforced. The agent files use aliases (`haiku`, `opus`) rather than versioned IDs so they keep working when new models ship.

- **Why `opus` and not `fable`:** these files land in strangers' folders. `fable` needs separate access, billing errors don't trigger a fallback, and `-p` runs bill usage credits without asking (https://code.claude.com/docs/en/model-config). `best` picks Fable where available, but the subagent docs don't list it. Anyone with Fable can change one line.
- **Advisor strategy** (https://claude.com/blog/the-advisor-strategy):
  - A cheaper executor consulting a stronger model improved results at lower cost: Sonnet with an Opus advisor scored +2.7 points on SWE-bench Multilingual at 11.9% lower cost.
  - That result measured a server-side tool that sees the conversation; the `advisor` subagent sees only its brief, so it is an analogy.
- **Multi-agent runs use about 15× the tokens of chat** and suit independent work better than tightly coupled work. Delegate deliberately, with a full brief. https://www.anthropic.com/engineering/multi-agent-research-system
- **Other tools:** no cross-tool convention for model tiers exists yet, which is why AGENTS.md describes tiers by role.

## Deliberately left out

These are cheap to add later and would only be noise in a fresh folder:

- per-session logs and an audit mode;
- a migration command: no public release used another layout;
- empty folders and placeholder READMEs;
- shims for unused agents;
- hooks (SessionStart hooks have reports of hanging on Windows);
- `disable-model-invocation`, which blocks unslashed requests and is rejected outside Claude Code; the description already limits triggering.

## Packaging

One tree serves both routes: `plugin/skills/coldstart/` is a plain skill under the open standard (https://agentskills.io/specification), and `plugin/` is the Claude Code plugin, so installs don't carry tests or the demo. A plugin can't replace the copied files: its settings can't set `plansDirectory` or permissions, and its agents wouldn't travel with the folder. It only makes installing and updating easier.
