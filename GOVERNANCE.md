# Golden Jackets — Governance

How decisions and access work across the community as we hand more ownership to
Chapter Leads and elect Contributors to help build the platform.

---

## Roles

### Core Team
Founder + elected co-founders. Own the platform, the brand, the global site and final decisions.
- Full admin on the org and all repos.
- Merge rights on `golden-jackets-infra` (the platform).
- Manage `GLOBAL_ADMINS`, AWS accounts, domains.

### Contributors
Elected community members who help build the **platform** (`golden-jackets-infra`).
- `maintain` (or `write`) on `golden-jackets-infra`.
- Pick up `ai:ready` / Phase 1 issues, open PRs, get reviewed by the Core Team.
- No access to production secrets or the AWS root/billing.

### Chapter Leads
Run their own chapter (`golden-jackets-<country>`).
- `write` on their chapter repo + admin on their Cognito group (via the Admin Panel).
- Own their chapter backlog (members, content, events).
- Cannot edit other chapters, the platform, or the global site.

---

## RACI

| Activity | Core Team | Contributor | Chapter Lead |
|----------|:---------:|:-----------:|:------------:|
| Platform code (Lambdas, MCP, hooks, specs) | **A** | **R** | I |
| Fix a known platform bug (Phase 1) | A | **R** | I |
| Global site (goldenjackets.org) | **A/R** | C | I |
| Add / move a member in a chapter | I | — | **A/R** |
| Publish chapter content / events | I | — | **A/R** |
| Approve a member PR | C | — | **A/R** |
| Provision a new chapter | **A/R** | C | I |
| Brand, domains, AWS billing | **A/R** | — | I |
| Elect Contributors / Chapter Leads | **A/R** | I | I |

*A = Accountable · R = Responsible · C = Consulted · I = Informed*

---

## Chapter Lead requirement
A Chapter Lead should be an all-certified professional (Golden Jacket) or the most senior
AWS-certified person driving that country. They register the domain, get admin on their
Cognito group, and receive the Operations Guide.

## Contributor election
Contributors are invited by the Core Team based on real contribution (PRs, community work).
They start with `maintain` on `golden-jackets-infra` and are scoped to platform work.

## Decision making
- Chapter-local decisions → the Chapter Lead decides.
- Platform / cross-chapter / brand decisions → the Core Team decides, Contributors consulted.
- Everything visible on the board: https://github.com/orgs/goldenjackets-community/projects/2

---

*Independent community, not officially affiliated with Amazon Web Services.*
