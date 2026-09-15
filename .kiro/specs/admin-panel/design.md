# Admin Panel — Design

> Arquitetura real do backend admin (gj-admin).

## Componentes

```
Painel admin (frontend no repo do chapter, área logada)
  │  JWT Cognito no header Authorization
  ▼
API Gateway HTTP (kqiq2bltjd) — rota /admin (POST + OPTIONS/CORS)
  ▼
Lambda gj-admin (lambda_handler)
  │  - get_caller_email(event) via jwt.claims.email
  │  - get_user_groups(email) → grupos Cognito do caller
  │  - is_global_admin = email in GLOBAL_ADMINS
  │  - resolve chapter (body → origin header → primeiro grupo)
  │  - checagem de acesso (skip_chapter_actions p/ globais)
  │  - dispatch por action (cadeia if/elif)
  ├──► Cognito (users/groups)
  ├──► GitHub (via github_auth App) — PRs, cards, artigos
  ├──► AWS Backup (vaults) — status/restore
  └──► SNS — notificações (suggest-topic)
```

## Dispatch de actions

As 20 actions estão documentadas no steering `admin-actions` (tabela completa com
restrições). O handler é uma cadeia `if action == ... elif ...`. Novas actions entram
no fim da cadeia.

## Modelo de dados

- **Usuários/grupos:** Cognito pool `us-east-1_Z0VzzrmIX`, um grupo por chapter.
- **Job board:** persistência via gj-admin (post/list/delete/apply-job).
- **Cards de membro:** HTML nos `index.html` dos repos de chapter.
- **Backup:** AWS Backup vaults por chapter.

## Segurança

- Global admins hardcoded em `GLOBAL_ADMINS` no código (3 emails).
- `restore-backup` gated a global admin.
- `delete-user` valida que o alvo pertence ao chapter do caller.
- CORS liberado (`*`) no header, mas auth por JWT protege as actions.

## Decisões

- Lambda monolítica por design (um handler, muitas actions) — simples de operar e deployar.
- Ao estender: manter o padrão de checagem de acesso; não afrouxar `restore-backup`.
