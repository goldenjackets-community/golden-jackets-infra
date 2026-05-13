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
