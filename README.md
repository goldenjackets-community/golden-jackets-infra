# Golden Jackets — Shared Infrastructure

Backend Lambdas and infrastructure shared across all chapters.

## Structure

```
lambdas/
  gj-admin/       — Admin panel API (list/create/delete users, backup, restore)
```

## Deployment

Push to `main` → GitHub Actions deploys Lambda automatically.

## Architecture

- **Cognito Pool:** `us-east-1_Z0VzzrmIX` (shared across all chapters)
- **Groups:** `brazil`, `poland` (one per chapter)
- **API:** `https://kqiq2bltjd.execute-api.us-east-1.amazonaws.com/admin`
- **Backup Vaults:** `gj-site-backups` (BR), `gj-poland-backups` (PL)

## Access Control

- Global admins see all chapters
- Chapter admins only see their own users
- Restore restricted to global admins only

## 🤖 Built With AI

This project was entirely built using **Kiro CLI** (powered by Claude, Anthropic) — from Lambda functions to IAM policies, CI/CD workflows, and operational guides.

## 📋 Project Management & Governance

This community runs on an **AI-Agile Spec-Driven** framework (GitHub Issues + Projects + Milestones + Labels). Start here:

- **[PROJECT-MANAGEMENT.md](./PROJECT-MANAGEMENT.md)** — how the board, issues, phases and labels work.
- **[GOVERNANCE.md](./GOVERNANCE.md)** — roles (Core Team, Contributors, Chapter Leads), RACI and elections.
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** — how to pick up a task, open an issue and submit a PR.
- **[Community Backlog board](https://github.com/orgs/goldenjackets-community/projects/2)** — full platform & chapters roadmap.
