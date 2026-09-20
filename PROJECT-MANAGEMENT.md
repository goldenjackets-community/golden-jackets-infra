# Golden Jackets — Project Management (AI-Agile Spec-Driven)

How we run work across the Golden Jackets community. This is a lightweight framework
built for an **asynchronous, volunteer-driven, AI-assisted** community spread across 20+ time zones.
It is not Scrum. There are no daily standups. It is **Kanban + milestones + specs as the source of truth**,
where part of the execution is done by AI agents (Kiro).

---

## 1. The two layers

| Layer | Repos | Who owns it | Backlog is about |
|-------|-------|-------------|------------------|
| **Platform** | `golden-jackets-infra` | Core Team (+ Contributors) | Lambdas, specs, hooks, MCP tools, global site, bugs |
| **Chapter** | `golden-jackets-<country>` | Chapter Lead | Members, content, events, local site |

The **Platform** backlog is technical (PT-BR internally). The **Chapter** backlog is
operational and business-facing (English), because Chapter Leads are not developers.

---

## 2. The board

Everything lives in one aggregated project board:

**Golden Jackets — Community Backlog** → https://github.com/orgs/goldenjackets-community/projects/2

Custom fields:
- **Phase** — where the work sits in the roadmap (Phase 0 Baseline → Phase 3).
- **Chapter** — which chapter/area it belongs to (Platform, Global, Brazil, India, ...).
- **Status** — Todo / In Progress / Done.

A Chapter Lead sees their own work by filtering `Chapter = <country>`.
The Core Team sees the whole platform by filtering `Chapter = Platform`.

---

## 3. Phases (milestones)

We reverse-engineered the history so the board reads like the community was managed from day one.

**Platform (`golden-jackets-infra`):**
- **Phase 0 — Baseline** *(closed)* — the platform as it existed at launch: shared infra, chapter provisioning, observability, MCP, global site, steering.
- **Phase 1 — Hardening & Automation** — close known bugs, finish end-to-end automation, self-service chapter ops.
- **Phase 2 — Platform as Code (Kiro)** *(closed)* — steering, hooks, MCP tools and skills that turn ops into platform-as-code.
- **Phase 3 — Community Value & Scale** — self-service tiers, health dashboard, 2027 give-back-to-members roadmap.

**Chapters:**
- **Phase 0 — Chapter Launch** *(closed)* — site live, lead onboarded, first members, listed on the global map.
- **Phase 1 — Growth** — grow members, keep counters/map accurate, publish content.
- **Phase 2 — Engagement** — events, community value, local partnerships.

Closed Phase 0 issues are the **reverse-engineered baseline** — they document what was already built.

---

## 4. Labels

Three axes, so anyone can slice the backlog:

- **Phase** — `phase-0-baseline`, `phase-1-*`, `phase-2-*`, `phase-3-value-scale`, `done`
- **Type** — Platform: `type:steering|hook|mcp-tool|bugfix|baseline`. Chapter: `type:member|content|event|bug|site`.
- **Spec** *(platform only)* — `spec:member-lifecycle|admin-panel|chapter-provisioning|observability|global-site|community-platform`
- **Priority / Status** — `priority:high`, `status:blocked`
- **`ai:ready`** — the issue has enough context for an AI agent (Kiro) to execute it end-to-end.

---

## 5. The "AI-Agile" part

This community is operated by **humans + Kiro (AI)**. That is the core of the framework:

- Issues labeled **`ai:ready`** are written so a Kiro agent can pick them up and execute
  (clear scope, files touched, acceptance in the body).
- The **hooks** (`.kiro/hooks/community-hooks.json`) act as automated reviewers on save.
- The **MCP tools** (`mcp-server/`) are the executors — approve member PRs, recount, validate, check links.
- The **specs** (`.kiro/specs/`) are the source of truth; issues reference them, they are not re-explained.

So "sprint" here means: pick an `ai:ready` issue → Kiro drafts/executes → human reviews & merges → close.

---

## 6. Workflow

1. Something needs doing → open an issue in the right repo (use the templates).
2. Set **Phase**, **Chapter**, **Status = Todo**, assignee.
3. Working on it → **Status = In Progress**.
4. Done → close the issue (Status flips to **Done**), or for platform work, merge the PR that references it.
5. Recurring chapter tasks (keep counters synced, publish monthly) stay open as living reminders.

---

*Independent community, not officially affiliated with Amazon Web Services.*
