---
name: flop-hermes-devnet
description: Use for FLOP devnet Hermes setup and readiness checks.
license: Apache-2.0
metadata:
  hermes:
    version: 0.3.8
    author: FLOP Labs
    platforms: [macos, linux, windows]
    tags: [flop, hermes, hermes-desktop, devnet, inference]
---

# Run Hermes on the public FLOP devnet

Use this skill to configure Hermes CLI or Desktop with the public FLOP model
provider. Public launcher 0.4.11 bundles Python provider `flop-public` 0.1.6.
It needs Node.js 22+, curl, Git and the qualified Hermes 0.22.2 release, including
Desktop when requested. Newer Hermes releases are not independently qualified.
The FLOP installer installs the launcher, not Hermes or Desktop. Node 22+ is the
FLOP launcher's floor. The pinned Desktop source requires
`^22.22.0 || ^24.11.0 || >=26.0.0`; its managed builder supplies locked Node 26.7.0.
Do not interpret the launcher floor as Desktop build compatibility.

This native model provider is separate from the TypeScript
`@flop-labs/hermes-plugin` tool bundle. Installing that tool bundle does not select
FLOP as Hermes's model provider. Public setup needs no FLOP repository access,
npm credentials, private-network access or OAuth. Never ask for keys or seed phrases in chat.

## Configure

Run commands locally as the intended user. Preserve the same `HERMES_HOME` for
all plugin, authentication, config, model and Desktop commands, including in later
shells. Do not import the user's existing Hermes configuration.

For a fresh Linux installation, install the pinned official Hermes source first:

Prepare `ca-certificates`, `curl`, `git`, `xz-utils` and `libatomic1` on minimal
Debian hosts. The pinned Linux Desktop CI additionally uses `libgtk-3-0`,
`libnotify4`, `libnss3`, `libxss1`, `libxtst6`, `xdg-utils`, `libatspi2.0-0`,
`libdrm2`, `libgbm1` and `libasound2t64`; package names vary by distribution.
`xvfb` is needed for a headless GUI check, not a normal graphical session.
Prepare the platform prerequisites before wallet enrollment.

```sh
test ! -e "$HOME/hermes-agent"
git clone --filter=blob:none https://github.com/NousResearch/hermes-agent.git "$HOME/hermes-agent"
git -C "$HOME/hermes-agent" checkout --detach d923a5eb487a17c0a68801bba9ef0f56c81040a8
cd "$HOME/hermes-agent"
bash scripts/install.sh --commit d923a5eb487a17c0a68801bba9ef0f56c81040a8 \
  --dir "$HOME/hermes-agent" --non-interactive --skip-browser --skip-computer-use
export PATH="$HOME/hermes-agent/.hermes/bin:$HOME/.local/bin:$PATH"
hermes --version
hermes desktop --build-only
cd "$HOME"
```

