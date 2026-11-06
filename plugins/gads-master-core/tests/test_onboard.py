"""Onboarding acceptance: saved HTML fixtures only, no live network."""
import json
from pathlib import Path

from common.schema import errors
from memory import context as C
from onboard import draft, extract, fetch, questions

FX = Path(__file__).parent / "fixtures" / "onboard"
ACC = "acme-1"


def sig(name, url):
    return extract.extract((FX / name).read_text(), url)


def saas_draft():
    company = [sig("company_saas.html", "https://flowly.example/")]
    comps = {"approvo.example": [sig("competitor_saas.html", "https://approvo.example/")],
             "deskshop.example": [sig("competitor_store.html", "https://deskshop.example/")]}
    return draft.build(company, comps)


def test_extract_signals_structured_only():
    s = sig("company_saas.html", "https://flowly.example/")
    assert {"trial", "demo"} <= set(s["ctas"])
    assert {"gtm", "ga4", "consent_banner"} <= set(s["trackers"])
    assert s["hreflang"] == ["en-us", "pt-br", "x-default"] and s["has_pricing_page"]
    assert {"amount": 29.0, "currency": "USD", "period": "month"} in s["prices"]
    assert "company" in s["form_fields"] and "SoftwareApplication" in s["schema_types"]
    assert "ignore previous" not in json.dumps(s).lower()  # page text is never copied


def test_draft_has_provenance_on_every_field_and_unknowns():
    d = saas_draft()
    assert set(d["fields"]) == set(C.FIELDS)
    for name, f in d["fields"].items():
        assert {"value", "source", "confidence", "evidence", "captured_at"} <= set(f), name
        if f["source"] == "inferred":
            assert f["evidence"] and all(e.startswith("https://") for e in f["evidence"]) and f["ttl_days"]
    fv = {k: v["value"] for k, v in d["fields"].items()}
    assert fv["business_model"] == "saas_hybrid" and fv["buyer_type"] == "b2b"
    assert fv["price_point"]["currency"] == "USD" and fv["price_point"]["metric"] == "mrr"
    assert {m["language"] for m in fv["markets"]} == {"en", "pt"}
    assert fv["tracking_maturity"] == "basic" and d["fields"]["tracking_maturity"]["confidence"] == "low"
    for undeducible in ("vertical", "primary_offer", "goal", "owner_hypothesis_constraint", "do_not_touch", "seasonality"):
        assert d["fields"][undeducible]["source"] == "unknown"
    assert all(c["evidence_type"] == "reported" for c in fv["competitors"])
    check = {c["domain"]: c for c in d["competitor_check"]}
    assert check["approvo.example"]["likely_direct_competitor"] is True
    assert check["deskshop.example"]["likely_direct_competitor"] is False
    assert "ignore previous" not in json.dumps(d).lower()


def test_draft_merges_and_validates(tmp_path):
    obj = C.merge_draft(tmp_path, ACC, saas_draft())
    assert not errors("business-context.v1", obj)


def test_questions_only_remaining_high_impact(tmp_path):
    d = saas_draft()
    qs = questions.select(d["fields"], C.profile_get(tmp_path, ACC), "saas")
    ids = [q["id"] for q in qs]
    assert len(qs) <= 7 and ids[:3] == ["Q01", "Q02", "Q03"]
    assert "Q11" not in ids  # markets were deduced
    assert "Q15" not in ids and "Q17" not in ids  # ecommerce-only
    assert all(q["allow_dont_know"] and q["default"] for q in qs)
    C.profile_set(tmp_path, ACC, "targets.throughput", 40)
    assert "Q02" not in [q["id"] for q in questions.select(d["fields"], C.profile_get(tmp_path, ACC), "saas")]


def test_ecommerce_fixture():
    d = draft.build([sig("company_ecommerce.html", "https://cafe.example/")], {})
    fv = {k: v["value"] for k, v in d["fields"].items()}
    assert fv["business_model"] == "ecommerce" and fv["sales_motion"] == "self_serve"
    assert fv["price_point"]["currency"] == "BRL" and fv["price_point"]["range"] == [49.9, 150.0]  # 150 = free-shipping threshold mention
    assert fv["markets"][0]["language"] == "pt" and fv["markets"][0]["country"] == "BR"


def test_js_rendered_page_asks_instead_of_guessing():
    d = draft.build([sig("js_shell.html", "https://spa.example/")], {})
    assert d["fields"]["business_model"]["source"] == "unknown" and d["notes"]


def test_fetch_refuses_google_serp_without_network():
    ok, why = fetch.allowed("https://www.google.com/search?q=standing+desk")
    assert not ok and "hard stop" in why
