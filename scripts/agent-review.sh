#!/bin/bash
set -e

# Review a PR
# Usage: ./scripts/agent-review.sh <pr-number>

PR=$1

if [ -z "$PR" ]; then
    echo "Usage: ./scripts/agent-review.sh <pr-number>"
    exit 1
fi

echo "=== Reviewing PR #$PR ==="

# Fetch PR info
gh pr view "$PR"

echo ""
echo "=== Files Changed ==="
gh pr diff "$PR" --name-only

echo ""
echo "=== Full Diff ==="
gh pr diff "$PR"

echo ""
echo "To approve: gh pr review $PR --approve"
echo "To request changes: gh pr review $PR --request-changes --body 'reason'"
echo "To merge: gh pr merge $PR --squash"
