import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";
import "./styles.css";

type Address = `0x${string}`;
const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const ids: Record<string, string> = { case: "case-id", assessment: "assessment-id", challenge: "challenge-id", ruling: "ruling-id" };
let wallet: Address | undefined;

function contract(): Address { return $("contract-address") as HTMLInputElement ? ($("contract-address") as HTMLInputElement).value.trim() as Address : "0xb6Ab1351FeFDD395Bf229343971Fa5998ADA9579"; }
function setStatus(message: string, phase = "READY") { $("status").textContent = message; $("phase").textContent = phase; }
function explorer(path: "address" | "tx", value: string) { return `https://explorer-studio.genlayer.com/${path}/${value}`; }
function output(value: unknown) { $("output").textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2); }
function extract(value: unknown, prefix: string): string | undefined { if (typeof value === "string") return value.match(new RegExp(`${prefix}_[a-f0-9]{20}`))?.[0]; if (!value || typeof value !== "object") return; return Object.values(value as Record<string, unknown>).map((item) => extract(item, prefix)).find(Boolean); }
function fillCase(value: string) { ["assess-case", "challenge-case", "finalize-case"].forEach((id) => { ($(id) as HTMLInputElement).value = value; }); }

async function connect() {
  const provider = window.ethereum;
  if (!provider) throw new Error("No browser wallet detected.");
  const accounts = await provider.request({ method: "eth_requestAccounts" }) as Address[];
  if (!accounts[0]) throw new Error("No wallet account returned.");
  wallet = accounts[0];
  $("connect").textContent = `${wallet.slice(0, 6)}...${wallet.slice(-4)}`;
  setStatus("Wallet connected. The forms write directly to the deployed contract.");
}

async function write(method: string, args: string[], prefix: string) {
  if (!wallet) await connect();
  const address = contract();
  if (!/^0x[a-fA-F0-9]{40}$/.test(address)) throw new Error("Enter a valid deployed Studio contract address.");
  setStatus("Submitting consensus transaction...", "PENDING");
  const provider = window.ethereum;
  const client = createClient({ chain: studionet, account: wallet!, provider });
  const hash = await client.writeContract({ address, functionName: method, args, value: BigInt(0), leaderOnly: false });
  $("tx").innerHTML = `<a target="_blank" rel="noreferrer" href="${explorer("tx", hash)}">${hash.slice(0, 10)}...</a>`;
  const receipt = await client.waitForTransactionReceipt({ hash, status: TransactionStatus.ACCEPTED, fullTransaction: true });
  const id = extract(receipt, prefix);
  if (!id) throw new Error("Accepted transaction did not return the expected record ID.");
  $(ids[prefix]).textContent = id;
  if (prefix === "case") fillCase(id);
  if (prefix === "assessment") { ($("challenge-assessment") as HTMLInputElement).value = id; }
  if (prefix === "challenge") { ($("resolve-challenge") as HTMLInputElement).value = id; }
  setStatus(`${prefix}_ receipt accepted by consensus.`, "ACCEPTED");
  output(receipt);
  return id;
}

$("connect").addEventListener("click", () => connect().catch(showError));
$("contract-address").addEventListener("input", () => { const address = contract(); $("short-address").textContent = `${address.slice(0, 6)}...${address.slice(-4)}`; $("explorer").setAttribute("href", explorer("address", address)); });
$("explorer").setAttribute("href", explorer("address", contract()));

document.querySelectorAll<HTMLButtonElement>(".tab").forEach((tab) => tab.addEventListener("click", () => { document.querySelectorAll(".tab,.view").forEach((node) => node.classList.remove("active")); tab.classList.add("active"); $(tab.dataset.tab!).classList.add("active"); }));
$("case").addEventListener("submit", (event) => { event.preventDefault(); write("register_case", [($("title") as HTMLInputElement).value, ($("outcome") as HTMLInputElement).value, ($("primary") as HTMLInputElement).value, ($("corroborating") as HTMLInputElement).value, ($("window") as HTMLInputElement).value], "case").catch(showError); });
$("assess").addEventListener("submit", (event) => { event.preventDefault(); write("assess_case", [($("assess-case") as HTMLInputElement).value, ($("assessment-evidence") as HTMLInputElement).value], "assessment").catch(showError); });
$("appeal").addEventListener("submit", (event) => { event.preventDefault(); write("challenge_assessment", [($("challenge-case") as HTMLInputElement).value, ($("challenge-assessment") as HTMLInputElement).value, ($("counterevidence") as HTMLInputElement).value], "challenge").catch(showError); });
$("resolve").addEventListener("click", () => write("resolve_challenge", [($("challenge-case") as HTMLInputElement).value, ($("resolve-challenge") as HTMLInputElement).value], "challenge").catch(showError));
$("finalize").addEventListener("click", () => write("finalize_ruling", [($("finalize-case") as HTMLInputElement).value], "ruling").catch(showError));
$("read").addEventListener("click", async () => { try { setStatus("Reading accepted chain state...", "READING"); const client = createClient({ chain: studionet }); const result = await client.readContract({ address: contract(), functionName: ($("record-type") as HTMLSelectElement).value, args: [($("record-id") as HTMLInputElement).value], jsonSafeReturn: true, leaderOnly: true }); output(result); setStatus("Accepted record loaded.", "READ"); } catch (error) { showError(error); } });
function showError(error: unknown) { const message = error instanceof Error ? error.message : String(error); setStatus(message, "ERROR"); }
