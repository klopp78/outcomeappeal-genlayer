# OutcomeAppeal for GenLayer

OutcomeAppeal is a challengeable consensus court for disputed public outcomes. It gives a market operator, AI agent, or community member a verifiable path from an initial claim to a final ruling instead of treating a one-off oracle answer as irreversible.

## Workflow

1. `register_case` renders two public sources once, normalizes each into a 3,200-character evidence snapshot, and stores the bounded content plus an immutable SHA-256 commitment.
2. `assess_case` adds one admitted assessment snapshot, then evaluates it together with the stored baseline snapshots. Validators compare the consequential verdict and evidence commitment, never free-form model prose.
3. `challenge_assessment` accepts counterevidence only during the stored window and records its own immutable, bounded snapshot as a `chg_*` record.
4. `resolve_challenge` never re-fetches the web: it evaluates the stored baseline, assessment, and counterevidence snapshots, verifies their bindings, and produces a final `rul_*` receipt after resolution or the window closes.

Every consequential record stores canonical source URLs and collision-resistant snapshot commitments. The app writes directly to the Studio contract, waits for consensus acceptance, extracts returned IDs, and reads records back on-chain.

## Run locally

```bash
npm ci
npm test
npm run dev
```

Deploy `contracts/outcome_appeal.py` in GenLayer Studio, then enter that contract address in the app before creating a case.
