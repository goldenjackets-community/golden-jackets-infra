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


# ---------- Authorization / chapter isolation (issue #35) ----------

# Deterministic global-admin list for these tests.
_AUTH_ENV = {"GLOBAL_ADMINS": "boss@global.com"}


def test_chapter_admin_cannot_act_on_other_chapter():
    """A brazil admin must NOT be able to act on the poland chapter."""
    gj = _load_module(env=_AUTH_ENV)
    allowed, err = gj.authorize_action(
        action="list-users", chapter="poland",
        caller_email="admin@brazil.com", caller_groups=["brazil"],
    )
    assert allowed is False
    assert err == "Access denied to this chapter"


def test_chapter_admin_can_act_on_own_chapter():
    gj = _load_module(env=_AUTH_ENV)
    allowed, err = gj.authorize_action(
        action="list-users", chapter="brazil",
        caller_email="admin@brazil.com", caller_groups=["brazil"],
    )
    assert allowed is True
    assert err is None


def test_global_admin_can_act_on_any_chapter():
    gj = _load_module(env=_AUTH_ENV)
    for chapter in ["brazil", "poland", "chile", "uk"]:
        allowed, err = gj.authorize_action(
            action="list-users", chapter=chapter,
            caller_email="boss@global.com", caller_groups=[],
        )
        assert allowed is True, f"global admin blocked on {chapter}"


def test_global_admin_email_is_case_insensitive():
    gj = _load_module(env=_AUTH_ENV)
    allowed, _ = gj.authorize_action(
        action="list-users", chapter="poland",
        caller_email="BOSS@GLOBAL.COM", caller_groups=[],
    )
    assert allowed is True


def test_restore_backup_denied_for_chapter_admin():
    """restore-backup is global-admin only, even on the admin's own chapter."""
    gj = _load_module(env=_AUTH_ENV)
    allowed, err = gj.authorize_action(
        action="restore-backup", chapter="brazil",
        caller_email="admin@brazil.com", caller_groups=["brazil"],
    )
    assert allowed is False
    assert err == "Only global admins can restore backups"


def test_restore_backup_allowed_for_global_admin():
    gj = _load_module(env=_AUTH_ENV)
    allowed, err = gj.authorize_action(
        action="restore-backup", chapter="brazil",
        caller_email="boss@global.com", caller_groups=[],
    )
    assert allowed is True
    assert err is None


def test_delete_user_denied_when_target_in_other_chapter():
    """A brazil admin cannot delete a user that belongs only to poland."""
    gj = _load_module(env=_AUTH_ENV)
    allowed, err = gj.authorize_action(
        action="delete-user", chapter="brazil",
        caller_email="admin@brazil.com", caller_groups=["brazil"],
        target_groups=["poland"],
    )
    assert allowed is False
    assert err == "Cannot delete user from another chapter"


def test_delete_user_allowed_when_target_in_own_chapter():
    gj = _load_module(env=_AUTH_ENV)
    allowed, err = gj.authorize_action(
        action="delete-user", chapter="brazil",
        caller_email="admin@brazil.com", caller_groups=["brazil"],
        target_groups=["brazil"],
    )
    assert allowed is True


def test_skip_chapter_action_allowed_without_membership():
    """Chapter-agnostic actions (e.g. list-jobs) don't require chapter membership."""
    gj = _load_module(env=_AUTH_ENV)
    allowed, err = gj.authorize_action(
        action="list-jobs", chapter="poland",
        caller_email="admin@brazil.com", caller_groups=["brazil"],
    )
    assert allowed is True


# ---------- pagination consistency (issue #34) ----------

import datetime as _dt


class _FakeCognitoPaged:
    """Fake Cognito client that returns users across TWO pages, to prove the
    caller follows the pagination token instead of stopping at page one."""
    def __init__(self, token_key, page1, page2):
        self._token_key = token_key      # 'PaginationToken' or 'NextToken'
        self._page1 = page1
        self._page2 = page2

    def _mk(self, emails):
        return [{
            "Attributes": [{"Name": "email", "Value": e}],
            "UserStatus": "CONFIRMED",
            "UserCreateDate": _dt.datetime(2026, 1, 1),
        } for e in emails]

    def list_users(self, **params):
        if params.get("PaginationToken") == "PAGE2":
            return {"Users": self._mk(self._page2)}
        return {"Users": self._mk(self._page1), "PaginationToken": "PAGE2"}

    def list_users_in_group(self, **params):
        if params.get("NextToken") == "PAGE2":
            return {"Users": self._mk(self._page2)}
        return {"Users": self._mk(self._page1), "NextToken": "PAGE2"}


def test_list_all_users_follows_pagination_token():
    gj = _load_module()
    gj.cognito = _FakeCognitoPaged("PaginationToken",
                                   ["a@x.com", "b@x.com"], ["c@x.com"])
    gj.POOL_ID = "pool"
    users = gj.list_all_users()
    emails = [u["email"] for u in users]
    assert emails == ["a@x.com", "b@x.com", "c@x.com"], emails  # both pages


def test_get_users_in_group_follows_next_token():
    gj = _load_module()
    gj.cognito = _FakeCognitoPaged("NextToken",
                                   ["one@x.com"], ["two@x.com", "three@x.com"])
    gj.POOL_ID = "pool"
    users = gj.get_users_in_group("brazil")
    emails = [u["email"] for u in users]
    assert emails == ["one@x.com", "two@x.com", "three@x.com"], emails


def test_list_all_users_single_page_no_token():
    gj = _load_module()

    class _OnePage:
        def list_users(self, **p):
            return {"Users": [{
                "Attributes": [{"Name": "email", "Value": "solo@x.com"}],
                "UserStatus": "CONFIRMED",
                "UserCreateDate": _dt.datetime(2026, 1, 1),
            }]}  # no PaginationToken -> stop after one page
    gj.cognito = _OnePage()
    gj.POOL_ID = "pool"
    users = gj.list_all_users()
    assert [u["email"] for u in users] == ["solo@x.com"]


def test_list_all_users_swallows_errors():
    gj = _load_module()

    class _Boom:
        def list_users(self, **p):
            raise RuntimeError("cognito down")
    gj.cognito = _Boom()
    gj.POOL_ID = "pool"
    # must not raise; returns whatever was collected (empty)
    assert gj.list_all_users() == []
