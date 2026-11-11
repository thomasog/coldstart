# Running the evals

Each folder here is one case for `claude plugin eval`: a prompt, an optional `place-files.sh` that builds the starting folder, and graders. All data is fictional.

## Where they run

- **macOS:** yes. The sandbox is built in.
- **Linux and WSL2:** yes, with `bubblewrap` and `socat` installed.
- **Windows without WSL2:** no. The cases need the Bash tool, and the runner refuses to grant it without a sandbox. A refused run still prints `score 1.00` for cases whose graders check that something did not happen, so ignore any Windows result.

## Known limit: `.claude/settings.json`

The Bash sandbox refuses the script's write to `.claude/settings.json`, so `init` hands that file back under `blocked`. The runner works in don't-ask mode and refuses the agent's Write as well; on 2.1.321 neither `Write(.claude/settings.json)` nor `Edit(.claude/settings.json)` in `--allow-tools` lets it through. Every case that uses the Claude Code adapter therefore ends with that file missing, and `check-passes`, `exactly-the-planned-files` and `no-advisor-setting` fail there for that reason alone. In an interactive session the Write asks the user instead.

## Steps on a Mac

1. Have Claude Code installed and signed in (`claude --version`; these cases were written on 2.1.318), and `python3` on the PATH.
2. Get the branch to test:
   ```bash
   git fetch origin && git checkout release-1.4.0 && git pull
   ```
3. Run the script's own tests first; they take a few seconds and cost nothing:
   ```bash
   python3 -m unittest discover -s tests
   ```
4. Run the evals from the repository root:
   ```bash
   claude plugin eval . --scaffold --ablation none --allow-tools Bash Write Edit
   ```
   - It asks once to trust the plugin folder; answer yes.
   - Each case runs 3 times, so expect 27 runs and roughly 20 to 40 minutes. It uses your plan or API credits; add `--max-cost-usd 15` for a hard ceiling.
   - To run one case, add `--case routing-accepted`.
5. Read the table it prints. Every case should show `PASS% 100`. The `NOTES` column must be empty: a note that starts with `exit 1` means the run never happened.

## What to bring back

- The table from the terminal, pasted as text.
- For any case under 100%, the grader lines printed above the table for that case (they start with `✗`).
- The result folder is `evals/results/<timestamp>/`; git ignores it. `report.html` in it has the full detail if a failure needs a closer look.

## What changed in 1.4.0

Three cases cover the new routing question:

- `routing-accepted` (new): a yes keeps the `Delegation` section in `AGENTS.md`, with no model named, no agent file and no advisor setting.
- `empty-personal-folder`: a no leaves 5 files and no `Delegation` section.
- `codex-only-user`: a prompt that doesn't mention routing gets no `Delegation` section.

No case measures yet whether the section makes an agent delegate well; that is the next item in `ROADMAP.md`.
