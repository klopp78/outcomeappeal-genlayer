import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const page = readFileSync("app/page.tsx", "utf8");
const client = readFileSync("lib/genlayer.ts", "utf8");
for (const marker of ["Register case", "Assess case", "Challenge", "Resolve challenge", "Finalize ruling", "Read on-chain record"]) assert.ok(page.includes(marker), `missing visible workflow control: ${marker}`);
for (const method of ["register_case", "assess_case", "challenge_assessment", "resolve_challenge", "finalize_ruling", "get_case", "get_ruling"]) assert.ok(client.includes(method), `missing GenLayer client call: ${method}`);
assert.ok(client.includes("waitForTransactionReceipt"), "writes must wait for consensus acceptance");
console.log("OutcomeAppeal frontend-contract flow checks passed");
