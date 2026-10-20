# Claude x Jules loop: port plan for ai-video-research (STATIC, nothing is active)

Source of truth: `kamiyusense/multi-ai-council-phase0` (`docs/claude-jules-loop/README.md`, `docs/CLAUDE_JULES_API_ROUTE_V1.md`,
`docs/CLAUDE_TAKEOVER_V1.md`, `docs/USER_COPY_TEXT_FORMAT.md`). Nothing here starts Jules, labels an issue, or touches a secret.

## Flow being ported
signal Issue -> loop makes a task Issue -> Jules starts -> Routine 1 (Sonnet reviewer, hourly + PR events) -> corrective via
PR comment + Jules API message -> after 2 failed Jules rounds, Routine 2 (Opus takeover, branch `claude/takeover-*`) ->
PASS PRs wait for the owner's Merge. Stop = close the checkpoint Issue or add label `loop-stop`.

## Parts inventory
| # | Part (phase0) | Needed here? | Status in this PR |
|---|---|---|---|
| 1 | `docs/claude-jules-loop/active/{campaign,authorization,budget-declaration}.json` | yes | TEMPLATEs in `templates/`, owner fields empty, budget 0 |
| 2 | `.github/workflows/claude-jules-api-start.yml` (one Jules REST call, retry 0, key only in env `jules-api`) | yes (API route) | disabled TEMPLATE; starting branch pinned to the research branch |
| 3 | Python core (~6.6k lines, 21 modules: loop, planner, signal CLI, starter, budget ledger, GitHub ports, reviewer protocol) | yes, but heavy | NOT copied (see Decision B) |
| 4 | Routine 1 prompt v1.9, Routine 2 prompt v1 | yes | NOT copied; they name phase0 paths. Adapted after Decision B |
| 5 | Jules GitHub App on the repo | only for the label route | owner step; this port uses the API route |
| 6 | `jules-session-message/readback/stop` workflows | later (corrective resend) | not copied |
| 7 | Labels `jules`, `loop-stop`; checkpoint Issue | yes | owner/loop creates after activation |
| 8 | Guard `path_classes` | yes | set in campaign TEMPLATE (see below) |

## Changes versus phase0 (minimum)
- Repository -> `kamiyusense/ai-video-research`. Route -> `jules-api-carrier` (the `jules` label route starts Jules from the
  default branch, which here is a README-only `main`; the API route lets us name the starting branch).
- Starting/base branch -> `feature/gemini-notebook-research-loop-20261016` (phase0 hard-requires the default branch; the
  template workflow check is changed to this one branch). `main` is never written.
- Concurrency 1 (phase0: 5). One objective: bug fixes and tests in `automation/gemini-notebook/*.py` and `tests/test_*`.
- Protected (`safety_boundary`): `registry.json`, `research/`, `evidence/`, `automation/gemini-notebook/state/`,
  `cloud_relay_gas.js`, `docs/claude-jules-loop/`; `execution_config`: `.github/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`.
  Research notes, the video ledger and subtitle material are never loop work. Full subtitle text must never reach GitHub.

## Conflicts with this repo's AGENTS.md (must be resolved by the owner, not by the loop)
1. AGENTS.md says no Jules/provider LIVE, no GitHub Actions or scheduled start without explicit owner permission. Activation
   needs an owner-approved amendment (proposed wording in OWNER_STEPS.md step 1). This PR does not edit AGENTS.md.
2. AGENTS.md says writes go to the permitted non-default branch only. The loop writes `claude/*` branches (carrier, data,
   takeover) and Jules opens PRs. Owner must accept that `claude/*` branches are allowed for the loop.
3. Jules works from repo files only; it cannot read the private repo's Issues or PRs. Tasks must carry everything needed.

## Decisions for the owner
- A. Is code in `automation/gemini-notebook/` (Python/JS pipeline + 116 tests) the right target for Jules? If the research
  system is mostly notes, the loop has little to do and the port is not worth its cost.
- B. Copy the Python core now (about 6.6k lines, needs its own tests run here) or keep this PR as plan-only until A is yes.
  Recommendation: wait for A, then copy as one separate Draft PR with tests run in this repo.
- C. Starting branch: the research branch (recommended) or merge/move the work to `main` first.

## Not done / UNKNOWN
No test was run for the loop in this repo. Jules quality here is UNKNOWN (phase0 observed roughly 80-90% on small tasks).
Phase0 note: its Actions secret for Jules returned HTTP 401 on 2026-10-16; a key here must be fresh and owner-set.
