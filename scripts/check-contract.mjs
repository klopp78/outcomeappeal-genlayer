import { readFileSync } from "node:fs";
import assert from "node:assert/strict";

const source = readFileSync("contracts/outcome_appeal.py", "utf8");
for (const marker of [
  "class OutcomeAppeal(gl.Contract)", "create_payment_case", "open_payment_appeal",
  "respond_to_appeal", "resolve_payment_appeal", "settle_payment_appeal",
  "release_unappealed_payment", "recover_unresponded_appeal", "gl.public.write.payable",
  "gl.vm.run_nondet_unsafe", "gl.nondet.web.render", "gl.nondet.exec_prompt",
  "payment_commitment", "evidence_commitment", "merchant_bond_wei", "hashlib.sha256",
  "only_payer_can_open_appeal", "only_named_merchant_can_respond", "merchant_response_required",
]) assert.ok(source.includes(marker), `missing payment-recourse integrity marker: ${marker}`);
assert.ok(!/[^_]\bhash\(/.test(source), "non-cryptographic hash must not be used");
assert.match(source, /emit_transfer\(value=payment \+ claimant_bond \+ merchant_bond\)/);
console.log("OutcomeAppeal v2 payment-recourse contract checks passed");
