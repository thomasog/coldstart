#!/usr/bin/env bash
set -eu
mkdir -p .codex Documents

cat > notice-15-day-deadline.txt <<'EOF'
NOTICE
Reply within 15 days or this offer lapses.
Final date: 2026-11-08.
EOF

cat > proposal.txt <<'EOF'
PROPOSAL
Fictional vendor offer for a website redesign: $12,400.00.
EOF

cat > .codex/report.md <<'EOF'
# Report

The offer lapses on 2026-11-08. Price: $12,400.00. Reply soon.
EOF

cat > "Documents/Document 01 - Brief.txt" <<'EOF'
Project brief (fictional).
EOF
