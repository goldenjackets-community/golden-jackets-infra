# Admin Panel — Requirements

> O painel administrativo da comunidade, servido pela Lambda `gj-admin` via API Gateway.
> Referência dura das actions: steering `admin-actions`. Este spec descreve o subsistema.

## 1. Visão

Cada site de chapter tem um painel admin (área logada via Cognito) que chama a API
`/admin`. Chapter admins gerenciam o próprio chapter; global admins gerenciam tudo. O
painel cobre usuários do Lounge, PRs de membros, cards, job board, artigos e backup.

## 2. Requisitos

- **REQ-AP-1:** Autenticação por JWT Cognito (claim `email`). Sem JWT válido → negar.
- **REQ-AP-2:** Autorização em dois níveis: global admin (lista fixa) vê tudo; chapter
  admin só o próprio grupo. 403 ao tentar agir em chapter alheio.
- **REQ-AP-3:** `restore-backup` é exclusivo de global admin (ação destrutiva).
- **REQ-AP-4:** Gestão de usuários: list/create/delete-user, resend-pending.
- **REQ-AP-5:** Gestão de membros: list-members, update-photo, move-member.
- **REQ-AP-6:** Gestão de PRs: list-prs, merge-pr (renumera restantes), close-pr.
- **REQ-AP-7:** Job board: post-job, list-jobs, delete-job, apply-job.
- **REQ-AP-8:** Conteúdo: submit-article, suggest-topic.
- **REQ-AP-9:** Operação: chapter-status, create-chapter, backup-status.
- **REQ-AP-10:** CORS deve aceitar o domínio de cada chapter (inclui `www.` e alternativos).
- **REQ-AP-11:** Nenhuma action existente pode ser removida/renomeada (frontend depende).
  Mudanças são aditivas.

## 3. Constraints

- Backup vaults por chapter: `gj-poland-backups`, `gj-uk-backups`, `gj-chile-backups`,
  `gj-site-backups` (default).
- Role de restore: `arn:aws:iam::800712212925:role/gj-backup-role`.
- GitHub via App (ver steering `github-app`).

## 4. Fora de escopo

- UI do painel (mora nos repos de chapter). Aqui é o backend/contrato.
