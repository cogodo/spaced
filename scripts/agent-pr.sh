#!/bin/bash
set -e

# Create a PR for the current branch
# Usage: ./scripts/agent-pr.sh "PR title"

TITLE=$1

if [ -z "$TITLE" ]; then
    echo "Usage: ./scripts/agent-pr.sh \"PR title\""
    exit 1
fi

BRANCH=$(git branch --show-current)

if [ "$BRANCH" = "main" ]; then
    echo "Error: Cannot create PR from main branch"
    exit 1
fi

echo "=== Creating PR ==="

# Push branch
git push -u origin "$BRANCH"

# Create PR
gh pr create --title "$TITLE" --body "$(cat <<EOF
## Summary
Automated PR from agent working on $BRANCH

## Checklist
- [ ] Tests pass
- [ ] Human reviewed checkpoints
- [ ] Ready for final review

---
🤖 Created by Claude Code agent
EOF
)"

echo ""
echo "✓ PR created"
gh pr view --web
