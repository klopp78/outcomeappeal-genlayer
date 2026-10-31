# OutcomeAppeal for GenLayer v2

OutcomeAppeal v2 upgrades the original consensus-ruling project into a payment-recourse rail for AI agents. A payer escrows GEN for a named merchant and order, then either lets the payment release after the appeal window or opens a bonded, evidence-bound appeal.

## Payment recourse lifecycle

1. `create_payment_case` is payable. It permanently binds the payer, merchant, order reference, payment evidence URL, terms URL, exact escrowed amount, expiry and a nonce in a canonical SHA-256 commitment.
2. `open_payment_appeal` is payable and available only to the bound payer before expiry. A claimant bond makes frivolous appeals costly.
3. `respond_to_appeal` is payable and available only to the named merchant. The merchant must post at least the claimant bond and provide its own evidence URL.
4. `resolve_payment_appeal` uses `gl.vm.run_nondet_unsafe`. Each validator independently renders the payment evidence, terms and both parties' sources, then compares the full consequential decision and immutable evidence commitments.
5. `settle_payment_appeal` executes the verdict, transferring the payment escrow and both bonds to the prevailing party. An inconclusive result returns payment and each party's own bond. There are also deterministic paths for expired unappealed payments and unanswered appeals.

The browser app connects a wallet to each actual payable contract method, waits for consensus acceptance, and reads finalized contract state back before reporting a result.

## Local checks

```bash
npm ci
npm test
npm run dev
```

Deploy `contracts/outcome_appeal.py` in GenLayer Studio, set the address in the app, then use a small test GEN amount to exercise the complete workflow.
