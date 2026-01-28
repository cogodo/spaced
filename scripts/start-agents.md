# Starting Multiple Claude Code Agents

## Quick Start

Open 2 terminal tabs/windows. In each, run:

```bash
cd /Users/colingordon/flutter_projects/spaced/spaced
claude
```

## Agent Prompts

### Agent 1 - Paste this:
```
You are Agent-1. Read AGENTS.md and TASKS.md.

Claim one task from TASKS.md by:
1. Run: ./scripts/agent-start.sh <task-name>
2. Read the spec file thoroughly
3. Implement the feature incrementally
4. Run ./scripts/agent-test.sh after changes
5. Stop at checkpoints and ask me to review

Start by showing me which task you're claiming.
```

### Agent 2 - Paste this:
```
You are Agent-2. Read AGENTS.md and TASKS.md.

Claim a DIFFERENT task from TASKS.md (not the one Agent-1 took) by:
1. Run: ./scripts/agent-start.sh <task-name>
2. Read the spec file thoroughly
3. Implement the feature incrementally
4. Run ./scripts/agent-test.sh after changes
5. Stop at checkpoints and ask me to review

Start by showing me which task you're claiming.
```

## Your Workflow

1. **Monitor both agents** - Switch between tabs
2. **Review checkpoints** - When agent says "🔔 CHECKPOINT", review and approve/redirect
3. **Run local tests** - `./run-local.sh` to test manually
4. **Approve PRs** - When agent creates PR, review it
5. **Assign reviewer** - Have the other agent review with `./scripts/agent-review.sh <pr>`

## Tips

- Agents work independently on separate branches
- They'll ask for review at key points - don't ignore these
- If an agent goes off track, just tell it to stop and redirect
- Keep TASKS.md updated so agents don't conflict
