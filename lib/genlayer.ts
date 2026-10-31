import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

export const OUTCOME_APPEAL_CONTRACT_ADDRESS = (process.env.NEXT_PUBLIC_OUTCOME_APPEAL_CONTRACT_ADDRESS ?? "0x0000000000000000000000000000000000000000") as `0x${string}`;
export type WalletAddress = `0x${string}`;
type Address = `0x${string}`;

export function explorerAddress(address = OUTCOME_APPEAL_CONTRACT_ADDRESS) { return `https://explorer-studio.genlayer.com/address/${address}`; }
function client(walletAddress?: WalletAddress) { return createClient({ chain: studionet, account: walletAddress }); }
function contract(address?: Address) { return address ?? OUTCOME_APPEAL_CONTRACT_ADDRESS; }
function writer(wallet: WalletAddress) {
  const provider = typeof window !== "undefined" ? window.ethereum : undefined;
  if (!provider) throw new Error("No browser wallet detected.");
  return createClient({ chain: studionet, account: wallet, provider });
}

export async function connectWallet(): Promise<WalletAddress> {
  const provider = typeof window !== "undefined" ? window.ethereum : undefined;
  if (!provider) throw new Error("No browser wallet detected.");
  const accounts = await provider.request({ method: "eth_requestAccounts" }) as WalletAddress[];
  if (!accounts[0]) throw new Error("No wallet account returned.");
  return accounts[0];
}

export async function readRecord(method: "get_case" | "get_appeal" | "get_resolution", id: string, address?: Address) {
  return client().readContract({ address: contract(address), functionName: method, args: [id], jsonSafeReturn: true, leaderOnly: true });
}

export async function createPaymentCase(input: { wallet: WalletAddress; merchant: string; orderReference: string; paymentEvidence: string; termsUrl: string; appealWindow: string; nonce: string; amountWei: string; address?: Address }) {
  return write(input.wallet, "create_payment_case", [input.merchant, input.orderReference, input.paymentEvidence, input.termsUrl, input.appealWindow, input.nonce], BigInt(input.amountWei), /pay_[a-f0-9]{20}/, input.address);
}
export async function openPaymentAppeal(input: { wallet: WalletAddress; caseId: string; resolution: string; claimantEvidence: string; bondWei: string; address?: Address }) {
  return write(input.wallet, "open_payment_appeal", [input.caseId, input.resolution, input.claimantEvidence], BigInt(input.bondWei), /app_[a-f0-9]{20}/, input.address);
}
export async function respondToAppeal(input: { wallet: WalletAddress; appealId: string; merchantEvidence: string; bondWei: string; address?: Address }) {
  return write(input.wallet, "respond_to_appeal", [input.appealId, input.merchantEvidence], BigInt(input.bondWei), /(?:)/, input.address);
}
export async function resolvePaymentAppeal(input: { wallet: WalletAddress; appealId: string; address?: Address }) {
  return write(input.wallet, "resolve_payment_appeal", [input.appealId], BigInt(0), /res_[a-f0-9]{20}/, input.address);
}
export async function settlePaymentAppeal(input: { wallet: WalletAddress; resolutionId: string; address?: Address }) {
  return write(input.wallet, "settle_payment_appeal", [input.resolutionId], BigInt(0), /(?:)/, input.address);
}

async function write(wallet: WalletAddress, functionName: string, args: string[], value: bigint, expected: RegExp, address?: Address) {
  const target = contract(address);
  if (/^0x0{40}$/i.test(target)) throw new Error("Set the deployed Studio contract address first.");
  const instance = writer(wallet);
  const hash = await instance.writeContract({ address: target, functionName, args, value, leaderOnly: false });
  const receipt = await instance.waitForTransactionReceipt({ hash, status: TransactionStatus.ACCEPTED, fullTransaction: true });
  const id = collect(receipt).map((text) => text.match(expected)?.[0]).find(Boolean) ?? "accepted";
  return { hash, receipt, id, explorer: `https://explorer-studio.genlayer.com/tx/${hash}` };
}
function collect(value: unknown): string[] { if (typeof value === "string") return [value]; if (!value || typeof value !== "object") return []; return Object.values(value as Record<string, unknown>).flatMap(collect); }
export function compactError(error: unknown): string { if (error instanceof Error && error.message) return error.message; try { return JSON.stringify(error) || "Unknown GenLayer error."; } catch { return "Unknown GenLayer error."; } }
