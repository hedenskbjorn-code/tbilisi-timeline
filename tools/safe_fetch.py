"""Safe download of a page whose address comes from an UNTRUSTED source (an answer of Gemini): only https, only public addresses (no loopback, private, link-local or reserved ranges, checked at every
redirect), at most three redirects, 20 s, at most 3 MB, only text pages (html / plain / xhtml), no cookies, no login, a generic User-Agent. Returns the plain text of the page (no script, no style, tags removed,
the spaces squeezed, as tools/verify_mainroads.norm does) or None. Usage: from safe_fetch import fetch_text
"""
import html
import http.client
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
    return out
