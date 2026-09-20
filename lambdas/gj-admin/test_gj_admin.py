"""
Unit tests for gj_admin security behavior (CORS allowlist + GLOBAL_ADMINS).

These run in CI with no AWS access: boto3 is stubbed before importing the module,
so we test pure logic (header building, admin resolution) without deploying.
"""
import importlib
import importlib.util
import sys
import types
import os


def _load_module(env=None):
    """(Re)load gj_admin with boto3 stubbed and a given environment."""
    # stub boto3 so `import boto3` + boto3.client(...) at module load don't fail
    boto3_stub = types.ModuleType("boto3")
    boto3_stub.client = lambda *a, **k: object()
    sys.modules["boto3"] = boto3_stub

    # apply env overrides
    old = {}
    env = env or {}
    for k, v in env.items():
        old[k] = os.environ.get(k)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("gj_admin", os.path.join(here, "gj_admin.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # restore env
    for k, v in old.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return mod


def _event(origin=None):
    headers = {}
    if origin is not None:
        headers["origin"] = origin
    return {"headers": headers}


# ---------- CORS ----------

def test_cors_reflects_allowed_origin():
    gj = _load_module()
    h = gj._cors_headers(_event("https://goldenjacketsbrazil.com"))
    assert h["Access-Control-Allow-Origin"] == "https://goldenjacketsbrazil.com"
    assert h["Vary"] == "Origin"


def test_cors_blocks_unknown_origin():
    gj = _load_module()
    h = gj._cors_headers(_event("https://evil.com"))
    assert h["Access-Control-Allow-Origin"] == ""


def test_cors_blocks_missing_origin():
    gj = _load_module()
    h = gj._cors_headers(_event(None))
    assert h["Access-Control-Allow-Origin"] == ""


def test_cors_never_wildcard():
    gj = _load_module()
    for origin in ["https://goldenjackets.pl", "https://evil.com", None]:
        h = gj._cors_headers(_event(origin))
        assert h["Access-Control-Allow-Origin"] != "*"


def test_cors_honors_env_allowlist():
    gj = _load_module(env={"ALLOWED_ORIGINS": "https://a.com,https://b.com"})
    assert gj._cors_headers(_event("https://a.com"))["Access-Control-Allow-Origin"] == "https://a.com"
    # a previously-default domain is no longer allowed when env is set explicitly
    assert gj._cors_headers(_event("https://goldenjacketsbrazil.com"))["Access-Control-Allow-Origin"] == ""


# ---------- GLOBAL_ADMINS ----------

def test_global_admins_from_env():
    gj = _load_module(env={"GLOBAL_ADMINS": "boss@x.com, second@y.com"})
    assert gj.GLOBAL_ADMINS == ["boss@x.com", "second@y.com"]


def test_global_admins_fallback_when_env_missing():
    gj = _load_module(env={"GLOBAL_ADMINS": None})
    assert len(gj.GLOBAL_ADMINS) >= 1
    # stored lowercased for case-insensitive comparison
    assert all(a == a.lower() for a in gj.GLOBAL_ADMINS)


def test_global_admins_no_pii_hardcoded_in_source():
    """The literal email list must not sit in an assignable GLOBAL_ADMINS line."""
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "gj_admin.py")) as f:
        src = f.read()
    # the old smell: GLOBAL_ADMINS = ['someone@...']
    assert "GLOBAL_ADMINS = ['" not in src
    assert 'GLOBAL_ADMINS = ["' not in src
