"""Deterministic signal extraction from a saved public HTML page.

Output is structured signals only (categories, numbers, ids, URLs). Page text is untrusted:
it is matched against patterns and never copied into the output.
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

CTA = {
    "trial": r"\b(free trial|start (your )?trial|try (it )?free|try for free)\b",
    "demo": r"\b(book|request|schedule|get) (a |your )?demo\b|\btalk to sales\b|\bcontact sales\b",
    "signup": r"\b(sign ?up|get started|create (an )?account|start for free)\b",
    "checkout": r"\b(add to (cart|bag|basket)|buy now|checkout|shop now)\b",
    "app_install": r"\b(download (the )?app|get it on google play|download on the app store)\b",
    "quote": r"\b(get a quote|request a quote|free quote)\b",
    "booking": r"\b(book (an )?appointment|book now|reserve)\b",
    "newsletter": r"\b(subscribe|newsletter)\b",
    "contact_form": r"\b(contact us|get in touch)\b",
}
B2B = r"\b(for teams|enterprise|for business|per seat|per user|sso|soc ?2|api|integrations?|b2b|workspace)\b"
B2C = r"\b(free shipping|free returns|add to cart|gift|size guide|for you and your family)\b"
REGULATED = {"health": r"\b(prescription|medication|clinic|diagnos)", "finance": r"\b(loan|credit card|investment|insurance)\b",
             "gambling": r"\b(casino|betting|sportsbook)\b", "alcohol": r"\b(wine|beer|spirits|liquor)\b"}
CUR = {"$": "USD", "US$": "USD", "R$": "BRL", "€": "EUR", "£": "GBP"}
PRICE = re.compile(r"(US\$|R\$|\$|€|£|\b(?:USD|BRL|EUR|GBP)\s?)\s?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?|\d+)"
                   r"(\s*(?:/|per)\s*(mo|month|mês|year|yr|ano|user|seat))?", re.I)
TRACKERS = {"gtm": r"GTM-[A-Z0-9]{4,}", "ga4": r"\bG-[A-Z0-9]{6,}", "google_ads": r"\bAW-\d{6,}",
            "meta_pixel": r"fbq\(", "linkedin_insight": r"snap\.licdn\.com|_linkedin_partner_id",
            "consent_banner": r"cookiebot|onetrust|cookieyes|didomi|usercentrics",
            "chat_widget": r"intercom|drift\.com|zendesk|hubspot.*conversations|crisp\.chat"}
APPSTORE = ("apps.apple.com", "play.google.com")


class _P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang, self.hreflang, self.links, self.texts, self.inputs = None, [], [], [], []
        self.jsonld, self._in_jsonld, self._buf, self._skip = [], False, [], 0
        self.cta_texts = []
        self._cta_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "link" and (a.get("rel") or "").lower() == "alternate" and a.get("hreflang"):
            self.hreflang.append(a["hreflang"].lower())
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag in ("a", "button") or (tag == "input" and a.get("type") == "submit"):
            self._cta_depth += 1
            if tag == "input" and a.get("value"):
                self.cta_texts.append(a["value"])
        if tag in ("input", "select", "textarea"):
            self.inputs.append(((a.get("name") or "") + " " + (a.get("type") or "") + " " + (a.get("placeholder") or "")).lower())
        if tag == "script" and (a.get("type") or "") == "application/ld+json":
            self._in_jsonld, self._buf = True, []
        elif tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("a", "button") and self._cta_depth:
            self._cta_depth -= 1
        if tag == "script" and self._in_jsonld:
            self.jsonld.append("".join(self._buf))
            self._in_jsonld = False
        elif tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._in_jsonld:
            self._buf.append(data)
        elif not self._skip:
            self.texts.append(data)
            if self._cta_depth:
                self.cta_texts.append(data)


def _types(blob: str) -> set[str]:
    out = set()
    try:
        def walk(o):
            if isinstance(o, dict):
                t = o.get("@type")
                out.update([t] if isinstance(t, str) else t or [])
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(json.loads(blob))
    except (ValueError, TypeError):
        pass
    return {t for t in out if isinstance(t, str) and re.fullmatch(r"[A-Za-z]{2,40}", t)}


def _num(s: str) -> float | None:
    """'1.234,56' / '1,234.56' / '49,90' / '29'. A separator followed by exactly 2 final digits is decimal."""
    s = s.strip()
    m = re.search(r"[.,](\d{2})$", s)
    whole = re.sub(r"[.,]", "", s[: m.start()] if m else s)
    try:
        return float(f"{whole}.{m.group(1)}" if m else whole)
    except ValueError:
        return None


def extract(html: str, url: str) -> dict:
    p = _P()
    p.feed(html)
    text = " ".join(" ".join(p.texts).split())
    cta_text = " ".join(" ".join(p.cta_texts).split()).lower()
    low = text.lower()
    host = urlparse(url).netloc.lower().removeprefix("www.")
    links = [urljoin(url, h) for h in p.links]
    ctas = sorted({k for k, rx in CTA.items() if re.search(rx, cta_text, re.I)})
    if any(l.startswith("tel:") for l in p.links):
        ctas.append("phone")
    if any(urlparse(l).netloc in APPSTORE for l in links):
        ctas.append("app_install")
    if any(re.search(r"/(cart|checkout|basket)\b", urlparse(l).path) for l in links):
        ctas.append("checkout")
    trackers = sorted(k for k, rx in TRACKERS.items() if re.search(rx, html, re.I))
    if "chat_widget" in trackers:
        ctas.append("chat")
    prices = []
    for m in PRICE.finditer(text):
        sym, amount, per = m.group(1).strip(), _num(m.group(2)), (m.group(4) or "").lower()
        if amount is None or amount <= 0:
            continue
        cur = CUR.get(sym, sym.upper() if len(sym) == 3 else None)
        period = ("month" if per in ("mo", "month", "mês") else "year" if per in ("year", "yr", "ano")
                  else "seat" if per in ("user", "seat") else None)
        prices.append({"amount": amount, "currency": cur, "period": period})
    form_fields = sorted({w for i in p.inputs for w in ("email", "company", "phone", "job", "employees", "website", "name")
                          if w in i})
    schema_types = sorted(set().union(*[_types(b) for b in p.jsonld]) if p.jsonld else set())
    internal = sorted({urlparse(l).path.rstrip("/") or "/" for l in links if urlparse(l).netloc.removeprefix("www.") == host})
    return {
        "url": url, "host": host, "lang": (p.lang or "").lower() or None,
        "hreflang": sorted(set(p.hreflang)),
        "ctas": sorted(set(ctas)), "prices": prices[:30],
        "currencies": sorted({x["currency"] for x in prices if x["currency"]}),
        "form_fields": form_fields, "trackers": trackers, "schema_types": schema_types,
        "has_pricing_page": any(re.search(r"/(pricing|plans|precos|planos)\b", s) for s in internal),
        "b2b_hits": len(re.findall(B2B, low)), "b2c_hits": len(re.findall(B2C, low)),
        "regulated_hits": sorted(k for k, rx in REGULATED.items() if re.search(rx, low)),
        "app_store_links": sorted({l for l in links if urlparse(l).netloc in APPSTORE})[:5],
        "text_chars": len(text),
        "possibly_js_rendered": len(text) < 400 and not ctas,
    }
