# GitHub App & OIDC — Integração

> Como as Lambdas e os workflows autenticam no GitHub e na AWS. Referência para
> qualquer automação que crie PR, faça commit ou dispare deploy. Validado 2026-09-14.

## GitHub App (para as Lambdas)

As Lambdas `gj-apply` e `gj-admin` autenticam no GitHub via **GitHub App** (não PAT
estático), gerando installation tokens dinâmicos. Código: `lambdas/shared/github_auth.py`
(copiado para cada lambda que precisa).

- **App ID:** `4409622` (env `GH_APP_ID`)
- **Private key:** env `GH_APP_PRIVATE_KEY` (PEM) — segredo, nunca commitar
- **Installation ID:** env `GH_APP_INSTALLATION_ID` (ou descoberto via API)
- **Fallback:** se o App falhar, cai em `GITHUB_TOKEN`/`GH_TOKEN` env var
- **Fluxo:** `_create_jwt()` (RS256, assinado com a private key) → troca por
  installation token em `/app/installations/{id}/access_tokens` → cache no container
- **Uso:** `from github_auth import get_installation_token`; header `Authorization: token <t>`

## REPO_MAP (domínio → repo)

O `gj-apply` decide em qual repo criar o PR pelo header `origin`. Fonte de verdade do
mapeamento está em `lambdas/gj-apply/gj_apply.py` (REPO_MAP) e resumida no steering
`chapters-registry`. Todo chapter aceita o domínio e o prefixo `www.`; USA também aceita
`goldenjacketsus.com`.

## OIDC (para os GitHub Actions → AWS)

Os workflows (`deploy.yml`, `create-chapter.yml`, `fix-groups.yml`) assumem uma role AWS
via OIDC — sem chaves estáticas.

- **Role:** `arn:aws:iam::800712212925:role/github-actions-deploy`
- **Permissions no workflow:** `id-token: write`
- **Região:** `us-east-1`
- **Account (secret):** `AWS_ACCOUNT_GJ`

### Trust policy — regra importante (BUG conhecido)

O `sub` claim do OIDC precisa aceitar **dois formatos**, porque repos criados após
~jul/2026 usam um formato novo:

- `repo:goldenjackets-community/*` (formato antigo)
- `repo:goldenjackets-community@*` (formato novo)

Se um chapter novo falhar no deploy com erro de OIDC/AssumeRole, a causa provável é a
trust policy não aceitar o formato `@`. Ver steering `known-bugs`.

## Workflows que usam isso

| Workflow | Trigger | Faz |
|---|---|---|
| `deploy.yml` | push em `main` (repo infra) | Deploy das Lambdas gj-admin/gj-apply/gj-poland-counter |
| `create-chapter.yml` | manual (workflow_dispatch) | Provisiona chapter novo (ver spec chapter-provisioning) |
| `fix-groups.yml` | manual | Corrige/atribui grupos Cognito |

## Regras

- Nunca commitar private key do App nem tokens. São env vars/secrets.
- MCP local usa profile AWS `gj-mcp` (chave estática, não SSO) — separado do OIDC dos workflows.
- Alterações são aditivas; não quebrar o fallback de token nem o REPO_MAP existente.
