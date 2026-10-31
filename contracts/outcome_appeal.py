# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

"""OutcomeAppeal v2: consensus payment recourse with evidence-bound settlement."""

from genlayer import *
import hashlib
import json


@gl.evm.contract_interface
class _Account:
    class View:
        pass

    class Write:
        pass


class OutcomeAppeal(gl.Contract):
    cases: TreeMap[str, str]
    appeals: TreeMap[str, str]
    resolutions: TreeMap[str, str]
    case_ids: DynArray[str]
    latest_case_id: str
    latest_appeal_id: str
    latest_resolution_id: str

    def __init__(self):
        self.latest_case_id = ""
        self.latest_appeal_id = ""
        self.latest_resolution_id = ""

    @gl.public.view
    def get_case(self, case_id: str) -> str:
        return self.cases.get(case_id.strip(), "")

    @gl.public.view
    def get_appeal(self, appeal_id: str) -> str:
        return self.appeals.get(appeal_id.strip(), "")

    @gl.public.view
    def get_resolution(self, resolution_id: str) -> str:
        return self.resolutions.get(resolution_id.strip(), "")

    @gl.public.view
    def list_case_ids(self, offset: u64, limit: u64) -> str:
        start, count = int(offset), int(limit)
        if start < 0 or count < 1 or count > 50:
            raise Exception("invalid_page")
        return _json([self.case_ids[i] for i in range(start, min(start + count, len(self.case_ids)))])

    @gl.public.view
    def get_latest_case_id(self) -> str:
        return self.latest_case_id

    @gl.public.view
    def get_latest_appeal_id(self) -> str:
        return self.latest_appeal_id

    @gl.public.view
    def get_latest_resolution_id(self) -> str:
        return self.latest_resolution_id

    @gl.public.write.payable
    def create_payment_case(self, merchant: str, order_reference: str, payment_evidence_url: str, terms_url: str, appeal_window_seconds: u64, creation_nonce: str) -> str:
        if gl.message.value == u256(0):
            raise Exception("positive_payment_escrow_required")
        now, window = _now(), int(appeal_window_seconds)
        if now <= 0 or window < 300 or window > 2_592_000:
            raise Exception("invalid_appeal_window")
        payer, payee = str(gl.message.sender_address).lower(), str(Address(merchant)).lower()
        if payer == payee:
            raise Exception("merchant_must_differ_from_payer")
        canonical = {
            "schema": "outcome-appeal.payment-recourse.v2",
            "payer": payer,
            "merchant": payee,
            "order_reference": _clean(order_reference, 180, "order_reference_required"),
            "payment_evidence_url": _url(payment_evidence_url, "invalid_payment_evidence_url"),
            "terms_url": _url(terms_url, "invalid_terms_url"),
            "reserved_amount_wei": str(gl.message.value),
        }
        nonce = _hash(creation_nonce, "invalid_creation_nonce")
        case_id = "pay_" + _parts([_json(canonical), str(window), nonce])[:20]
        if self.cases.get(case_id, ""):
            raise Exception("creation_nonce_already_used")
        record = {"case_id": case_id, "canonical_payment": canonical, "payment_commitment": _parts([_json(canonical)]), "appeal_deadline": now + window, "status": "funded", "appeal_id": "", "resolution_id": "", "created_at": now}
        self.cases[case_id] = _json(record)
        self.case_ids.append(case_id)
        self.latest_case_id = case_id
        return case_id

    @gl.public.write.payable
    def open_payment_appeal(self, case_id: str, requested_resolution: str, claimant_evidence_url: str) -> str:
        case = _load(self.cases, case_id, "unknown_payment_case")
        if str(gl.message.sender_address).lower() != case["canonical_payment"]["payer"]:
            raise Exception("only_payer_can_open_appeal")
        if case["status"] != "funded" or _now() <= 0 or _now() > int(case["appeal_deadline"]):
            raise Exception("payment_not_appealable")
        if gl.message.value == u256(0):
            raise Exception("positive_claimant_bond_required")
        requested = _choice(requested_resolution, ("refund", "partial_refund"))
        claimant_url = _url(claimant_evidence_url, "invalid_claimant_evidence_url")
        appeal_id = "app_" + _parts([case["case_id"], requested, claimant_url, str(gl.message.value)])[:20]
        if self.appeals.get(appeal_id, ""):
            raise Exception("duplicate_appeal")
        appeal = {"appeal_id": appeal_id, "case_id": case["case_id"], "payer": case["canonical_payment"]["payer"], "merchant": case["canonical_payment"]["merchant"], "requested_resolution": requested, "claimant_evidence_url": claimant_url, "claimant_bond_wei": str(gl.message.value), "merchant_bond_wei": "0", "merchant_evidence_url": "", "status": "open", "response_deadline": _now() + 172800, "opened_at": _now()}
        case["status"], case["appeal_id"] = "appealed", appeal_id
        self.appeals[appeal_id], self.cases[case["case_id"]] = _json(appeal), _json(case)
        self.latest_appeal_id = appeal_id
        return appeal_id

    @gl.public.write.payable
    def respond_to_appeal(self, appeal_id: str, merchant_evidence_url: str) -> None:
        appeal = _load(self.appeals, appeal_id, "unknown_appeal")
        if str(gl.message.sender_address).lower() != appeal["merchant"]:
            raise Exception("only_named_merchant_can_respond")
        if appeal["status"] != "open" or _now() <= 0 or _now() > int(appeal["response_deadline"]):
            raise Exception("appeal_not_respondable")
        if gl.message.value < u256(int(appeal["claimant_bond_wei"])):
            raise Exception("merchant_bond_must_cover_claimant_bond")
        appeal["merchant_bond_wei"] = str(gl.message.value)
        appeal["merchant_evidence_url"] = _url(merchant_evidence_url, "invalid_merchant_evidence_url")
        appeal["status"] = "responded"
        self.appeals[appeal["appeal_id"]] = _json(appeal)

    @gl.public.write
    def resolve_payment_appeal(self, appeal_id: str) -> str:
        appeal = _load(self.appeals, appeal_id, "unknown_appeal")
        case = _load(self.cases, appeal["case_id"], "unknown_payment_case")
        if appeal["status"] != "responded":
            raise Exception("merchant_response_required")
        context = {"case_id": case["case_id"], "payment_commitment": case["payment_commitment"], "canonical_payment": case["canonical_payment"], "requested_resolution": appeal["requested_resolution"], "claimant_evidence_url": appeal["claimant_evidence_url"], "merchant_evidence_url": appeal["merchant_evidence_url"]}

        def leader_fn():
            return _json(_adjudicate(context))

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                proposed = _resolution(leader_result.calldata)
                independent = _resolution(_json(_adjudicate(context)))
                return all(proposed[key] == independent[key] for key in ("decision", "reason", "payment_commitment", "evidence_commitment", "terms_hash", "payment_evidence_hash", "claimant_evidence_hash", "merchant_evidence_hash"))
            except Exception:
                return False

        verdict = _resolution(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        resolution_id = "res_" + _parts([appeal["appeal_id"], verdict["evidence_commitment"], verdict["decision"]])[:20]
        if self.resolutions.get(resolution_id, ""):
            raise Exception("resolution_already_exists")
        resolution = {"resolution_id": resolution_id, "appeal_id": appeal["appeal_id"], **verdict, "created_at": _now(), "settled_at": 0}
        appeal["status"], appeal["resolution_id"] = "resolved", resolution_id
        case["status"], case["resolution_id"] = "resolved", resolution_id
        self.resolutions[resolution_id], self.appeals[appeal["appeal_id"]], self.cases[case["case_id"]] = _json(resolution), _json(appeal), _json(case)
        self.latest_resolution_id = resolution_id
        return resolution_id

    @gl.public.write
    def settle_payment_appeal(self, resolution_id: str) -> None:
        resolution = _load(self.resolutions, resolution_id, "unknown_resolution")
        appeal = _load(self.appeals, resolution["appeal_id"], "unknown_appeal")
        case = _load(self.cases, appeal["case_id"], "unknown_payment_case")
        if resolution["settled_at"] != 0 or appeal["status"] != "resolved" or case["status"] != "resolved":
            raise Exception("resolution_not_settleable")
        payment = u256(int(case["canonical_payment"]["reserved_amount_wei"]))
        claimant_bond, merchant_bond = u256(int(appeal["claimant_bond_wei"])), u256(int(appeal["merchant_bond_wei"]))
        if resolution["decision"] == "payer_upheld":
            _Account(Address(appeal["payer"])).emit_transfer(value=payment + claimant_bond + merchant_bond)
        elif resolution["decision"] == "merchant_upheld":
            _Account(Address(appeal["merchant"])).emit_transfer(value=payment + claimant_bond + merchant_bond)
        else:
            _Account(Address(appeal["payer"])).emit_transfer(value=payment + claimant_bond)
            _Account(Address(appeal["merchant"])).emit_transfer(value=merchant_bond)
        resolution["settled_at"], appeal["status"], case["status"] = _now(), "settled", "settled"
        self.resolutions[resolution_id], self.appeals[appeal["appeal_id"]], self.cases[case["case_id"]] = _json(resolution), _json(appeal), _json(case)

    @gl.public.write
    def release_unappealed_payment(self, case_id: str) -> None:
        case = _load(self.cases, case_id, "unknown_payment_case")
        if case["status"] != "funded" or _now() <= int(case["appeal_deadline"]):
            raise Exception("payment_not_releasable")
        _Account(Address(case["canonical_payment"]["merchant"])).emit_transfer(value=u256(int(case["canonical_payment"]["reserved_amount_wei"])))
        case["status"] = "released_unappealed"
        self.cases[case["case_id"]] = _json(case)

    @gl.public.write
    def recover_unresponded_appeal(self, appeal_id: str) -> None:
        appeal = _load(self.appeals, appeal_id, "unknown_appeal")
        case = _load(self.cases, appeal["case_id"], "unknown_payment_case")
        if appeal["status"] != "open" or _now() <= int(appeal["response_deadline"]):
            raise Exception("appeal_not_recoverable")
        _Account(Address(appeal["payer"])).emit_transfer(value=u256(int(case["canonical_payment"]["reserved_amount_wei"])) + u256(int(appeal["claimant_bond_wei"])))
        appeal["status"], case["status"] = "recovered_unresponded", "recovered_unresponded"
        self.appeals[appeal["appeal_id"]], self.cases[case["case_id"]] = _json(appeal), _json(case)


def _adjudicate(context: dict) -> dict:
    payment, terms = _render(context["canonical_payment"]["payment_evidence_url"]), _render(context["canonical_payment"]["terms_url"])
    claimant, merchant = _render(context["claimant_evidence_url"]), _render(context["merchant_evidence_url"])
    evidence = {"terms_hash": terms["hash"], "payment_evidence_hash": payment["hash"], "claimant_evidence_hash": claimant["hash"], "merchant_evidence_hash": merchant["hash"]}
    commitment = _parts([context["payment_commitment"], _json(evidence)])
    if not all(item["readable"] for item in (payment, terms, claimant, merchant)):
        return {"decision": "inconclusive", "reason": "source_unavailable", "payment_commitment": context["payment_commitment"], "evidence_commitment": commitment, **evidence}
    prompt = """You are a strict GenLayer payment-recourse judge. Use only supplied evidence. Return minified JSON: decision (payer_upheld|merchant_upheld|inconclusive) and reason (payment_not_owed|payment_owed|insufficient_evidence)."""
    payload = {"payment": context["canonical_payment"], "requested_resolution": context["requested_resolution"], "terms": terms["content"], "payment_evidence": payment["content"], "claimant_evidence": claimant["content"], "merchant_evidence": merchant["content"]}
    try:
        raw = json.loads(gl.nondet.exec_prompt(prompt + "\n" + _json(payload)))
    except Exception:
        raw = {}
    decision, reason = str(raw.get("decision", "inconclusive")).lower(), str(raw.get("reason", "insufficient_evidence")).lower()
    valid = ((decision == "payer_upheld" and reason == "payment_not_owed") or (decision == "merchant_upheld" and reason == "payment_owed") or (decision == "inconclusive" and reason == "insufficient_evidence"))
    if not valid:
        decision, reason = "inconclusive", "insufficient_evidence"
    return {"decision": decision, "reason": reason, "payment_commitment": context["payment_commitment"], "evidence_commitment": commitment, **evidence}


def _resolution(raw: str) -> dict:
    data = json.loads(raw)
    if data.get("decision") not in ("payer_upheld", "merchant_upheld", "inconclusive"):
        raise Exception("invalid_resolution")
    for key in ("reason", "payment_commitment", "evidence_commitment", "terms_hash", "payment_evidence_hash", "claimant_evidence_hash", "merchant_evidence_hash"):
        if not data.get(key):
            raise Exception("missing_resolution_field")
    return data


def _render(url: str) -> dict:
    try:
        content = " ".join(str(gl.nondet.web.render(url, mode="text")).split())
        return {"readable": len(content) >= 80, "content": content[:12000], "hash": hashlib.sha256(content.encode()).hexdigest()}
    except Exception:
        return {"readable": False, "content": "", "hash": hashlib.sha256(b"SOURCE_UNAVAILABLE").hexdigest()}


def _load(store, key: str, error: str) -> dict:
    raw = store.get(key.strip(), "")
    if not raw:
        raise Exception(error)
    return json.loads(raw)


def _now() -> int:
    try:
        return int(gl.message.block_timestamp)
    except Exception:
        return 0


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _parts(values: list) -> str:
    return hashlib.sha256("".join(str(len(str(item))) + ":" + str(item) for item in values).encode()).hexdigest()


def _hash(value: str, error: str) -> str:
    clean = value.strip().lower()
    if len(clean) != 64 or any(ch not in "0123456789abcdef" for ch in clean):
        raise Exception(error)
    return clean


def _clean(value: str, limit: int, error: str) -> str:
    clean = " ".join(value.strip().split())
    if not clean or len(clean) > limit:
        raise Exception(error)
    return clean


def _url(value: str, error: str) -> str:
    clean = value.strip()
    if not clean.startswith("https://") or len(clean) > 500:
        raise Exception(error)
    return clean


def _choice(value: str, choices: tuple) -> str:
    clean = value.strip().lower()
    if clean not in choices:
        raise Exception("invalid_requested_resolution")
    return clean
