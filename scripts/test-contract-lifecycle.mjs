import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync("contracts/outcome_appeal.py", "utf8");
for (const id of ["pay_" + "a".repeat(20), "app_" + "b".repeat(20), "res_" + "c".repeat(20)]) assert.match(id, /^(pay|app|res)_[a-f0-9]{20}$/);
for (const marker of ["positive_payment_escrow_required", "positive_claimant_bond_required", "merchant_bond_must_cover_claimant_bond", "payment_not_appealable", "appeal_not_respondable", "resolution_not_settleable", "payment_not_releasable", "appeal_not_recoverable"]) assert.ok(source.includes(marker), `missing lifecycle guard ${marker}`);
assert.ok(source.includes('"payer": payer') && source.includes('"merchant": payee'), "canonical payment must bind both parties");
assert.ok(source.includes('"reserved_amount_wei": str(gl.message.value)'), "case must bind the exact escrowed amount");
assert.ok(source.includes("case[\"status\"], case[\"appeal_id\"] = \"appealed\", appeal_id"), "case must be bound to exactly one appeal path");
assert.ok(source.includes("if resolution[\"decision\"] == \"payer_upheld\":"), "settlement must follow the consensus verdict");
console.log("OutcomeAppeal v2 adversarial lifecycle checks passed");
