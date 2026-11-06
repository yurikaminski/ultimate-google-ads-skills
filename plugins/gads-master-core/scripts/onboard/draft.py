"""Infer a business-context draft from extracted signals. Provenance on every field."""
from __future__ import annotations

from datetime import date

FIELDS = ["business_model", "buyer_type", "vertical", "primary_offer", "price_point", "markets",
          "sales_motion", "sales_cycle_days", "conversion_path", "seasonality", "competitors",
          "brand_strength", "tracking_maturity", "goal", "owner_hypothesis_constraint",
          "regulatory_flags", "do_not_touch"]
TTL = 90


def _f(value, conf, evidence, source="inferred"):
    return {"value": value, "source": source, "confidence": conf, "evidence": sorted(set(evidence)),
            "captured_at": date.today().isoformat(), "ttl_days": TTL if source == "inferred" else None}


def _unknown():
    return _f(None, "low", [], "unknown")


def _model(sigs: list[dict]) -> tuple[str | None, str, list[str], int]:
    ctas = set().union(*[set(s["ctas"]) for s in sigs]) if sigs else set()
    types = set().union(*[set(s["schema_types"]) for s in sigs]) if sigs else set()
    recurring = any(p["period"] in ("month", "year", "seat") for s in sigs for p in s["prices"])
    ev = [s["url"] for s in sigs]
    votes = []
    if "checkout" in ctas:
        votes.append("ecommerce")
    saas_signals = recurring + ("SoftwareApplication" in types) + any(s["has_pricing_page"] for s in sigs)
    if saas_signals and ({"trial", "signup", "demo"} & ctas):
        if {"trial", "signup"} & ctas and "demo" in ctas:
            votes.append("saas_hybrid")
        elif "demo" in ctas:
            votes.append("saas_sales_led")
        else:
            votes.append("saas_plg")
    if "app_install" in ctas and not votes:
        votes.append("app")
    if "LocalBusiness" in types and ({"phone", "booking"} & ctas):
        votes.append("local")
    if not votes and ({"contact_form", "quote"} & ctas):
        votes.append("lead_gen")
    if not votes:
        return None, "low", ev, 0
    strength = saas_signals + len(ctas & {"trial", "signup", "demo", "checkout"})
    return votes[0], ("medium" if strength >= 3 else "low"), ev, strength


def _price(sigs):
    ps = [p for s in sigs for p in s["prices"]]
    if not ps:
        return None
    cur = max({p["currency"] for p in ps if p["currency"]} or {None}, key=lambda c: sum(p["currency"] == c for p in ps))
    same = [p["amount"] for p in ps if p["currency"] == cur]
    metric = "mrr" if any(p["period"] in ("month", "seat") for p in ps) else "acv" if any(p["period"] == "year" for p in ps) else "aov"
    return {"metric": metric, "range": [min(same), max(same)], "currency": cur}


def build(company: list[dict], competitors: dict[str, list[dict]]) -> dict:
    fields = {f: _unknown() for f in FIELDS}
    notes = []
    usable = [s for s in company if not s.get("possibly_js_rendered")]
    for s in company:
        if s.get("possibly_js_rendered"):
            notes.append(f"{s['url']}: little text and no CTAs found (likely JS-rendered). Ask the user instead of guessing.")
    if not usable:
        return {"fields": fields, "notes": notes, "competitor_check": []}
    ev = [s["url"] for s in usable]

    bm, conf, bev, _ = _model(usable)
    if bm:
        fields["business_model"] = _f(bm, conf, bev)
        motion = {"saas_plg": "self_serve", "saas_sales_led": "sales_assisted", "saas_hybrid": "hybrid",
                  "ecommerce": "self_serve"}.get(bm)
        if motion:
            fields["sales_motion"] = _f(motion, conf, bev)
        if bm == "ecommerce":
            fields["sales_cycle_days"] = _f(0, "low", bev)

    b2b = sum(s["b2b_hits"] for s in usable) + sum("company" in s["form_fields"] or "job" in s["form_fields"] for s in usable) * 3
    b2c = sum(s["b2c_hits"] for s in usable)
    if b2b or b2c:
        bt = "b2b" if b2b >= 2 * max(b2c, 1) else "b2c" if b2c >= 2 * max(b2b, 1) else None
        if bt:
            fields["buyer_type"] = _f(bt, "medium" if abs(b2b - b2c) >= 4 else "low", ev)

    pp = _price(usable)
    if pp:
        fields["price_point"] = _f(pp, "medium", [s["url"] for s in usable if s["prices"]])

    markets = []
    for s in usable:
        for h in s["hreflang"]:
            if h == "x-default":
                continue
            lang, _, country = h.partition("-")
            markets.append({"country": country.upper() or None, "language": lang, "currency": None, "priority": None})
    if not markets and any(s["lang"] for s in usable):
        lang, _, country = next(s["lang"] for s in usable if s["lang"]).partition("-")
        markets.append({"country": country.upper() or None, "language": lang, "currency": None, "priority": None})
    if markets:
        uniq = {(m["country"], m["language"]): m for m in markets}
        if pp and pp["currency"] and len(uniq) == 1:
            next(iter(uniq.values()))["currency"] = pp["currency"]
        fields["markets"] = _f(list(uniq.values()), "medium" if any(s["hreflang"] for s in usable) else "low", ev)

    paths = sorted(set().union(*[set(s["ctas"]) for s in usable]))
    if paths:
        fields["conversion_path"] = _f(paths, "medium", ev)

    trk = set().union(*[set(s["trackers"]) for s in usable])
    if trk & {"gtm", "ga4", "google_ads"}:
        # Visible tags are hints only: they say nothing about OCI or enhanced conversions.
        fields["tracking_maturity"] = _f("basic", "low", ev)

    reg = sorted(set().union(*[set(s["regulated_hits"]) for s in usable]))
    if reg:
        fields["regulatory_flags"] = _f(reg, "low", ev)

    comp_rows, check = [], []
    for domain, sigs in competitors.items():
        ok = [s for s in sigs if not s.get("possibly_js_rendered")]
        cbm = _model(ok)[0] if ok else None
        cpp = _price(ok) if ok else None
        pos = ", ".join(x for x in [cbm, cpp and f"{cpp['range'][0]:g}-{cpp['range'][1]:g} {cpp['currency'] or ''} {cpp['metric']}".strip()] if x) or None
        comp_rows.append({"domain": domain, "positioning": pos, "evidence_type": "reported"})
        same = bool(bm and cbm and (bm == cbm or (bm.startswith("saas") and cbm.startswith("saas"))))
        check.append({"domain": domain, "fetched": bool(ok), "business_model": cbm,
                      "likely_direct_competitor": same if (bm and cbm) else None,
                      "note": None if same or not (bm and cbm) else "different business model: confirm with the user"})
    if comp_rows:
        fields["competitors"] = _f(comp_rows, "low", [s["url"] for v in competitors.values() for s in v])
    return {"fields": fields, "notes": notes, "competitor_check": check}
