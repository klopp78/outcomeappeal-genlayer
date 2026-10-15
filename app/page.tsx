"use client";

import { useState, type ReactNode } from "react";
import { OUTCOME_APPEAL_CONTRACT_ADDRESS, assessCase, challengeCase, compactError, connectWallet, explorerAddress, finalizeRuling, readRecord, resolveChallenge, submitCase, type WalletAddress } from "@/lib/genlayer";

type Step = "register" | "assess" | "challenge" | "finalize" | "read";

export default function Home() {
  const [contractAddress, setContractAddress] = useState(OUTCOME_APPEAL_CONTRACT_ADDRESS);
  const [wallet, setWallet] = useState<WalletAddress | null>(null);
  const [status, setStatus] = useState("Deploy the contract in Studio, enter its address, then create a disputed outcome case.");
  const [result, setResult] = useState("");
  const [busy, setBusy] = useState<Step | null>(null);
  const [caseForm, setCaseForm] = useState({ title: "Will the announced policy take effect by the stated deadline?", outcome: "The policy takes effect by the stated deadline.", primary: "https://www.whitehouse.gov/", corroborating: "https://www.reuters.com/", window: "3600" });
  const [caseId, setCaseId] = useState("case_");
  const [assessmentId, setAssessmentId] = useState("asm_");
  const [challengeId, setChallengeId] = useState("chg_");
  const [evidence, setEvidence] = useState("https://apnews.com/");
  const [counterEvidence, setCounterEvidence] = useState("https://www.bbc.com/news");
  const [readKind, setReadKind] = useState<"get_case" | "get_assessment" | "get_challenge" | "get_ruling">("get_case");
  const [readId, setReadId] = useState("case_");

  const address = contractAddress as `0x${string}`;
  async function withWallet(step: Step, action: (account: WalletAddress) => Promise<{ id: string; explorer?: string }>) {
    try {
      setBusy(step); setResult("");
      const account = wallet ?? await connectWallet();
      setWallet(account);
      const response = await action(account);
      setStatus(`Accepted ${step} transaction: ${response.id}`);
      setResult(JSON.stringify(response, null, 2));
      if (response.id.startsWith("case_")) { setCaseId(response.id); setReadId(response.id); }
      if (response.id.startsWith("asm_")) { setAssessmentId(response.id); setReadId(response.id); }
      if (response.id.startsWith("chg_")) { setChallengeId(response.id); setReadId(response.id); }
      if (response.id.startsWith("rul_")) setReadId(response.id);
    } catch (error) { setStatus(compactError(error)); } finally { setBusy(null); }
  }
  async function read() {
    try { setBusy("read"); setResult(""); const record = await readRecord(readKind, readId, address); setStatus(`Loaded ${readKind}.`); setResult(typeof record === "string" ? record : JSON.stringify(record, null, 2)); } catch (error) { setStatus(compactError(error)); } finally { setBusy(null); }
  }
  return (
    <main className="min-h-screen bg-[#f5f7fb] text-[#15171a]">
      <header className="border-b border-[#d7dee9] bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-5 lg:px-8">
          <div><span className="field-label">GenLayer Project</span><h1 className="text-2xl font-semibold">OutcomeAppeal</h1></div>
          <a className="action-button" href={explorerAddress(address)} rel="noreferrer" target="_blank">Studio explorer</a>
        </div>
      </header>
      <section className="mx-auto max-w-6xl px-5 py-8 lg:px-8">
        <div className="grid gap-7 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <span className="pill">Challengeable public-outcome rulings</span>
            <h2 className="mt-5 max-w-3xl text-4xl font-semibold leading-tight">A real appeal path for outcomes that are not black and white.</h2>
            <p className="mt-5 max-w-3xl text-lg leading-8 text-[#60707b]">OutcomeAppeal captures an immutable evidence baseline, asks GenLayer validators for an initial ruling, accepts time-bound counterevidence, then finalizes a durable consensus receipt.</p>
          </div>
          <aside className="tool-panel"><span className="field-label">Live contract</span><label className="grid gap-2"><span>Studio contract address</span><input className="text-input" value={contractAddress} onChange={(event) => setContractAddress(event.target.value)} /></label><button className="action-button mt-4" onClick={() => connectWallet().then(setWallet).then(() => setStatus("Wallet connected.")).catch((error) => setStatus(compactError(error)))}>{wallet ? `Connected ${wallet.slice(0, 6)}...${wallet.slice(-4)}` : "Connect wallet"}</button></aside>
        </div>
      </section>
      <section className="mx-auto grid max-w-6xl gap-5 px-5 pb-5 md:grid-cols-2 lg:px-8">
        <Panel number="01" title="Create a case" detail="Two public sources are rendered and hashed before the claim is assessable.">
          <Field label="Case title" value={caseForm.title} onChange={(value) => setCaseForm({ ...caseForm, title: value })} />
          <Field label="Claimed outcome" value={caseForm.outcome} onChange={(value) => setCaseForm({ ...caseForm, outcome: value })} />
          <Field label="Primary source URL" value={caseForm.primary} onChange={(value) => setCaseForm({ ...caseForm, primary: value })} />
          <Field label="Corroborating source URL" value={caseForm.corroborating} onChange={(value) => setCaseForm({ ...caseForm, corroborating: value })} />
          <Field label="Challenge window seconds" value={caseForm.window} onChange={(value) => setCaseForm({ ...caseForm, window: value })} />
          <button className="action-button primary" disabled={busy !== null} onClick={() => withWallet("register", (walletAddress) => submitCase({ wallet: walletAddress, ...caseForm, contractAddress: address }))}>{busy === "register" ? "Awaiting consensus" : "Register case"}</button>
        </Panel>
        <Panel number="02" title="Assess the claim" detail="Validators compare the registered baseline with a new evidence surface.">
          <Field label="Case ID" value={caseId} onChange={setCaseId} />
          <Field label="Assessment evidence URL" value={evidence} onChange={setEvidence} />
          <button className="action-button primary" disabled={busy !== null} onClick={() => withWallet("assess", (walletAddress) => assessCase({ wallet: walletAddress, caseId, evidence, contractAddress: address }))}>{busy === "assess" ? "Awaiting consensus" : "Assess case"}</button>
        </Panel>
        <Panel number="03" title="Challenge and resolve" detail="A challenge is only valid during the case's stored window; resolution reruns consensus over the counterevidence.">
          <Field label="Case ID" value={caseId} onChange={setCaseId} />
          <Field label="Assessment ID" value={assessmentId} onChange={setAssessmentId} />
          <Field label="Counterevidence URL" value={counterEvidence} onChange={setCounterEvidence} />
          <div className="flex flex-wrap gap-3"><button className="action-button primary" disabled={busy !== null} onClick={() => withWallet("challenge", (walletAddress) => challengeCase({ wallet: walletAddress, caseId, assessmentId, evidence: counterEvidence, contractAddress: address }))}>{busy === "challenge" ? "Awaiting consensus" : "Challenge"}</button><button className="action-button" disabled={busy !== null} onClick={() => withWallet("challenge", (walletAddress) => resolveChallenge({ wallet: walletAddress, caseId, challengeId, contractAddress: address }))}>Resolve challenge</button></div>
          <Field label="Challenge ID" value={challengeId} onChange={setChallengeId} />
        </Panel>
        <Panel number="04" title="Finalize and inspect" detail="Finalization enforces the challenge window and binds the outcome to baseline, assessment, and resolution hashes.">
          <Field label="Case ID" value={caseId} onChange={setCaseId} />
          <button className="action-button primary" disabled={busy !== null} onClick={() => withWallet("finalize", (walletAddress) => finalizeRuling({ wallet: walletAddress, caseId, contractAddress: address }))}>{busy === "finalize" ? "Awaiting consensus" : "Finalize ruling"}</button>
          <label className="grid gap-2"><span className="field-label">Read a record</span><select className="text-input" value={readKind} onChange={(event) => setReadKind(event.target.value as typeof readKind)}><option value="get_case">Case</option><option value="get_assessment">Assessment</option><option value="get_challenge">Challenge</option><option value="get_ruling">Ruling</option></select></label>
          <Field label="Record ID" value={readId} onChange={setReadId} />
          <button className="action-button" disabled={busy !== null} onClick={read}>{busy === "read" ? "Reading" : "Read on-chain record"}</button>
        </Panel>
      </section>
      <section className="mx-auto max-w-6xl px-5 pb-10 lg:px-8"><div className="result-card"><span className="field-label">Transaction status</span><p className="leading-7 text-[#60707b]">{status}</p>{result ? <pre className="mt-4 overflow-x-auto text-sm">{result}</pre> : null}</div></section>
    </main>
  );
}

function Panel({ number, title, detail, children }: { number: string; title: string; detail: string; children: ReactNode }) { return <section className="tool-panel grid gap-4"><span className="field-label">{number}</span><div><h2 className="text-2xl font-semibold">{title}</h2><p className="mt-2 leading-7 text-[#60707b]">{detail}</p></div>{children}</section>; }
function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) { return <label className="grid gap-2"><span className="field-label">{label}</span><input className="text-input" value={value} onChange={(event) => onChange(event.target.value)} /></label>; }
