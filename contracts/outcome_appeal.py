# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

"""Challengeable consensus rulings for disputed public outcomes."""

from genlayer import *
import hashlib
import json
import typing


class OutcomeAppeal(gl.Contract):
    case_count: u64
    latest_case_id: str
    latest_assessment_id: str
    latest_challenge_id: str
    latest_ruling_id: str
    cases: TreeMap[str, str]
    assessments: TreeMap[str, str]
    challenges: TreeMap[str, str]
    rulings: TreeMap[str, str]
    case_ids: DynArray[str]

    def __init__(self):
        self.case_count = u64(0)
        self.latest_case_id = ""
        self.latest_assessment_id = ""
        self.latest_challenge_id = ""
        self.latest_ruling_id = ""

    @gl.public.view
    def get_case(self, case_id: str) -> str:
        return self.cases.get(case_id.strip(), "")

    @gl.public.view
    def get_assessment(self, assessment_id: str) -> str:
        return self.assessments.get(assessment_id.strip(), "")

    @gl.public.view
    def get_challenge(self, challenge_id: str) -> str:
        return self.challenges.get(challenge_id.strip(), "")

    @gl.public.view
    def get_ruling(self, ruling_id: str) -> str:
        return self.rulings.get(ruling_id.strip(), "")

    @gl.public.view
    def list_case_ids(self) -> str:
        return json.dumps([item for item in self.case_ids], separators=(",", ":"))

    @gl.public.view
    def get_latest_case_id(self) -> str:
        return self.latest_case_id

    @gl.public.view
    def get_latest_assessment_id(self) -> str:
        return self.latest_assessment_id

    @gl.public.view
    def get_latest_challenge_id(self) -> str:
        return self.latest_challenge_id

    @gl.public.view
    def get_latest_ruling_id(self) -> str:
        return self.latest_ruling_id

    @gl.public.write
    def register_case(
        self,
        title: str,
        claimed_outcome: str,
        primary_source_url: str,
        corroborating_source_url: str,
        challenge_window_seconds: str,
    ) -> str:
        clean_title = _clean_text(title, 160, "title_required")
        outcome = _clean_text(claimed_outcome, 180, "outcome_required")
        window = _window(challenge_window_seconds)
        sources = [_source("primary", primary_source_url), _source("corroborating", corroborating_source_url)]

        def leader_fn():
            snapshots = _render_sources(sources)
            return json.dumps(_baseline(clean_title, outcome, snapshots), separators=(",", ":"))

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                leader = json.loads(leader_result.value)
                local = _baseline(clean_title, outcome, _render_sources(sources))
                return _canonical_json(leader) == _canonical_json(local)
            except Exception:
                return False

        baseline = json.loads(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        case_id = "case_" + _sha256(clean_title + "|" + outcome + "|" + baseline["baseline_hash"])[:20]
        if len(self.cases.get(case_id, "")) > 0:
            raise Exception("case_already_registered")
        now = _now()
        record = {
            "id": case_id,
            "title": clean_title,
            "claimed_outcome": outcome,
            "source_urls": [item["canonical_url"] for item in sources],
            "baseline_hash": baseline["baseline_hash"],
            "baseline_snapshot_commitments": baseline["snapshot_commitments"],
            "challenge_window_seconds": window,
            "status": "open",
            "assessment_id": "",
            "challenge_id": "",
            "ruling_id": "",
            "created_at": now,
        }
        self.cases[case_id] = _canonical_json(record)
        self.case_ids.append(case_id)
        self.case_count = u64(int(self.case_count) + 1)
        self.latest_case_id = case_id
        return case_id

    @gl.public.write
    def assess_case(self, case_id: str, evidence_url: str) -> str:
        case = _load_case(self, case_id)
        if case["status"] != "open":
            raise Exception("case_not_open_for_assessment")
        evidence = _source("assessment_evidence", evidence_url)
        sources = [_source("primary", case["source_urls"][0]), _source("corroborating", case["source_urls"][1]), evidence]

        def leader_fn():
            return _canonical_json(_assess(case, _render_sources(sources)))

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                leader = json.loads(leader_result.value)
                local = _assess(case, _render_sources(sources))
                return _assessment_equal(leader, local)
            except Exception:
                return False

        verdict = json.loads(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        assessment_id = "asm_" + _sha256(case["id"] + "|" + verdict["assessment_hash"])[:20]
        if len(self.assessments.get(assessment_id, "")) > 0:
            raise Exception("assessment_already_exists")
        assessment = {
            "id": assessment_id,
            "case_id": case["id"],
            "outcome": verdict["outcome"],
            "confidence": verdict["confidence"],
            "summary": verdict["summary"],
            "evidence_hash": verdict["evidence_hash"],
            "snapshot_commitments": json.loads(verdict["snapshot_commitments_json"]),
            "assessment_hash": verdict["assessment_hash"],
            "created_at": _now(),
        }
        case["status"] = "assessed"
        case["assessment_id"] = assessment_id
        case["challenge_deadline"] = _now() + int(case["challenge_window_seconds"])
        self.cases[case["id"]] = _canonical_json(case)
        self.assessments[assessment_id] = _canonical_json(assessment)
        self.latest_assessment_id = assessment_id
        return assessment_id

    @gl.public.write
    def challenge_assessment(self, case_id: str, assessment_id: str, counterevidence_url: str) -> str:
        case = _load_case(self, case_id)
        if case["status"] != "assessed" or case["assessment_id"] != assessment_id.strip():
            raise Exception("assessment_not_challengeable")
        if _now() > int(case["challenge_deadline"]):
            raise Exception("challenge_window_closed")
        counter = _source("counterevidence", counterevidence_url)
        assessment = _load_assessment(self, assessment_id)
        challenge_id = "chg_" + _sha256(case["id"] + "|" + assessment["assessment_hash"] + "|" + counter["canonical_url"])[:20]
        if len(self.challenges.get(challenge_id, "")) > 0:
            raise Exception("challenge_already_exists")
        snapshot = _render_sources([counter])[0]
        challenge = {
            "id": challenge_id,
            "case_id": case["id"],
            "assessment_id": assessment["id"],
            "counterevidence_url": counter["canonical_url"],
            "counterevidence_snapshot_hash": snapshot["snapshot_hash"],
            "status": "pending_resolution",
            "created_at": _now(),
        }
        case["status"] = "challenged"
        case["challenge_id"] = challenge_id
        self.cases[case["id"]] = _canonical_json(case)
        self.challenges[challenge_id] = _canonical_json(challenge)
        self.latest_challenge_id = challenge_id
        return challenge_id

    @gl.public.write
    def resolve_challenge(self, case_id: str, challenge_id: str) -> str:
        case = _load_case(self, case_id)
        if case["status"] != "challenged" or case["challenge_id"] != challenge_id.strip():
            raise Exception("challenge_not_pending")
        assessment = _load_assessment(self, case["assessment_id"])
        challenge = _load_challenge(self, challenge_id)
        sources = [_source("primary", case["source_urls"][0]), _source("corroborating", case["source_urls"][1]), _source("counterevidence", challenge["counterevidence_url"])]

        def leader_fn():
            return _canonical_json(_resolve(case, assessment, challenge, _render_sources(sources)))

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                leader = json.loads(leader_result.value)
                local = _resolve(case, assessment, challenge, _render_sources(sources))
                return _resolution_equal(leader, local)
            except Exception:
                return False

        resolution = json.loads(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        challenge["status"] = "resolved"
        challenge["resolution_outcome"] = resolution["outcome"]
        challenge["resolution_hash"] = resolution["resolution_hash"]
        challenge["snapshot_commitments"] = json.loads(resolution["snapshot_commitments_json"])
        case["status"] = "resolved"
        self.challenges[challenge["id"]] = _canonical_json(challenge)
        self.cases[case["id"]] = _canonical_json(case)
        return challenge["id"]

    @gl.public.write
    def finalize_ruling(self, case_id: str) -> str:
        case = _load_case(self, case_id)
        if case["status"] == "assessed" and _now() <= int(case["challenge_deadline"]):
            raise Exception("challenge_window_still_open")
        if case["status"] not in ["assessed", "resolved"]:
            raise Exception("case_not_finalizable")
        assessment = _load_assessment(self, case["assessment_id"])
        final_outcome = assessment["outcome"]
        resolution_hash = ""
        if case["status"] == "resolved":
            challenge = _load_challenge(self, case["challenge_id"])
            final_outcome = challenge["resolution_outcome"]
            resolution_hash = challenge["resolution_hash"]
        ruling_id = "rul_" + _sha256(case["id"] + "|" + assessment["assessment_hash"] + "|" + resolution_hash + "|" + final_outcome)[:20]
        if len(self.rulings.get(ruling_id, "")) > 0:
            raise Exception("ruling_already_finalized")
        ruling = {"id": ruling_id, "case_id": case["id"], "assessment_id": assessment["id"], "challenge_id": case["challenge_id"], "outcome": final_outcome, "assessment_hash": assessment["assessment_hash"], "resolution_hash": resolution_hash, "case_baseline_hash": case["baseline_hash"], "finalized_at": _now()}
        case["status"] = "finalized"
        case["ruling_id"] = ruling_id
        self.cases[case["id"]] = _canonical_json(case)
        self.rulings[ruling_id] = _canonical_json(ruling)
        self.latest_ruling_id = ruling_id
        return ruling_id


def _baseline(title: str, outcome: str, snapshots: typing.Sequence[dict]) -> dict:
    commitments = _commitments(snapshots)
    return {"baseline_hash": _sha256(_canonical_json({"title": title, "claimed_outcome": outcome, "snapshot_commitments": commitments})), "snapshot_commitments": commitments}


def _assess(case: dict, snapshots: typing.Sequence[dict]) -> dict:
    commitments = _commitments(snapshots)
    prompt = """You are a GenLayer consensus judge. Decide whether the claim is upheld, rejected, or inconclusive using only the rendered public evidence. Return minified JSON with outcome, confidence, summary. confidence must be an integer 0-100."""
    data = json.loads(gl.nondet.exec_prompt(prompt + "\nCase: " + _canonical_json({"title": case["title"], "claimed_outcome": case["claimed_outcome"]}) + "\nEvidence: " + _canonical_json(snapshots)))
    normalized = {"outcome": _choice(str(data.get("outcome", "inconclusive")).lower(), ["upheld", "rejected", "inconclusive"]), "confidence": _u8(data.get("confidence", 0)), "summary": _clean_text(str(data.get("summary", "inconclusive")), 280, "summary_required")}
    if sum(1 for item in snapshots if item["snapshot_hash"]) < 2:
        normalized["outcome"] = "inconclusive"
        normalized["confidence"] = min(normalized["confidence"], 40)
    normalized["evidence_hash"] = _sha256(_canonical_json({"commitments": commitments, "normalized": normalized}))
    normalized["snapshot_commitments_json"] = _canonical_json(commitments)
    normalized["assessment_hash"] = _sha256(_canonical_json({"case_id": case["id"], "evidence_hash": normalized["evidence_hash"], "baseline_hash": case["baseline_hash"]}))
    return normalized


def _resolve(case: dict, assessment: dict, challenge: dict, snapshots: typing.Sequence[dict]) -> dict:
    commitments = _commitments(snapshots)
    prompt = """You are a GenLayer appeal judge. Re-evaluate the stated claim after a challenge. Return minified JSON with outcome, confidence, summary. outcome must be upheld, rejected, or inconclusive."""
    context = {"claim": case["claimed_outcome"], "initial_outcome": assessment["outcome"], "counterevidence_url": challenge["counterevidence_url"]}
    data = json.loads(gl.nondet.exec_prompt(prompt + "\nContext: " + _canonical_json(context) + "\nEvidence: " + _canonical_json(snapshots)))
    normalized = {"outcome": _choice(str(data.get("outcome", "inconclusive")).lower(), ["upheld", "rejected", "inconclusive"]), "confidence": _u8(data.get("confidence", 0)), "summary": _clean_text(str(data.get("summary", "inconclusive")), 280, "summary_required")}
    normalized["snapshot_commitments_json"] = _canonical_json(commitments)
    normalized["resolution_hash"] = _sha256(_canonical_json({"case_id": case["id"], "assessment_hash": assessment["assessment_hash"], "challenge_id": challenge["id"], "commitments": commitments, "normalized": normalized}))
    return normalized


def _render_sources(sources: typing.Sequence[dict]) -> typing.Sequence[dict]:
    result = []
    for source in sources:
        try:
            text = gl.nondet.web.render(source["canonical_url"], mode="text")[:6000]
            error = ""
        except Exception as exc:
            text = ""
            error = str(exc)[:240]
        result.append({"role": source["role"], "canonical_url": source["canonical_url"], "snapshot_hash": _sha256(text) if text else "", "fetch_error_hash": _sha256(error) if error else ""})
    return result


def _commitments(snapshots: typing.Sequence[dict]) -> typing.Sequence[dict]:
    return [{"role": item["role"], "canonical_url": item["canonical_url"], "snapshot_hash": item["snapshot_hash"], "fetch_error_hash": item["fetch_error_hash"]} for item in snapshots]


def _assessment_equal(a: dict, b: dict) -> bool:
    return all(a[key] == b[key] for key in ["outcome", "confidence", "evidence_hash", "snapshot_commitments_json", "assessment_hash"])


def _resolution_equal(a: dict, b: dict) -> bool:
    return all(a[key] == b[key] for key in ["outcome", "confidence", "snapshot_commitments_json", "resolution_hash"])


def _load_case(contract, case_id: str) -> dict:
    value = contract.cases.get(case_id.strip(), "")
    if not value:
        raise Exception("unknown_case")
    return json.loads(value)


def _load_assessment(contract, assessment_id: str) -> dict:
    value = contract.assessments.get(assessment_id.strip(), "")
    if not value:
        raise Exception("unknown_assessment")
    return json.loads(value)


def _load_challenge(contract, challenge_id: str) -> dict:
    value = contract.challenges.get(challenge_id.strip(), "")
    if not value:
        raise Exception("unknown_challenge")
    return json.loads(value)


def _source(role: str, url: str) -> dict:
    clean = str(url).strip()
    if not clean.startswith("https://") or len(clean) > 280:
        raise Exception(role + "_url_required")
    return {"role": role, "canonical_url": clean}


def _clean_text(value: str, limit: int, error: str) -> str:
    clean = " ".join(str(value).strip().split())
    if not clean or len(clean) > limit:
        raise Exception(error)
    return clean


def _window(value: str) -> int:
    amount = int(str(value).strip())
    if amount < 60 or amount > 604800:
        raise Exception("invalid_challenge_window")
    return amount


def _choice(value: str, choices: typing.Sequence[str]) -> str:
    return value if value in choices else "inconclusive"


def _u8(value) -> int:
    return max(0, min(100, int(value)))


def _canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> int:
    try:
        return int(gl.block.timestamp)
    except Exception:
        return 0
