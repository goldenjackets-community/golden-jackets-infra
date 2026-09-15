#!/usr/bin/env python3
"""Golden Jackets MCP Server — Phase 1 (local, stdio)"""

import json
import sys
import time

import boto3

# --- AWS clients (lazy init to not block startup) ---

_cognito = None
_cloudfront = None
_sns = None

def get_cognito():
    global _cognito
    if not _cognito:
        _cognito = boto3.client("cognito-idp")
    return _cognito

def get_cloudfront():
    global _cloudfront
    if not _cloudfront:
        _cloudfront = boto3.client("cloudfront")
    return _cloudfront

def get_sns():
    global _sns
    if not _sns:
        _sns = boto3.client("sns")
    return _sns

POOL_ID = "us-east-1_Z0VzzrmIX"
CHAPTERS = {
    "brazil": {"bucket": "www.goldenjacketsbrazil.com", "distribution": "E3N4417EU5IQE6"},
    "poland": {"bucket": "goldenjackets.pl", "distribution": "E174XK4PPCRG0L"},
    "uk": {"bucket": "goldenjackets.co.uk", "distribution": "E10YX1BT67IAVC"},
    "chile": {"bucket": "goldenjackets.cl", "distribution": "EHYKP6CKN2HQ4"},
    "india": {"bucket": "goldenjackets.in", "distribution": "E3NWIF50KGT06C"},
    "france": {"bucket": "goldenjackets.fr", "distribution": "E2O44PVJBUUR5Y"},
    "usa": {"bucket": "goldenjackets.us", "distribution": "E9TMGWA6LF7DP"},
    "italy": {"bucket": "goldenjackets.it", "distribution": "E1PME26ZJ9H7WV"},
    "peru": {"bucket": "goldenjackets.pe", "distribution": "E3V1Z9N208C841"},
    "israel": {"bucket": "goldenjackets.co.il", "distribution": "E12FG4V68VTB02"},
    "belarus": {"bucket": "goldenjackets.by", "distribution": "E2OVUWFPFH9S4Z"},
    "ecuador": {"bucket": "goldenjackets.ec", "distribution": "E3NV9WJS4AZL32"},
    "colombia": {"bucket": "goldenjackets.co", "distribution": "E2IPBAVCWPQWL1"},
    "belgium": {"bucket": "goldenjackets.be", "distribution": "EE0BVLVAL9RPX"},
    "uae": {"bucket": "goldenjackets.ae", "distribution": "E3I43LMFL7RNDS"},
}

# --- Tool implementations ---

def list_members(args):
    chapter = args.get("chapter", "brazil")
    users = []
    params = {"UserPoolId": POOL_ID, "GroupName": chapter, "Limit": 60}
    try:
        while True:
            resp = get_cognito().list_users_in_group(**params)
            for u in resp["Users"]:
                email = next((a["Value"] for a in u["Attributes"] if a["Name"] == "email"), "")
                users.append({"email": email, "status": u["UserStatus"]})
            if "NextToken" not in resp:
                break
            params["NextToken"] = resp["NextToken"]
    except Exception as e:
        return {"error": str(e)}
    return {"chapter": chapter, "members": users, "count": len(users)}

def chapter_status(args):
    results = {}
    for name, cfg in CHAPTERS.items():
        try:
            dist = get_cloudfront().get_distribution(Id=cfg["distribution"])
            status = dist["Distribution"]["Status"]
        except Exception:
            status = "unknown"
        results[name] = {"bucket": cfg["bucket"], "cloudfront_status": status}
    return results

def list_chapters(args):
    return {"chapters": list(CHAPTERS.keys()), "count": len(CHAPTERS)}

def invalidate_cache(args):
    chapter = args.get("chapter", "brazil")
    cfg = CHAPTERS.get(chapter)
    if not cfg:
        return {"error": f"Chapter '{chapter}' not found"}
    try:
        resp = get_cloudfront().create_invalidation(
            DistributionId=cfg["distribution"],
            InvalidationBatch={"Paths": {"Quantity": 1, "Items": ["/*"]}, "CallerReference": f"mcp-{chapter}-{time.time()}"}
        )
        return {"chapter": chapter, "invalidation_id": resp["Invalidation"]["Id"], "status": "created"}
    except Exception as e:
        return {"error": str(e)}

def suggest_topic(args):
    topic = args.get("topic", "")
    author = args.get("author", "anonymous")
    chapter = args.get("chapter", "brazil")
    if not topic:
        return {"error": "topic is required"}
    try:
        get_sns().publish(
            TopicArn="arn:aws:sns:us-east-1:800712212925:gj-brazil-alerts",
            Subject=f"[GJ-{chapter.upper()}] Topic suggestion"[:100],
            Message=f"Author: {author}\nChapter: {chapter}\nTopic: {topic}"
        )
        return {"status": "sent", "topic": topic}
    except Exception as e:
        return {"error": str(e)}

