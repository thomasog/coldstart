#!/usr/bin/env bash
set -eu
mkdir -p .ai/memory

cat > AGENTS.md <<'EOF'
# Trip

Trip to Chile in March, done when back home.

## Session
- **Start:** read `.ai/HANDOFF.md` and state its date.
EOF

cat > .ai/HANDOFF.md <<'EOF'
# Handoff
_Updated: 2026-10-01_

## Next
1. Book the hotel in Santiago.
EOF

cat > .ai/memory/MEMORY.md <<'EOF'
# Memory

- 2026-10-01 Preferred hotel is near the metro (the user)
EOF

cat > itinerary.txt <<'EOF'
Fictional itinerary.
EOF
