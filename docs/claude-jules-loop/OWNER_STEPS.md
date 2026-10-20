# Owner-only steps (phone-friendly). Do them in order; none is needed until PORT_PLAN decisions A-C are yes.

Never paste a key into chat. Never press "Re-run" on a finished run.

1. **AGENTS.md amendment (Merge by owner).** Add under "自動実行しない": "Claude x Jules loop is allowed only per
   `docs/claude-jules-loop/` after the owner's activation PR; loop writes only `claude/*` branches; no Merge by the loop."
2. **GitHub app -> repo Settings -> Actions -> General:** allow Actions for this repo; Workflow permissions "Read repository contents".
3. **Settings -> Environments -> New environment `jules-api`:** add secret `JULES_API_KEY` (key from Jules settings;
   Jules Settings -> Usage: credits OFF). Required reviewers: yourself (adds a tap before each start).
4. **Jules (jules.google.com):** connect GitHub, grant the `ai-video-research` repo only.
5. **Labels:** create `jules`, `loop-stop` (Issues -> Labels -> New label). Do not put `jules` on any Issue by hand.
6. **Routine 1 (reviewer, Sonnet 5.5 explicit)** and **Routine 2 (takeover, Opus)** on claude.ai/code/routines: created only
   after the adapted prompts exist (Decision B). Environment must NOT contain the Jules key.
7. **Activation PR:** move the three `templates/*.TEMPLATE.json` to `docs/claude-jules-loop/active/` without `.TEMPLATE`, fill
   `approved_by`, `approval_ref`, `expires_at`, budget limits; move the workflow template to `.github/workflows/`. Your Merge
   is the approval.
8. **First LIVE start:** one controlled run with a sentence you type yourself. Not before 1-7.
9. **Merge** of any loop PR: only you, at the head the reviewer receipt names.
