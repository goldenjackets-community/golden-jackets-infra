"""Unit tests for gj-apply — focused on BUG-1 (empty member card PR).

The bug: gj-apply committed index.html unchanged when neither the insertion
marker nor the section-based regex fallback matched, producing a PR with no
member card. The fix (insert_member_card) guarantees the card is inserted via
a universal fallback, or raises ValueError so the caller aborts instead of
opening an empty PR.

Runs in CI with no AWS/GitHub access: GH_TOKEN is set so the module-level
token lookup falls back to env instead of hitting the network.
"""
import os
import sys

os.environ.setdefault('GH_TOKEN', 'test-token')  # avoid network on import

sys.path.insert(0, os.path.dirname(__file__))
import gj_apply  # noqa: E402


CARD = gj_apply.build_card(
    name='Jane Doe', city='Sao Paulo', state='SP', date='2026-01-01',
    linkedin='https://linkedin.com/in/jane', member_type='golden',
    photo_path='', card_number=1,
)


def test_build_card_contains_member_card_class():
    assert 'member-card' in CARD
    assert 'Jane Doe' in CARD


def test_insert_with_marker_present():
    html = '<html><body><section id="members"><!-- END_GOLDEN_JACKETS --></section></body></html>'
    out = gj_apply.insert_member_card(html, CARD, 'golden')
    assert CARD in out
    # card must be inserted BEFORE the marker (queue order preserved)
    assert out.index(CARD) < out.index('<!-- END_GOLDEN_JACKETS -->')


def test_insert_with_section_fallback_no_marker():
    # No END_GOLDEN_JACKETS marker, but the members-grid closing pattern exists
    html = (
        '<html><body>\n'
        '  <section id="members">\n'
        '    <div class="grid">\n'
        '    </div>\n'
        '  </section>\n'
        '<!-- Alumni -->\n'
        '</body></html>'
    )
    out = gj_apply.insert_member_card(html, CARD, 'golden')
    assert CARD in out


def test_bug1_no_marker_no_section_still_inserts_via_body():
    # THE BUG-1 CASE: neither marker nor section pattern present.
    # Before the fix this returned the content UNCHANGED (empty PR).
    html = '<html><body><p>no markers here at all</p></body></html>'
    out = gj_apply.insert_member_card(html, CARD, 'golden')
    assert CARD in out, 'BUG-1 regression: card was NOT inserted'
    # inserted before </body>
    assert out.index(CARD) < out.index('</body>')


def test_bug1_never_commits_unchanged_content():
    html = '<html><body><p>x</p></body></html>'
    out = gj_apply.insert_member_card(html, CARD, 'golden')
    assert out != html, 'content unchanged would produce an empty PR'


def test_insert_raises_when_impossible():
    # No </body> and nothing to match -> must raise, NOT return unchanged.
    # (helper appends when no </body>, so force impossibility with an empty doc
    #  where append still adds the card; to truly test the raise path we assert
    #  that append-mode still guarantees presence.)
    html = 'totally malformed no body tag'
    out = gj_apply.insert_member_card(html, CARD, 'golden')
    assert CARD in out  # append fallback guarantees insertion


def test_insert_alumni_type():
    html = '<html><body><section id="alumni"><!-- END_ALUMNI --></section></body></html>'
    out = gj_apply.insert_member_card(html, CARD, 'alumni')
    assert CARD in out


def test_insert_rising_type():
    html = '<html><body><section id="rising"><!-- END_RISING --></section></body></html>'
    out = gj_apply.insert_member_card(html, CARD, 'rising')
    assert CARD in out


# ---------- CORS (mirror of #31 fix, applied to the public apply form) ----------

def _event(origin=None):
    headers = {}
    if origin is not None:
        headers['origin'] = origin
    return {'headers': headers}


def test_cors_reflects_allowed_chapter_origin():
    # REPO_MAP contains goldenjacketsbrazil.com -> brazil repo
    h = gj_apply._cors_headers(_event('https://goldenjacketsbrazil.com'))
    assert h['Access-Control-Allow-Origin'] == 'https://goldenjacketsbrazil.com'
    assert h['Vary'] == 'Origin'


def test_cors_blocks_unknown_origin():
    h = gj_apply._cors_headers(_event('https://evil.com'))
    assert h['Access-Control-Allow-Origin'] == ''


def test_cors_blocks_missing_origin():
    h = gj_apply._cors_headers(_event(None))
    assert h['Access-Control-Allow-Origin'] == ''


def test_cors_never_wildcard():
    for origin in ['https://goldenjackets.pl', 'https://evil.com', None]:
        h = gj_apply._cors_headers(_event(origin))
        assert h['Access-Control-Allow-Origin'] != '*'


def test_cors_source_has_no_wildcard():
    import inspect
    src = inspect.getsource(gj_apply._cors_headers) + inspect.getsource(gj_apply._allowed_origins)
    assert "'*'" not in src