# --- Phase 2 tools (additive) ---
# These orchestrate the existing gj-admin API and read-only AWS/GitHub state.
# GitHub-side actions go through gj-admin (which holds the GitHub App), so this
# server needs no GitHub credentials of its own.

import os
import urllib.request

ADMIN_API = os.environ.get("GJ_ADMIN_API", "https://kqiq2bltjd.execute-api.us-east-1.amazonaws.com/admin")
ADMIN_TOKEN = os.environ.get("GJ_ADMIN_TOKEN", "")  # Cognito JWT for admin calls (optional)

# Certs-per-category formula and thresholds (see steering counting-rules)
CATEGORY_CERTS = {"golden": 12, "challenger": 10, "rising": 8, "alumni": 12}

def _admin_call(action, extra=None):
    """Call the gj-admin API. Requires a Cognito JWT in GJ_ADMIN_TOKEN."""
    if not ADMIN_TOKEN:
        return {"error": "GJ_ADMIN_TOKEN not set (Cognito JWT required for admin actions)"}
    payload = {"action": action}
    if extra:
        payload.update(extra)
    req = urllib.request.Request(
        ADMIN_API,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {ADMIN_TOKEN}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode() or "{}")
    except Exception as e:
        return {"error": str(e)}

def approve_member_pr(args):
    """Approve (merge) a member PR via gj-admin merge-pr, after a safety note."""
    chapter = args.get("chapter")
    pr = args.get("pr_number")
    if not chapter or not pr:
        return {"error": "chapter and pr_number are required"}
    # Safety: caller should have validated the diff has a non-empty member-card (BUG-1).
    return _admin_call("merge-pr", {"chapter": chapter, "pr_number": pr})

def recount_community(args):
    """Recount members per chapter from Cognito groups (source of truth = site cards +
    Cognito). Read-only aggregation; never inflates."""
    chapters = args.get("chapters") or list(CHAPTERS.keys())
    totals = {}
    grand = 0
    for ch in chapters:
        res = list_members({"chapter": ch})
        n = res.get("count", 0) if isinstance(res, dict) else 0
        totals[ch] = n
        grand += n
    return {"per_chapter": totals, "total_cognito_members": grand,
            "note": "Cognito Lounge members. Site card counts are the public source of truth; reconcile before publishing."}

def add_member(args):
    """Create a Cognito user in a chapter via gj-admin create-user."""
    chapter = args.get("chapter")
    email = args.get("email")
    if not chapter or not email:
        return {"error": "chapter and email are required"}
    return _admin_call("create-user", {"chapter": chapter, "email": email})

def check_broken_links(args):
    """Check that each chapter site responds (basic health) at its root domain."""
    results = {}
    for name, cfg in CHAPTERS.items():
        host = cfg["bucket"]
        url = f"https://{host}/"
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "gj-mcp-linkcheck"})
            with urllib.request.urlopen(req, timeout=10) as r:
                results[name] = {"url": url, "status": r.status}
        except Exception as e:
            results[name] = {"url": url, "status": "error", "detail": str(e)}
    broken = {k: v for k, v in results.items() if v.get("status") in ("error",) or (isinstance(v.get("status"), int) and v["status"] >= 400)}
    return {"checked": len(results), "broken_count": len(broken), "broken": broken, "all": results}

def community_stats(args):
    """Aggregate community stats (chapters + Cognito members). Never inflates."""
    member_totals = recount_community({})
    return {
        "chapters": len(CHAPTERS),
        "chapter_list": list(CHAPTERS.keys()),
        "cognito_members_total": member_totals.get("total_cognito_members", 0),
        "per_chapter": member_totals.get("per_chapter", {}),
        "certs_formula": "golden*12 + challenger*10 + rising*8 + alumni*12",
        "note": "Numbers reflect real state. Do not inflate (see steering counting-rules).",
    }

def validate_golden_jacket(args):
    """Validate a member category against the cert count (sacred ruler)."""
    certs = args.get("certs")
    if certs is None:
        return {"error": "certs (0-12) is required"}
    try:
        certs = int(certs)
    except Exception:
        return {"error": "certs must be an integer 0-12"}
    if certs >= 12:
        category = "golden"
    elif certs >= 10:
        category = "challenger"
    elif certs >= 7:
        category = "rising"
    else:
        category = "below-rising"
    return {"certs": certs, "category": category,
            "rule": "golden=12/12, challenger=10-11, rising=7-9, alumni=expired golden",
            "note": "Alumni is a former golden whose certs expired; determine by history, not count."}

