import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

export const OUTCOME_APPEAL_CONTRACT_ADDRESS =
  (process.env.NEXT_PUBLIC_OUTCOME_APPEAL_CONTRACT_ADDRESS ?? "0x6c8142cDF59D770A831BFf9F503009B573E6Daea") as `0x${string}`;

export type WalletAddress = `0x${string}`;
type Address = `0x${string}`;

export function explorerAddress(address = OUTCOME_APPEAL_CONTRACT_ADDRESS) {
  return `https://explorer-studio.genlayer.com/address/${address}`;
}

function client(walletAddress?: WalletAddress) { return createClient({ chain: studionet, account: walletAddress }); }
function writeClient(walletAddress: WalletAddress) {
  const provider = typeof window !== "undefined" ? window.ethereum : undefined;
  if (!provider) throw new Error("No browser wallet detected.");
  return createClient({ chain: studionet, account: walletAddress, provider });
}
function address(value?: Address) { return value ?? OUTCOME_APPEAL_CONTRACT_ADDRESS; }

export async function connectWallet(): Promise<WalletAddress> {
  const provider = typeof window !== "undefined" ? window.ethereum : undefined;
  if (!provider) throw new Error("No browser wallet detected.");
  const accounts = await provider.request({ method: "eth_requestAccounts" }) as WalletAddress[];
  if (!accounts[0]) throw new Error("No wallet account returned.");
  return accounts[0];
}

export async function readRecord(method: "get_case" | "get_assessment" | "get_challenge" | "get_ruling", id: string, contractAddress?: Address) {
  return client().readContract({ address: address(contractAddress), functionName: method, args: [id], jsonSafeReturn: true, leaderOnly: true });
}

export async function submitCase(input: { wallet: WalletAddress; title: string; outcome: string; primary: string; corroborating: string; window: string; contractAddress?: Address }) {
  return write(input.wallet, "register_case", [input.title, input.outcome, input.primary, input.corroborating, input.window], /case_[a-f0-9]{20}/, input.contractAddress);
}
export async function assessCase(input: { wallet: WalletAddress; caseId: string; evidence: string; contractAddress?: Address }) {
  return write(input.wallet, "assess_case", [input.caseId, input.evidence], /asm_[a-f0-9]{20}/, input.contractAddress);
}
export async function challengeCase(input: { wallet: WalletAddress; caseId: string; assessmentId: string; evidence: string; contractAddress?: Address }) {
  return write(input.wallet, "challenge_assessment", [input.caseId, input.assessmentId, input.evidence], /chg_[a-f0-9]{20}/, input.contractAddress);
}
export async function resolveChallenge(input: { wallet: WalletAddress; caseId: string; challengeId: string; contractAddress?: Address }) {
  return write(input.wallet, "resolve_challenge", [input.caseId, input.challengeId], /chg_[a-f0-9]{20}/, input.contractAddress);
}
export async function finalizeRuling(input: { wallet: WalletAddress; caseId: string; contractAddress?: Address }) {
  return write(input.wallet, "finalize_ruling", [input.caseId], /rul_[a-f0-9]{20}/, input.contractAddress);
}

async function write(wallet: WalletAddress, functionName: string, args: string[], pattern: RegExp, contractAddress?: Address) {
  const contract = address(contractAddress);
  if (/^0x0{40}$/i.test(contract)) throw new Error("Set the deployed Studio contract address first.");
  const writer = writeClient(wallet);
  const hash = await writer.writeContract({ address: contract, functionName, args, value: BigInt(0), leaderOnly: false });
  const receipt = await writer.waitForTransactionReceipt({ hash, status: TransactionStatus.ACCEPTED, fullTransaction: true });
  const id = collect(receipt).map((text) => text.match(pattern)?.[0]).find(Boolean);
  if (!id) throw new Error("Accepted transaction did not return the expected record ID.");
  return { hash, receipt, id, explorer: `https://explorer-studio.genlayer.com/tx/${hash}` };
}
function collect(value: unknown): string[] { if (typeof value === "string") return [value]; if (!value || typeof value !== "object") return []; return Object.values(value as Record<string, unknown>).flatMap(collect); }
export function compactError(error: unknown): string { if (error instanceof Error && error.message) return error.message; if (typeof error === "string") return error; try { const text = JSON.stringify(error); return text && text !== "{}" ? text : "Unknown GenLayer error."; } catch { return "Unknown GenLayer error."; } }
