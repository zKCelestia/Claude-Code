# Make.fun Superpower — Universal Agent Skill

**Version:** 1.0.0  
**Format:** Agent-neutral skill package  
**Primary file:** `SKILL.md`

This package equips a general-purpose AI agent to research, build, validate, submit, monitor, and improve Make.fun bounty entries. It is **not designed for Muse.ai specifically** and does not depend on chat names, Muse workspaces, Muse tools, or a particular agent runtime.

## What is included

- `SKILL.md` — the main operating instructions and decision framework.
- `UNIVERSAL_AGENT_PROMPT.md` — a portable bootstrap prompt for agents that cannot load skill folders natively.
- `references/` — detailed playbooks for operations, leaderboard interpretation, validation, permissions, and continuity.
- `templates/` — reusable state, intake, leaderboard, readiness, and postmortem templates.
- `examples/` — anonymized historical case studies illustrating how to turn leaderboard evidence into decisions.

## How to use

### Agents with a skills system
Install or copy this folder into the agent's skill directory using that platform's documented convention. Make `SKILL.md` discoverable. The exact installation path differs by agent.

### Agents without a skills system
1. Open `UNIVERSAL_AGENT_PROMPT.md`.
2. Paste it into the agent's project/system instructions.
3. Provide this folder or its contents as reference files.
4. Start a task by giving the agent a bounty URL, competition ID, repository, or current project state.

### Recommended project layout

Keep each bounty isolated in its own project folder or worktree. Do not rely on separate chat threads as the only source of continuity.

```text
makefun-workspace/
  shared/
    OPERATING_RULES.md
    portfolio-dashboard.md
  bounty-a/
    BOUNTY-STATE.md
    DECISIONS.md
    EVIDENCE/
    source/
    experiments/
    reports/
  bounty-b/
    BOUNTY-STATE.md
    DECISIONS.md
    EVIDENCE/
    source/
    experiments/
    reports/
```

## Important

- This skill does not include API keys, wallet secrets, private keys, claim codes, or account credentials.
- Read-only audit is the default. External submissions, resubmissions, claims, purchases, deployments, destructive actions, and other irreversible actions require explicit authorization from the operator.
- Platform APIs, CLI commands, scoring rules, and bounty requirements can change. Verify the current official documentation and live competition state before acting.
- Historical case studies are examples, not current leaderboard data or promises of future results.