Use the official managed installer; do not assemble its dependency environment
with bare pip. For this release, Linux Desktop is built locally from that public
source, rather than downloaded as a Linux app. Its platform prerequisites and
build procedure are in the pinned official
[Desktop guide](https://github.com/NousResearch/hermes-agent/blob/d923a5eb487a17c0a68801bba9ef0f56c81040a8/apps/desktop/BUILDING.md).
On macOS or Windows, use the official platform installation and verify the same
qualified version. Do not count an existing checkout, cached runtime or copied
wallet/profile as a fresh installation.

Start the fresh terminal conversation from a workspace outside the Hermes
installation checkout. Returning home above keeps Desktop from choosing that
checkout as its working directory.

```sh
curl -fsSL https://flop.network/releases/cli/0.4.11/install.sh | sh -s -- --version 0.4.11
export PATH="$HOME/.local/bin:$PATH"
flop --network devnet hermes desktop --doctor
install -d -m 700 "$HOME/.flop"
export HERMES_HOME="$HOME/.flop/hermes-native"
hermes pm repair
flop hermes plugin install
hermes auth add flop-public
hermes model
```

`hermes pm repair` prepares the managed dependency runtime for the new isolated
home; it creates no FLOP wallet and requests no funding. This ordering was
qualified with the official managed Hermes 0.22.2 installation on Linux. Changing
`HERMES_HOME` without preparing that home's runtime can otherwise fail with
“no dependency environment committed; run hermes pm repair”.

Missing `libatomic1` causes a `libatomic.so.1` loader failure. Use your system's
normal package setup elsewhere; the Debian package names above are not universal.

The `install -d` command prepares your local private `.flop` directory before
Hermes probes its version, including when reusing an existing directory. Provider
0.1.6 supports admitted unloaded models and allows one hour for loading, calibration allowance, proof and settlement.
The 2026-10-23 H100 cold-load trial passed real native Desktop tool use and two
positive finalized payments. A fresh installation and any candidate interactive
session mode require their own acceptance; H200 fleet qualification remains pending.

Read https://flop.network/releases/cli/0.4.11/release.json for the pinned source and
archive checksum. The installer preserves an existing full CLI; resolve an existing
command conflict explicitly. `--doctor` is read-only and submits no inference.
Plugin installation uses the release's local pinned Git source, Hermes's standard
security scan and enabled-state readback; it creates no wallet or funding request.
Stop if installation, readiness or catalog checks fail.

Authentication may create a devnet wallet, request faucet funding and sign wallet
enrollment. Do this only when the user intends that setup and enrollment is open.
The wallet and shared public cache remain owner-only local files under `~/.flop`.
Choose **FLOP Public Devnet** and an exact offered model in `hermes model`.
Before opening Desktop, keep the same `HERMES_HOME` and apply these settings on
every setup or reconnect, even if this profile already exists. Then open a fresh
conversation; do not resume a conversation created with older settings:

```sh
hermes config set providers.flop-public.request_timeout_seconds 3900
hermes config set providers.flop-public.stale_timeout_seconds 3900
hermes config set nous.guest false
hermes config set agent.max_turns 3
hermes config set agent.run_budget_seconds 10800
hermes config set agent.reasoning_effort none
hermes config set agent.coding_context off
hermes config set agent.disabled_toolsets '["project", "desktop_ui"]'
hermes config set agent.tool_use_enforcement false
hermes config set agent.execution_guidance false
hermes config set agent.task_completion_guidance false
hermes config set agent.parallel_tool_call_guidance false
hermes config set agent.environment_probe false
hermes config set agent.bot_mode_protocol false
hermes config set tools.tool_search.enabled off
hermes config set platform_toolsets.cli '["terminal"]'
hermes config set platform_toolsets.tui '["terminal"]'
hermes config set platform_toolsets.desktop '["terminal"]'
hermes config set memory.memory_enabled false
hermes config set memory.user_profile_enabled false
hermes config set compression.enabled false
hermes config set auxiliary.title_generation.enabled false
hermes config set auxiliary.title_generation.model_upgrade_enabled false
hermes desktop
```

If Desktop was already open, close and reopen it after CLI authentication and
model selection. For the bounded terminal test, stop the first-run welcome run
before choosing **Skip setup**, then open a new blank conversation. Skipping an
active welcome run can otherwise make an extra model request.

Start a fresh conversation after changing these settings. This limits terminal
work to three turns and a 10,800-second run budget; each provider request keeps
its separate one-hour deadline. In that Desktop conversation, open
the effort menu and turn **Thinking** off. Confirm the control reads **Off** and
your model appears under **FLOP Public Devnet** before sending a message.
The settings above disable auxiliary model calls and optional prompt guidance,
matching the qualified terminal trial. `nous.guest false` prevents the upstream
first-run flow from creating an alternate Nous guest/trial in this FLOP profile.
These settings do not disable payment or proof checks.
Provider requests independently enforce 512 output tokens and a 1,000-FLOP cap.
One run can make multiple requests. Default full-tool runs remain unqualified.

The native sequence above is the recommended public route. The alternate hosted
launcher creates its own key/model-specific custom-provider home and is not
qualified as a one-step launch on a fresh managed installation. Its supported
`--configure-only --json` option returns an absolute `profile`; that home must
be prepared with `hermes pm repair` under the returned `HERMES_HOME` before a
later hosted launch. A changed context may require preparation again. No automatic
recipe or external hosted Desktop acceptance is established. Do not mix that home
with the native profile, or enroll while readiness is failing.

## Reconnect and diagnose

`hermes auth status flop-public` validates the profile's allowance without creating
a new enrollment. `hermes auth add flop-public` explicitly synchronizes or rotates
a rejected bearer within the existing server allowance. Background refresh never
creates a wallet or requests faucet funding. Reconnection, reinstall and restart
never renew quota or expiry. Logout removes the current Hermes profile entry,
retaining the shared public cache and server allowance.

The operator configures public wallet quota explicitly; no live amount is verified here. Check returned remaining_quota (FLOP), model scope and expires_at (epoch milliseconds, at most 24 hours). Faucet funds belong to the wallet; this allowance spends broker funds. No midnight reset or issuer-approved same-wallet restoration route is verified. Availability and enrollment may be disabled independently of plugin
installation. An empty catalog means no qualified model is available. A 401 means
missing/rejected credentials; a 402 means insufficient quota or funding. Expired,
exhausted, malformed or unreachable credentials stop setup. Do not guess another
model, substitute another provider, or retry a paid request blindly.

Before sending a paid request, verify an existing funded allowance scoped to the
model, its remaining quota, expiry and the live quote. Do not silently increase
quota, mint funds or extend expiry. A clean
installation can deliberately restore an already authorized wallet identity and
then authenticate through the standard flow, without copying an old auth cache
or conversation. Record this as identity restoration, not brand-new wallet
enrollment; it does not renew the existing allowance.

## Optional six-hour residency

The candidate six-hour mode needs a live miner and gateway that both opt in.
The gateway's on-demand peer sets `residentReservationMs: 21600000`; the worker's
matching model profile sets `max_resident_reservation_ms: 21600000`. Omission
leaves the previous behavior. Installing Hermes does not enable or provision
this capacity. Public provider 0.1.6 works through that gateway configuration;
do not replace the immutable launcher/provider or increase request timeouts.

Before sending, verify a funded parent credential scoped to the exact model and
authorized through six hours after acceptance. Do not silently extend its expiry
or allowance. A short-lived ephemeral credential keeps its original limit and
cannot silently acquire a longer hold. The miner operator accepts idle gaps
without an additional idle charge; only real requests reserve funding under the
existing per-request caps. The backend can remain resident through zero-child
gaps and channel rollover, but the accepted owner, model/policy, miner, slot and
expiry stay fixed. Requests and heartbeats do not renew the hold. New work stops
at expiry while unresolved channel and proof obligations remain recoverable.

Keep each request's one-hour deadline, 1,000-FLOP cap and all verification checks.
Residency does not remove the conservative channel-work guard or the separate
elapsed-block settlement gate. Inspect accepted reservation metadata and pending
settlement in receipts; the native UI has no residency countdown or chain-status
display. The earlier two-hour H100 pilot established native tool use and warm
reuse/rollover. Six-hour fake-clock tests are lifecycle evidence; do not describe
them as a paid six-hour GPU run or H200 fleet qualification.

## Verification boundaries

Installation and a populated model picker prove configuration only. Report
inference delivery, proof production and finalized payment separately. A usable
reply with pending proof or settlement must remain labelled pending. Run paid inference only when the
user authorizes it. For a paid terminal test, create a fresh noncredential nonce
in an owner-only file and ask Hermes to read it without giving the nonce in the
prompt. Require the actual tool result, exact final answer and request-correlated
positive finalized receipts from `/v1/keys/me/receipts`. A pending receipt, channel
ID, Desktop spawn or discovery Test action does not establish paid acceptance.
Verify the same wallet, quota and expiry after restart without another faucet grant.
Cooperative settlement pays the full funded quote, including reserved output;
shorter answers do not necessarily lower the charge. Devnet FLOP is not a USD price.

## Separate private pilot

`flop-devnet` is the private-network provider, with separate cache, identity and
allowance. Never install it for public users or ask public users to contact a
private gateway. Approved private operators should use
https://github.com/flop-labs/flop-core/blob/main/sdk/hermes_native/README.md.
