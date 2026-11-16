"""
Bhashini connection diagnostic
==============================

Run this on your own laptop to find out exactly why Bhashini is refusing you.
It prints the server's own error message, which the app otherwise hides.

    pip install requests
    python test_bhashini.py

It reads your keys from environment variables, or from .streamlit/secrets.toml
if that file exists. It never prints your full key.
"""

import json
import os
import re
import sys

import requests
from urllib.parse import urljoin

CONFIG_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"

PIPELINES = {
    "MeitY": "64392f96daac500b55c543cd",
}

LANGS = ["en", "hi", "mr", "ta", "te", "bn", "gu"]


def load_keys():
    uid = os.getenv("BHASHINI_USER_ID", "").strip()
    key = os.getenv("BHASHINI_API_KEY", "").strip()

    path = os.path.join(".streamlit", "secrets.toml")
    if (not uid or not key) and os.path.exists(path):
        text = open(path, encoding="utf-8").read()
        m = re.search(r'BHASHINI_USER_ID\s*=\s*"([^"]+)"', text)
        n = re.search(r'BHASHINI_API_KEY\s*=\s*"([^"]+)"', text)
        uid = uid or (m.group(1).strip() if m else "")
        key = key or (n.group(1).strip() if n else "")
    return uid, key


def mask(s):
    return f"{s[:4]}…{s[-4:]} ({len(s)} chars)" if len(s) > 10 else "(too short / empty)"


def check(uid, key, pipeline_id, lang):
    headers = {"Content-Type": "application/json", "userID": uid, "ulcaApiKey": key}
    payload = {
        "pipelineTasks": [
            {"taskType": "asr", "config": {"language": {"sourceLanguage": lang}}}
        ],
        "pipelineRequestConfig": {"pipelineId": pipeline_id},
    }
    try:
        r = requests.post(
            CONFIG_URL, headers=headers, json=payload, timeout=20, allow_redirects=False
        )
        hops = 0
        while r.status_code in (301, 302, 303, 307, 308) and hops < 3:
            target = urljoin(CONFIG_URL, r.headers.get("Location", ""))
            if not target:
                break
            r = requests.post(
                target, headers=headers, json=payload, timeout=20, allow_redirects=False
            )
            hops += 1
    except Exception as exc:
        return f"NETWORK ERROR — {exc}"

    if "not supported" in r.text and "GET" in r.text:
        return "SERVER SAW A GET — the URL redirected. Report this line."

    if r.status_code >= 400:
        return f"HTTP {r.status_code} — {r.text.strip()[:220]}"

    try:
        cfg = r.json()["pipelineResponseConfig"][0]["config"]
    except Exception:
        return f"ODD REPLY — {r.text[:220]}"

    if not cfg:
        return "OK but NO ASR MODEL for this language on this pipeline"
    return f"WORKS — service {cfg[0]['serviceId']}"


def main():
    uid, key = load_keys()
    print("=" * 68)
    print("BHASHINI DIAGNOSTIC")
    print("=" * 68)
    print(f"user ID : {mask(uid)}")
    print(f"api key : {mask(key)}")

    if not uid or not key:
        print("\nNo credentials found.")
        print("Set them first, for example:")
        print('  export BHASHINI_USER_ID="..."')
        print('  export BHASHINI_API_KEY="..."')
        sys.exit(1)

    for warn, val, name in [(" ", uid, "user ID"), (" ", key, "api key")]:
        if val != val.strip() or '"' in val or "'" in val:
            print(f"\n!! Your {name} has stray spaces or quote marks in it. Clean it up.")

    for pname, pid in PIPELINES.items():
        print("\n" + "-" * 68)
        print(f"PIPELINE: {pname}  ({pid})")
        print("-" * 68)
        for lang in LANGS:
            print(f"  {lang:>3} : {check(uid, key, pid, lang)}")

    print("\n" + "=" * 68)
    print("HOW TO READ THIS")
    print("=" * 68)
    print("Every line says HTTP 401 or 403  -> keys are wrong. Regenerate them.")
    print("Every line says HTTP 400         -> keys are readable but your account")
    print("                                    has no access to these pipelines.")
    print("                                    Log in to ULCA and subscribe to a")
    print("                                    pipeline, then wait a few minutes.")
    print("Some languages WORK, others not  -> normal. Use a working language, or")
    print("                                    switch pipeline in the app sidebar.")
    print("All NETWORK ERROR                -> no internet, or a firewall is")
    print("                                    blocking ulcacontrib.org.")


if __name__ == "__main__":
    main()
