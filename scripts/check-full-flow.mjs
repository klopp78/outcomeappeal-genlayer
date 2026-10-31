import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const page = readFileSync("app/page.tsx", "utf8");
const client = readFileSync("lib/genlayer.ts", "utf8");
for (const control of ["Fund payment case", "Open payment appeal", "Respond with bond", "Resolve by consensus", "Settle payment appeal", "Read finalized state"]) assert.ok(page.includes(control), `missing visible v2 flow: ${control}`);
for (const method of ["create_payment_case", "open_payment_appeal", "respond_to_appeal", "resolve_payment_appeal", "settle_payment_appeal", "get_case", "get_appeal", "get_resolution"]) assert.ok(client.includes(method), `missing GenLayer call: ${method}`);
assert.ok(client.includes("waitForTransactionReceipt"), "writes must wait for consensus acceptance");
assert.ok(client.includes("BigInt(input.amountWei)"), "payment escrow must transmit the selected amount");
console.log("OutcomeAppeal v2 frontend-contract flow checks passed");
