"""Thin Apify API client.

Sources that block direct scraping (OLX, Facebook, and later Cars24) are pulled
through Apify Actors. The deployed app needs an APIFY_TOKEN env var (the
dealer's Apify account token). Without it, these sources stay idle and the live
"Scrape now" for them is skipped — the rest of the app works regardless.
"""
import os
import requests

BASE = "https://api.apify.com/v2"


def token():
    return os.environ.get("APIFY_TOKEN", "").strip()


def has_token():
    return bool(token())


def run_actor(actor_id, run_input, timeout=120):
    """Run an Actor synchronously and return its dataset items (a list).

    Uses Apify's run-sync-get-dataset-items endpoint, so one call starts the
    run, waits, and returns the rows.
    """
    if not has_token():
        raise RuntimeError("APIFY_TOKEN not set")
    url = f"{BASE}/acts/{actor_id}/run-sync-get-dataset-items"
    resp = requests.post(url, params={"token": token()}, json=run_input, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def credits():
    """Return Apify monthly usage as {used, limit, remaining} in USD, or None.

    Reads /users/me/limits. Returns None if there's no token or the call fails,
    so the UI can show a 'not connected' state instead of breaking.
    """
    if not has_token():
        return None
    try:
        resp = requests.get(f"{BASE}/users/me/limits", params={"token": token()}, timeout=12)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        used = (data.get("current") or {}).get("monthlyUsageUsd")
        limit = (data.get("limits") or {}).get("maxMonthlyUsageUsd")
        if used is None or limit is None:
            return None
        return {"used": round(used, 2), "limit": round(limit, 2),
                "remaining": round(max(0, limit - used), 2)}
    except Exception:
        return None
