import { readFileSync } from "node:fs";
import assert from "node:assert/strict";

const source = readFileSync("contracts/outcome_appeal.py", "utf8");
for (const marker of [
  "class OutcomeAppeal(gl.Contract)", "register_case", "assess_case",
  "challenge_assessment", "resolve_challenge", "finalize_ruling",
  "get_case", "get_assessment", "get_challenge", "get_ruling",
  "gl.vm.run_nondet_unsafe", "gl.nondet.web.render", "gl.nondet.exec_prompt",
  "baseline_snapshot_commitments", "challenge_window_still_open", "hashlib.sha256",
]) assert.ok(source.includes(marker), `missing contract integrity marker: ${marker}`);
assert.ok(!source.includes("hash("), "non-cryptographic hash must not be used");
console.log("OutcomeAppeal contract integrity checks passed");