TOOLS = {
    "list-members": {
        "description": "List Cognito members of a chapter (Lounge users)",
        "inputSchema": {"type": "object", "properties": {"chapter": {"type": "string", "description": "Chapter name (brazil, poland, uk, chile, india, france, usa, italy, peru, israel, belarus, ecuador, colombia, belgium, uae)", "default": "brazil"}}},
        "handler": list_members,
    },
    "chapter-status": {
        "description": "Show CloudFront and S3 status for all chapters",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": chapter_status,
    },
    "list-chapters": {
        "description": "List all available chapters",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": list_chapters,
    },
    "invalidate-cache": {
        "description": "Invalidate CloudFront cache for a chapter site",
        "inputSchema": {"type": "object", "properties": {"chapter": {"type": "string", "description": "Chapter name", "default": "brazil"}}},
        "handler": invalidate_cache,
    },
    "suggest-topic": {
        "description": "Suggest an article topic (sends SNS notification)",
        "inputSchema": {"type": "object", "properties": {"topic": {"type": "string", "description": "Topic suggestion"}, "author": {"type": "string", "description": "Who is suggesting"}, "chapter": {"type": "string", "default": "brazil"}}, "required": ["topic"]},
        "handler": suggest_topic,
    },
    "approve-member-pr": {
        "description": "Approve (merge) a member PR via gj-admin. Validate the diff has a non-empty member-card first (BUG-1). Requires GJ_ADMIN_TOKEN.",
        "inputSchema": {"type": "object", "properties": {"chapter": {"type": "string", "description": "Chapter name"}, "pr_number": {"type": "integer", "description": "PR number to merge"}}, "required": ["chapter", "pr_number"]},
        "handler": approve_member_pr,
    },
    "recount-community": {
        "description": "Recount Cognito members per chapter (read-only aggregation, never inflates)",
        "inputSchema": {"type": "object", "properties": {"chapters": {"type": "array", "items": {"type": "string"}, "description": "Optional subset of chapters; defaults to all"}}},
        "handler": recount_community,
    },
    "add-member": {
        "description": "Create a Cognito user in a chapter via gj-admin create-user. Requires GJ_ADMIN_TOKEN.",
        "inputSchema": {"type": "object", "properties": {"chapter": {"type": "string", "description": "Chapter name"}, "email": {"type": "string", "description": "Member email"}}, "required": ["chapter", "email"]},
        "handler": add_member,
    },
    "check-broken-links": {
        "description": "HEAD-check every chapter site root and report which are down/erroring",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": check_broken_links,
    },
    "community-stats": {
        "description": "Aggregate community stats (chapters + Cognito members). Never inflates numbers.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": community_stats,
    },
    "validate-golden-jacket": {
        "description": "Validate a member category against cert count (Golden=12, Challenger=10-11, Rising=7-9)",
        "inputSchema": {"type": "object", "properties": {"certs": {"type": "integer", "description": "Number of active AWS certs (0-12)"}}, "required": ["certs"]},
        "handler": validate_golden_jacket,
    },
}

# --- MCP message handling ---

def handle(msg):
    method = msg.get("method")
    id_ = msg.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": id_, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "goldenjackets", "version": "0.2.0"}
        }}

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        tools = [{"name": k, "description": v["description"], "inputSchema": v["inputSchema"]} for k, v in TOOLS.items()]
        return {"jsonrpc": "2.0", "id": id_, "result": {"tools": tools}}

    if method == "tools/call":
        name = msg["params"]["name"]
        args = msg["params"].get("arguments", {})
        tool = TOOLS.get(name)
        if not tool:
            return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": f"Unknown tool: {name}"}}
        result = tool["handler"](args)
        return {"jsonrpc": "2.0", "id": id_, "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}

    if method == "ping":
        return {"jsonrpc": "2.0", "id": id_, "result": {}}

    # Ignore unknown notifications (no id = notification)
    if id_ is None:
        return None

    return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": f"Unknown method: {method}"}}

# --- stdio transport ---

def read_message():
    """Read a JSON-RPC message from stdin (one per line)."""
    line = sys.stdin.readline()
    if not line:
        raise EOFError()
    return json.loads(line)

def write_message(msg):
    """Write a JSON-RPC message to stdout (one per line)."""
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

def main():
    while True:
        try:
            msg = read_message()
            resp = handle(msg)
            if resp:
                write_message(resp)
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
