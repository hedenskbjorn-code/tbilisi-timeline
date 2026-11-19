"""Deploys the Workers of the photo form (worker/submit.js, worker/admin.js) with the REST API of Cloudflare, without wrangler.
Secrets come only from the environment (never stored in the repository): CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID; for the submit worker TURNSTILE_SECRET and HASH_SALT;
for the admin worker TEAM_DOMAIN, POLICY_AUD and ADMIN_EMAILS.
Usage: python -X utf8 -P tools/deploy_worker.py submit|admin
What it does: makes sure that the KV namespace "tbilisi-photos" exists, uploads the script with its bindings, turns on its workers.dev address, prints the address.
"""
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API = "https://api.cloudflare.com/client/v4"
TOK = os.environ["CLOUDFLARE_API_TOKEN"]
AID = os.environ["CLOUDFLARE_ACCOUNT_ID"]
KV_TITLE = "tbilisi-photos"
SCRIPTS = {"submit": ("tbilisi-photos", "submit.js"), "admin": ("tbilisi-photos-admin", "admin.js")}


def call(method, path, body=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(API + path, data=data, method=method, headers={"Authorization": "Bearer " + TOK, "Content-Type": ctype, "User-Agent": "tbilisi-timeline-deploy"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def kv_id():
    st, d = call("GET", "/accounts/%s/storage/kv/namespaces?per_page=100" % AID)
    for n in d.get("result", []):
        if n["title"] == KV_TITLE:
            return n["id"]
    st, d = call("POST", "/accounts/%s/storage/kv/namespaces" % AID, {"title": KV_TITLE})
    if not d.get("success"):
        sys.exit("cannot create the KV namespace: %s" % d.get("errors"))
    return d["result"]["id"]


def multipart(parts):
    b = uuid.uuid4().hex
    out = b""
    for name, filename, ctype, content in parts:
        out += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"%s\r\nContent-Type: %s\r\n\r\n" % (b, name, "; filename=\"%s\"" % filename if filename else "", ctype)).encode() + content + b"\r\n"
    out += ("--%s--\r\n" % b).encode()
    return out, "multipart/form-data; boundary=" + b


def main():
    which = sys.argv[1]
    name, fname = SCRIPTS[which]
    kv = kv_id()
    bindings = [{"type": "kv_namespace", "name": "PHOTOS", "namespace_id": kv}]
    if which == "submit":
        bindings += [{"type": "secret_text", "name": k, "text": os.environ[k]} for k in ("TURNSTILE_SECRET", "HASH_SALT")]
    else:
        bindings += [{"type": "plain_text", "name": k, "text": os.environ[k]} for k in ("TEAM_DOMAIN", "POLICY_AUD")]
        bindings += [{"type": "secret_text", "name": "ADMIN_EMAILS", "text": os.environ["ADMIN_EMAILS"]}]
    meta = {"main_module": "worker.js", "compatibility_date": "2025-01-01", "bindings": bindings}
    code = open(os.path.join(ROOT, "worker", fname), "rb").read()
    body, ctype = multipart([("metadata", None, "application/json", json.dumps(meta).encode()), ("worker.js", "worker.js", "application/javascript+module", code)])
    st, d = call("PUT", "/accounts/%s/workers/scripts/%s" % (AID, name), raw=body, ctype=ctype)
    if not d.get("success"):
        sys.exit("upload failed (%s): %s" % (st, d.get("errors")))
    st, d = call("POST", "/accounts/%s/workers/scripts/%s/subdomain" % (AID, name), {"enabled": True, "previews_enabled": False})
    st2, sub = call("GET", "/accounts/%s/workers/subdomain" % AID)
    host = "%s.%s.workers.dev" % (name, (sub.get("result") or {}).get("subdomain", "?"))
    print("deployed", name, "| kv", kv[:6] + "...", "| subdomain call", st, d.get("success"), "| address: https://" + host)


if __name__ == "__main__":
    main()
