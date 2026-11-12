import copy
import datetime

from rds import passport, store


def test_a_fresh_seal_is_genuine():
    r = passport.verify(passport.issue("lydia"))
    assert r["result"] == "genuine" and all(s["ok"] for s in r["steps"])


def test_changing_one_number_breaks_the_seal():
    cred = passport.issue("martha")
    cred["credentialSubject"]["facts"][3]["value"] = 99
    assert passport.verify(cred)["result"] == "edited"


def test_changing_the_standing_breaks_the_seal():
    cred = passport.issue("martha")
    cred["credentialSubject"]["standing"] = "sealed"
    assert passport.verify(cred)["result"] == "edited"


def test_a_seal_signed_by_an_unknown_key_is_forged():
    assert passport.verify(passport.forged_sample())["result"] == "forged"


def test_copying_our_key_id_onto_a_forged_seal_does_not_help():
    cred = passport.forged_sample()
    cred["proof"]["verificationMethod"] = passport.verification_method()
    assert passport.verify(cred)["result"] == "edited"


def test_a_badge_or_a_sentence_is_not_a_seal():
    assert passport.verify("Real Deal Seal ✓ PayPal Verified Seller")["result"] == "unreadable"
    assert passport.verify({"standing": "sealed"})["result"] == "unreadable"


def test_an_old_seal_expires():
    assert passport.verify(passport.issue("lydia"), today=datetime.date(2027, 6, 1))["result"] == "expired"


def test_a_withdrawn_seal_stops_verifying():
    cred = copy.deepcopy(passport.issue("priscilla"))
    passport.set_status(cred["id"], "revoked", "merchant disconnected")
    assert passport.verify(cred)["result"] == "withdrawn"
    passport.set_status(cred["id"], "active", "")


def test_shops_without_a_paypal_record_get_no_seal():
    assert passport.issue("babel") is None


def test_the_credential_names_this_project_as_issuer_not_paypal():
    cred = passport.issue("lydia")
    assert "not PayPal" in cred["issuer"]["name"]
    assert any("not the signature" in l for l in cred["credentialSubject"]["limitations"])


def test_only_whole_numbers_and_text_are_signed():
    def walk(v):
        assert not isinstance(v, float), v
        for x in (v.values() if isinstance(v, dict) else v if isinstance(v, list) else []):
            walk(x)
    walk(passport.build("lydia"))
