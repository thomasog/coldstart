#!/usr/bin/env bash
set -eu
mkdir -p src test

cat > CLAUDE.md <<'EOF'
# mini-calc

- Pure functions in src/.
- No new dependencies without asking.
- Function names in camelCase.
EOF

cat > package.json <<'EOF'
{
  "name": "mini-calc",
  "version": "1.0.0",
  "scripts": {
    "test": "node --test",
    "lint": "eslint src"
  }
}
EOF

cat > src/index.js <<'EOF'
exports.add = (a, b) => a - b;
EOF

cat > test/index.test.js <<'EOF'
const t=require('node:test');const a=require('node:assert');const {add}=require('../src/index.js');
t.test('add',()=>a.equal(add(2,2),4));
EOF
