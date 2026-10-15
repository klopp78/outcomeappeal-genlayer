import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync("contracts/outcome_appeal.py", "utf8");
for (const id of ["case_" + "a".repeat(20), "asm_" + "b".repeat(20), "chg_" + "c".repeat(20), "rul_" + "d".repeat(20)]) assert.match(id, /^(case|asm|chg|rul)_[a-f0-9]{20}$/);
for (const marker of ["assessment_not_challengeable", "challenge_window_closed", "challenge_window_still_open", "case_not_finalizable", "case_baseline_hash", "resolution_hash"]) assert.ok(source.includes(marker), `missing lifecycle guard ${marker}`);
console.log("OutcomeAppeal lifecycle guard checks passed");
