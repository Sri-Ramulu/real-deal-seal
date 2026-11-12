"""The Merchant Passport: a W3C Verifiable Credential (Data Model 2.0) signed with Ed25519 (eddsa-jcs-2022).

Plain code decides whether a seal is genuine. A model is never asked.
A valid signature proves the facts were not changed since Real Deal Seal signed them. It does not make PayPal the
issuer, and it does not by itself prove the facts are true: the evidence class on each fact says where it came from.

Keys live in a small key ring. Rotating adds a new signing key and keeps the old one trusted for verification;
revoking a key makes everything it signed fail.
"""
from __future__ import annotations

import copy
import datetime
import hashlib
import json
import os
import uuid

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from . import config, store, warehouse

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
CONTEXT = ["https://www.w3.org/ns/credentials/v2", {"@vocab": "https://realdealseal.example/ns#"}]
KEYRING = config.VAR / "keyring.json"


def b58encode(b: bytes) -> str:
    n, out = int.from_bytes(b, "big"), ""
    while n:
        n, r = divmod(n, 58)
        out = _B58[r] + out
    return "1" * (len(b) - len(b.lstrip(b"\0"))) + out


def b58decode(s: str) -> bytes:
    n = 0
    for ch in s:
        n = n * 58 + _B58.index(ch)
    body = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return b"\0" * (len(s) - len(s.lstrip("1"))) + body


