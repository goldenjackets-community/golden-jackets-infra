# Contributing to Golden Jackets

Welcome! This guide is for **Contributors** (platform) and **Chapter Leads** (chapters).
Read [PROJECT-MANAGEMENT.md](./PROJECT-MANAGEMENT.md) for how the board and phases work,
and [GOVERNANCE.md](./GOVERNANCE.md) for roles and access.

---

## Where work lives
- **Board:** https://github.com/orgs/goldenjackets-community/projects/2
- **Platform repo:** `golden-jackets-infra`
- **Your chapter repo:** `golden-jackets-<country>`

---

## If you are a Chapter Lead

You mostly work through the **Admin Panel** and GitHub issues — no need to touch platform code.

1. Open an issue in your chapter repo using a template (New member / Content / Bug / Event).
2. It shows up on the board under your `Chapter`. Set **Status = Todo**.
3. Do the work (add the member card, publish content, etc.). Deploy is automatic on push to your default branch.
4. Close the issue when done.

Keep these recurring issues alive (Phase 1 — Growth):
- Keep member counters and the map in sync on every change.
- Publish at least one article/talk per month.
- Grow toward the next member milestone.

Gotchas to remember (see `.kiro/steering/known-bugs.md`):
- Count members by **section**, not by CSS class.
- When you change counts on the global site, update **all** spots (ticker, hero `data-target`, map tooltip, cards).
- Default branch differs per repo (`main` vs `master`).

---

## If you are a Contributor (platform)

1. Pick an open issue in `golden-jackets-infra` — prefer ones labeled **`ai:ready`** and **Phase 1**.
2. Assign yourself, set **Status = In Progress**.
3. Branch from the default branch, make the change.
   - Lambdas live in `lambdas/` (gj-admin, gj-apply, gj-architecture, gj-poland-counter).
   - Specs live in `.kiro/specs/` — read the relevant spec before coding; don't re-invent it.
   - Follow `.kiro/steering/` (conventions, security, known-bugs).
4. Open a PR that references the issue (`Closes #NN`). Push to the default branch triggers deploy.
5. A Core Team member reviews and merges. The issue closes → board shows **Done**.

**Working with Kiro:** issues labeled `ai:ready` are written so a Kiro agent can execute them.
The MCP tools in `mcp-server/` and the hooks in `.kiro/hooks/` are part of the toolchain — use them.

---

## Definition of Done
- The change is deployed (Actions green) and verified live where applicable.
- Counters/map are consistent (for member/site changes).
- The issue is closed and reflects reality on the board.

---

*Independent community, not officially affiliated with Amazon Web Services.*
