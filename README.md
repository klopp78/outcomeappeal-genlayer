# OutcomeAppeal for GenLayer

OutcomeAppeal is a challengeable consensus court for disputed public outcomes. It gives a market operator, AI agent, or community member a verifiable path from an initial claim to a final ruling instead of treating a one-off oracle answer as irreversible.

## Workflow

1. `register_case` records a title, claimed outcome, two public sources, and a challenge window. Validators render both sources and commit immutable SHA-256 snapshot hashes.
2. `assess_case` renders the baseline sources plus fresh assessment evidence. Validators independently judge the result as `upheld`, `rejected`, or `inconclusive`, returning an `asm_*` receipt.
3. `challenge_assessment` accepts counterevidence only during the stored window and creates a `chg_*` record bound to its source snapshot.
4. `resolve_challenge` has validators re-evaluate the original sources with counterevidence. `finalize_ruling` produces a `rul_*` receipt only after a challenge is resolved or the window closes.

Every consequential record stores canonical source URLs and collision-resistant snapshot commitments. The app writes directly to the Studio contract, waits for consensus acceptance, extracts returned IDs, and reads records back on-chain.

## Run locally

```bash
npm ci
npm test
npm run dev
```

Deploy `contracts/outcome_appeal.py` in GenLayer Studio, then enter that contract address in the app before creating a case.
