"""Safe download of a page whose address comes from an UNTRUSTED source (an answer of Gemini): only https, only public addresses (no loopback, private, link-local or reserved ranges, checked at every
redirect), at most three redirects, 20 s, at most 3 MB, only text pages (html / plain / xhtml), no cookies, no login, a generic User-Agent. Returns the plain text of the page (no script, no style, tags removed,
the spaces squeezed, as tools/verify_mainroads.norm does) or None. Usage: from safe_fetch import fetch_text

A page that was read is kept on disk (data/cache/http_text_cache.json.gz: the SHA-256 of the address, the address, the date and the text; not in git): a repeated run of any verify_*.py takes seconds and gives the same
answer offline. A copy older than 30 days (TT_CACHE_DAYS) is not used. A page that could not be read is never kept. BEFORE A RELEASE the check "the quotation still stands on the page" must run with the pages read anew:
python -P tools/verify_<x>.py --refresh (or TT_REFRESH=1): the cache is not used then, the new text replaces it. The end of a run says how many pages came from the cache.
"""
import atexit
import datetime
import gzip
import hashlib
import html
import http.client
import json
import ipaddress
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_mainroads import norm  # noqa: E402

UA = {"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project; page check)"}
MAX = 3 * 1024 * 1024
_cache = {}
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DISK = os.path.join(ROOT, "data", "cache", "http_text_cache.json.gz")
REFRESH = "--refresh" in sys.argv or os.environ.get("TT_REFRESH") == "1"
DAYS = int(os.environ.get("TT_CACHE_DAYS", "30"))
_disk = None
_stat = {"cache": 0, "net": 0, "dirty": 0}


def _load():
    global _disk
    if _disk is None:
        try:
            _disk = json.loads(gzip.decompress(open(DISK, "rb").read()).decode("utf-8"))
        except (OSError, ValueError, EOFError):
            _disk = {}
    return _disk


def _save():
    if _disk is not None and _stat["dirty"]:
        os.makedirs(os.path.dirname(DISK), exist_ok=True)
        tmp = DISK + ".tmp"
        open(tmp, "wb").write(gzip.compress(json.dumps(_disk, ensure_ascii=False).encode("utf-8"), 6))
        os.replace(tmp, DISK)
        _stat["dirty"] = 0


def _report():
    if _stat["cache"] or _stat["net"]:
        print("safe_fetch: pages from the cache %d, downloaded %d%s" % (_stat["cache"], _stat["net"], "" if REFRESH else "  (the cache is used; --refresh reads the pages anew: do it before a release)"), file=sys.stderr)


atexit.register(_save)
atexit.register(_report)


def public_https(url):
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or not u.hostname or u.username or u.password:
        return False
    try:
        infos = socket.getaddrinfo(u.hostname, u.port or 443, proto=socket.IPPROTO_TCP)
    except OSError:
        return False
    for i in infos:
        ip = ipaddress.ip_address(i[4][0].split("%")[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return False
    return bool(infos)


class Hop(urllib.request.HTTPRedirectHandler):
    count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        Hop.count += 1
        if Hop.count > 3 or not public_https(newurl):
            raise urllib.error.HTTPError(newurl, code, "redirect refused", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_text(url):
    if url in _cache:
        return _cache[url]
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    hit = None if REFRESH else _load().get(key)
    if hit and hit.get("url") == url and (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(hit["fetched"])).days < DAYS:
        _stat["cache"] += 1
        _cache[url] = hit["text"]
        return hit["text"]
    out = None
    if public_https(url):
        Hop.count = 0
        try:
            op = urllib.request.build_opener(Hop)
            with op.open(urllib.request.Request(url, headers=UA), timeout=20) as r:
                ct = (r.headers.get("Content-Type") or "").lower()
                if ct.startswith(("text/html", "text/plain", "application/xhtml")):
                    raw = r.read(MAX + 1)
                    if len(raw) <= MAX:
                        m = re.search(r"charset=([\w-]+)", ct)
                        t = raw.decode(m.group(1) if m else "utf-8", errors="replace")
                        t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
                        out = norm(html.unescape(re.sub(r"<[^>]+>", " ", t)))
        except (urllib.error.URLError, http.client.HTTPException, OSError, LookupError, ValueError):
            out = None
    _cache[url] = out
    if out is not None:
        _stat["net"] += 1
        _load()[key] = {"url": url, "fetched": datetime.datetime.now(datetime.timezone.utc).isoformat(), "text": out}
        _stat["dirty"] += 1
        if _stat["dirty"] >= 25:
            _save()
    return out
