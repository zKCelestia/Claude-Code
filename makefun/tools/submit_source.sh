#!/usr/bin/env bash
# Verify and submit a make.fun entry as a source bundle (steps 5 and 6 of the workflow).
# Bundles this session's transcripts, runs the kit's offline checks, submits signed by the
# agent keypair, then waits until the server has checked and scored it. An entry that fails
# a check is NOT left counting silently: the script prints every failed check and its fix.
#
# Usage: makefun/tools/submit_source.sh <slug> <repo-dir> "<title>"
# Env:   MAKEFUN_HOME   folder holding the unpacked <slug>-kit and makefun-keypair.json (default ~/makefun)
#        SESSION_LOG    this session's Claude Code log (default: the newest under ~/.claude/projects)
set -euo pipefail
slug="$1"; repo="$2"; title="$3"
home="${MAKEFUN_HOME:-$HOME/makefun}"
kit="$home/$slug-kit"
keypair="$home/makefun-keypair.json"
session="${SESSION_LOG:-$(ls -t "$HOME"/.claude/projects/*/*.jsonl | head -1)}"
out="$home/$slug-transcripts.tar.gz"

[ -d "$kit" ] || (cd "$home" && curl -sSL "https://make.fun/c/$slug/kit" | tar xz)
cd "$kit"
echo "== bundle (session $session)"
node cli/makefun.mjs bundle --repo "$repo" --session "$session" --no-discover \
  --mcp github=https://mcp-proxy.anthropic.com --mcp claude-code-remote=builtin \
  --context "$HOME/Claude-Code/CLAUDE.md" --context "$HOME/Claude-Code/.claude/skills/makefun-workflow/SKILL.md" \
  --effort default --notes "Built in a claude.ai cloud Claude Code session." --out "$out" | grep -E "wrote|missing"
echo "== check"
node cli/makefun.mjs check --kit . --repo "$repo" --transcripts "$out" | grep -E "^fail|passed|ok:"
echo "== submit"
node cli/makefun.mjs submit --competition "$slug" --source "$repo" --commit "$(git -C "$repo" rev-parse HEAD)" \
  --title "$title" --bundle "$out" --keypair "$keypair" > "$home/submit-$slug.log" 2>&1
grep -E "accepted|refused" "$home/submit-$slug.log"
id=$(grep -oE "submission [0-9a-f-]{36}" "$home/submit-$slug.log" | head -1 | cut -d' ' -f2)
[ -n "$id" ] || { grep -A20 refused "$home/submit-$slug.log"; exit 1; }
echo "== waiting for $id"
key=$(node -e 'const c=JSON.parse(require("fs").readFileSync(process.env.HOME+"/.makefun/credentials","utf8"));process.stdout.write(c.keys["https://make.fun"].key)')
for _ in $(seq 1 40); do
  stage=$(node cli/makefun.mjs status --submission "$id" --json | node -e 'const d=(j=>j.data??j)(JSON.parse(require("fs").readFileSync(0,"utf8")));console.log(d.stage)')
  [ "$stage" = scored ] || [ "$stage" = rejected ] && break
  curl -sS -m 55 "https://make.fun/api/agents/me/events?wait=50&until=entry:$id:leaves:$stage" -H "x-api-key: $key" -o /dev/null || true
done
echo "stage: $stage"
node cli/makefun.mjs status --submission "$id" | grep -E "^  fail|provisional rate" -A1 || true
