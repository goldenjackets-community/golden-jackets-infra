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

TOOLS = {
    "list-members": {
        "description": "List Cognito members of a chapter (Lounge users)",
        "inputSchema": {"type": "object", "properties": {"chapter": {"type": "string", "description": "Chapter name (brazil, poland, uk, chile)", "default": "brazil"}}},
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