def jcs(obj) -> bytes:
    """JSON Canonicalization (RFC 8785) for the values we sign: strings, integers, booleans, null. No floats."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


# ---- key ring ----------------------------------------------------------------------------------------------------
def keyring() -> list[dict]:
    if not KEYRING.exists():
        seed = os.environ.get("RDS_ISSUER_SEED_HEX") or os.urandom(32).hex()
        _save([{"key_id": "key-1", "seed_hex": seed, "status": "active", "created_at": store.now()}])
    return json.loads(KEYRING.read_text())


def _save(keys: list[dict]):
    KEYRING.write_text(json.dumps(keys, indent=1))
    KEYRING.chmod(0o600)


def _private(key: dict) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(key["seed_hex"]))


def _public_bytes(key: dict) -> bytes:
    return _private(key).public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _multibase(key: dict) -> str:
    return "z" + b58encode(b"\xed\x01" + _public_bytes(key))


def active_key() -> dict:
    return next(k for k in keyring() if k["status"] == "active")


def rotate_key() -> str:
    """New signing key. The previous key is retired: it signs nothing new but still verifies what it signed."""
    keys = keyring()
    for k in keys:
        if k["status"] == "active":
            k["status"] = "retired"
    new_id = f"key-{len(keys) + 1}"
    keys.append({"key_id": new_id, "seed_hex": os.urandom(32).hex(), "status": "active", "created_at": store.now()})
    _save(keys)
    store.audit("issuer", "key.rotate", new_id)
    return new_id


def revoke_key(key_id: str):
    keys = keyring()
    for k in keys:
        if k["key_id"] == key_id:
            k["status"] = "revoked"
    _save(keys)
    store.audit("issuer", "key.revoke", key_id)


def method_for(key_id: str) -> str:
    return f"{config.did()}#{key_id}"


def verification_method() -> str:
    return method_for(active_key()["key_id"])


def public_key_multibase() -> str:
    return _multibase(active_key())


def did_document() -> dict:
    keys = [k for k in keyring() if k["status"] != "revoked"]
    return {"@context": ["https://www.w3.org/ns/did/v1", "https://w3id.org/security/multikey/v1"], "id": config.did(),
            "verificationMethod": [{"id": method_for(k["key_id"]), "type": "Multikey", "controller": config.did(),
                                    "publicKeyMultibase": _multibase(k)} for k in keys],
            "assertionMethod": [method_for(k["key_id"]) for k in keys]}


# ---- signing -----------------------------------------------------------------------------------------------------
def _hash_data(doc: dict, proof_config: dict) -> bytes:
    return hashlib.sha256(jcs(proof_config)).digest() + hashlib.sha256(jcs(doc)).digest()


def sign(doc: dict, key: Ed25519PrivateKey | None = None, method: str | None = None) -> dict:
    doc = copy.deepcopy(doc)
    doc.pop("proof", None)
    k = active_key()
    proof = {"type": "DataIntegrityProof", "cryptosuite": "eddsa-jcs-2022", "created": doc["validFrom"],
             "verificationMethod": method or method_for(k["key_id"]), "proofPurpose": "assertionMethod"}
    sig = (key or _private(k)).sign(_hash_data(doc, {**proof, "@context": doc["@context"]}))
    return {**doc, "proof": {**proof, "proofValue": "z" + b58encode(sig)}}


STATUS_LIST_BITS = 131072  # the W3C minimum (16 KB), so a list reveals nothing about how many credentials exist
RENEW_DAYS = 14             # a seal whose facts haven't changed is re-signed this many days before it expires


def content_key(kind: str, subject: dict) -> str:
    return hashlib.sha256(jcs([kind, subject])).hexdigest()


def status_list_url() -> str:
    return f"{config.PUBLIC_URL}/api/credentials/status-list/revocation"


def _envelope(kind: str, subject: dict, valid_from: datetime.date, status_index: int | None = None) -> dict:
    """The validity window starts on the day of issue, not on the date of the data, so renewing a seal moves it forward.
    The id covers the content and the issue day: unchanged facts re-published the same day give the same credential."""
    cid = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, content_key(kind, subject) + valid_from.isoformat()))
    status = [{"id": f"{config.PUBLIC_URL}/api/credentials/status?id={cid}", "type": "RealDealSealStatus"}]
    if status_index is not None:
        status.insert(0, {"id": f"{status_list_url()}#{status_index}", "type": "BitstringStatusListEntry", "statusPurpose": "revocation",
                          "statusListIndex": str(status_index), "statusListCredential": status_list_url()})
    return {
        "@context": CONTEXT, "id": cid, "type": ["VerifiableCredential", kind],
        "issuer": {"id": config.did(), "name": config.ISSUER_NAME},
        "validFrom": f"{valid_from.isoformat()}T00:00:00Z",
        "validUntil": f"{(valid_from + datetime.timedelta(days=config.SEAL_VALID_DAYS)).isoformat()}T00:00:00Z",
        "credentialStatus": status,
        "credentialSubject": subject,
    }


def limitations(p: dict) -> list[str]:
    out = ["Issued by Real Deal Seal, a hackathon project. PayPal supplied the sandbox records, not the signature.",
           "A valid signature shows these facts were not changed after signing. Each fact's evidence class says how far it can be relied on."]
    if p["evidence_basis"] == "paypal_record":
        out.append("Payment facts come from the PayPal sandbox (test environment), not live commerce.")
    else:
        out.append("Payment facts come from the business's own imported records and are not confirmed by PayPal. They cannot earn the seal.")
    if p["has_simulated_evidence"]:
        out.append("Order dates, fulfilment speed and dispute outcomes are simulated for the demo and labelled 'simulated'.")
    return out


def build(merchant_id: str, valid_from: datetime.date | None = None, status_index: int | None = None) -> dict | None:
    """Assemble the unsigned passport from gold. Only whole numbers and text are signed. Facts the owner chose
    not to disclose are left out; rule results always stay in."""
    p = warehouse.one("SELECT * FROM gold.merchant_passport WHERE merchant_id = ? AND has_record", [merchant_id])
    if not p:
        return None
    facts = warehouse.rows("""SELECT metric, label, value, unit, numerator, denominator, window_label, evidence_class, layer
                              FROM gold.fact_metric_observations WHERE merchant_id = ? AND NOT (is_optional_to_disclose AND list_contains(?, metric))
                              ORDER BY display_order""", [merchant_id, p["hidden_metrics"]])
    rules = warehouse.rows("SELECT rule, rule_label, met, measured FROM gold.fact_rule_results WHERE merchant_id = ? ORDER BY rule_order", [merchant_id])
    subject = {
        "id": f"urn:rds:merchant:{merchant_id}", "name": p["merchant_name"], "businessType": p["business_type"], "ruleSet": p["ruleset"],
        "standing": p["standing"], "headline": p["headline"], "evidenceBasis": p["evidence_basis"],
        "criteriaVersion": p["criteria_version"], "dataAsOf": p["data_as_of"],
        "facts": [{"metric": f["metric"], "label": f["label"], "value": f["value"], "unit": f["unit"], "numerator": f["numerator"],
                   "denominator": f["denominator"], "window": f["window_label"], "evidenceClass": f["evidence_class"], "layer": f["layer"]} for f in facts],
        "rules": [{"rule": r["rule"], "label": r["rule_label"], "met": r["met"], "measured": r["measured"]} for r in rules],
        "notDisclosed": sorted(p["hidden_metrics"]),
        "limitations": limitations(p),
    }
    return _envelope("RealDealSealPassport", subject, valid_from or datetime.datetime.now(datetime.timezone.utc).date(), status_index)


# ---- registry ----------------------------------------------------------------------------------------------------
def register(cred: dict, merchant_id: str, kind: str):
    """Add the credential to the registry. The id is derived from the signed content, so re-publishing unchanged
    facts brings the same credential back to active rather than minting a duplicate."""
    if store.run("UPDATE credentials SET status = 'active', status_reason = 'Published again by the owner.' WHERE credential_id = ?", [cred["id"]]):
        store.audit("issuer", "credential.reactivate", cred["id"], merchant_id=merchant_id)
        return
    index = next((int(s["statusListIndex"]) for s in _status_entries(cred) if s.get("type") == "BitstringStatusListEntry"), None)
    store.insert("credentials", {"credential_id": cred["id"], "merchant_id": merchant_id, "kind": kind, "status": "active", "status_index": index,
                                 "key_id": cred["proof"]["verificationMethod"].split("#")[1], "data_as_of": cred["credentialSubject"].get("dataAsOf"),
                                 "issued_at": store.now(), "valid_until": cred["validUntil"], "document": json.dumps(cred)}, or_ignore=True)
    store.audit("issuer", "credential.issue", cred["id"], merchant_id=merchant_id, detail={"kind": kind})


def set_status(credential_id: str, status: str, reason: str):
    store.run("UPDATE credentials SET status = ?, status_reason = ? WHERE credential_id = ?", [status, reason, credential_id])
    store.audit("issuer", f"credential.{status}", credential_id, detail={"reason": reason})


def status_of(credential_id: str) -> dict:
    c = store.one("SELECT credential_id, status, status_reason, valid_until, kind FROM credentials WHERE credential_id = ?", [credential_id])
    return c or {"credential_id": credential_id, "status": "unknown", "status_reason": "This credential is not in the issuer's registry."}


def _status_entries(cred: dict) -> list[dict]:
    st = cred.get("credentialStatus") or []
    return st if isinstance(st, list) else [st]


def _next_status_index() -> int:
    row = store.one("SELECT max(status_index) AS m FROM credentials")
    return 0 if not row or row["m"] is None else int(row["m"]) + 1


def issue(merchant_id: str, today: datetime.date | None = None) -> dict | None:
    """The business's current public passport. The active one is kept while its facts are unchanged and it has more
    than RENEW_DAYS left; otherwise a fresh one is signed and the old one is marked superseded, with the reason."""
    p = warehouse.one("SELECT passport_published, has_record, standing FROM gold.merchant_passport WHERE merchant_id = ?", [merchant_id])
    if not p or not p["has_record"] or not p["passport_published"] or p["standing"] == "withdrawn":
        return None
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    draft = build(merchant_id, today)
    active = store.one("SELECT * FROM credentials WHERE merchant_id = ? AND kind = 'passport' AND status = 'active'", [merchant_id])
    if active:
        current = json.loads(active["document"])
        same = content_key("RealDealSealPassport", current["credentialSubject"]) == content_key("RealDealSealPassport", draft["credentialSubject"])
        days_left = (datetime.date.fromisoformat(current["validUntil"][:10]) - today).days
        if same and days_left > RENEW_DAYS:
            return current
        set_status(active["credential_id"], "superseded",
                   "Renewed before it expired; the facts are unchanged." if same else "A newer passport was issued from fresher records.")
    same_day = store.one("SELECT document FROM credentials WHERE credential_id = ?", [draft["id"]])
    if same_day:  # re-published the same day with the same facts: bring that credential back
        register(json.loads(same_day["document"]), merchant_id, "passport")
        return json.loads(same_day["document"])
    cred = sign(build(merchant_id, today, _next_status_index()))
    register(cred, merchant_id, "passport")
    return cred


def status_list_bits() -> bytes:
    """The revocation bitstring: bit i is 1 when the credential at status index i is revoked (index 0 is the leftmost bit)."""
    bits = bytearray(STATUS_LIST_BITS // 8)
    for r in store.q("SELECT status_index FROM credentials WHERE status = 'revoked' AND status_index IS NOT NULL"):
        i = int(r["status_index"])
        bits[i // 8] |= 0x80 >> (i % 8)
    return bytes(bits)


def status_list_credential() -> dict:
    """W3C Bitstring Status List v1.0 credential, signed by the issuer, so any verifier can check revocation offline."""
    import base64
    import gzip
    encoded = "u" + base64.urlsafe_b64encode(gzip.compress(status_list_bits(), mtime=0)).decode().rstrip("=")
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    doc = {"@context": CONTEXT, "id": status_list_url(), "type": ["VerifiableCredential", "BitstringStatusListCredential"],
           "issuer": {"id": config.did(), "name": config.ISSUER_NAME}, "validFrom": now.isoformat().replace("+00:00", "Z"),
           "credentialSubject": {"id": status_list_url() + "#list", "type": "BitstringStatusList", "statusPurpose": "revocation",
                                 "encodedList": encoded}}
    return sign(doc)


def forged_sample() -> dict:
    """What Linen Palace shows: a copied passport, edited to its own name and signed with a key nobody trusts."""
    doc = build("lydia")
    doc["credentialSubject"].update({"id": "urn:rds:merchant:palace", "name": "Linen Palace"})
    return sign(doc, key=Ed25519PrivateKey.generate(), method="did:web:linen-palace.example#key-1")


def verify(cred, today: datetime.date | None = None) -> dict:
    """Step-by-step check. `result` is one of genuine, edited, forged, expired, withdrawn, superseded, unreadable."""
    steps = []

    def step(name, ok, detail):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})
        return ok

    def done(result, summary):
        return {"result": result, "genuine": result == "genuine", "summary": summary, "steps": steps,
                "checked_by": "deterministic code (Ed25519, eddsa-jcs-2022), never a model"}

    if isinstance(cred, str):
        try:
            cred = json.loads(cred)
        except Exception:
            cred = None
    proof = cred.get("proof") if isinstance(cred, dict) else None
    if not step("Readable credential with a proof", isinstance(proof, dict) and "proofValue" in proof and "credentialSubject" in cred,
                "A seal is a signed document. A badge image or a sentence is not a seal."):
        return done("unreadable", "This is not a signed seal. A picture or a claim proves nothing.")
    method = str(proof.get("verificationMethod", ""))
    key = next((k for k in keyring() if method == method_for(k["key_id"])), None)
    if not step("Signed by a key Real Deal Seal publishes", key is not None and key["status"] != "revoked",
                f"Signer: {method}. " + ("That key was revoked by the issuer." if key and key["status"] == "revoked"
                                         else f"That key is published by Real Deal Seal at {config.did()}." if key
                                         else f"Trusted keys belong to {config.did()}.")):
        return done("forged", "Signed by a key Real Deal Seal does not publish. Treat it as forged.")
    doc = {k: v for k, v in cred.items() if k != "proof"}
    config_ = {k: v for k, v in proof.items() if k != "proofValue"}
    try:
        Ed25519PublicKey.from_public_bytes(_public_bytes(key)).verify(
            b58decode(proof["proofValue"][1:]), _hash_data(doc, {**config_, "@context": doc.get("@context")}))
        ok = True
    except (InvalidSignature, ValueError, KeyError):
        ok = False
    if not step("Signature matches every signed fact", ok, "Change one number and the signature stops matching."):
        return done("edited", "The contents were changed after signing. Do not rely on any number in it.")
    today = today or datetime.date.today()
    until = datetime.date.fromisoformat(cred["validUntil"][:10])
    if not step("Still inside its validity period", today <= until, f"Valid until {until.isoformat()}."):
        return done("expired", "The seal has expired. Ask for a fresh one.")
    st = status_of(cred["id"])
    if not step("Not withdrawn by the issuer", st["status"] != "revoked", st.get("status_reason") or "Checked against the issuer's registry."):
        return done("withdrawn", "The issuer withdrew this seal. It can no longer be relied on.")
    s = cred["credentialSubject"]
    if not step("Still the current version", st["status"] != "superseded", st.get("status_reason") or "No newer version exists."):
        return done("superseded", f"Genuine when issued, but a newer document for {s.get('name', 'this business')} replaces it. Ask for the current one.")
    return done("genuine", f"Genuine. {s['name']}: {s.get('headline', 'signed statement')} (data as of {s.get('dataAsOf', 'n/a')}).")
