# Skill: Deploy Lambda

Fazer deploy seguro de uma das Lambdas compartilhadas (gj-admin, gj-apply,
gj-poland-counter). Uso: "faz deploy do gj-admin" ou "como atualizo a lambda de apply?".

## Regras (ver steering github-app + admin-actions + known-bugs)
- Deploy é via GitHub Actions: push em `main` do repo `golden-jackets-infra` dispara o
  workflow "Deploy Lambdas" (`.github/workflows/deploy.yml`), que roda
  `aws lambda update-function-code` para gj-admin, gj-apply e gj-poland-counter.
- O workflow assume a role OIDC `github-actions-deploy` (sem chaves estáticas).
- Alterações no código das lambdas devem ser ADITIVAS. Não remover/renomear actions
  existentes do gj-admin (as 20 — ver steering admin-actions).

## Passos

### 1. Editar o código
- Alterar o `.py` da lambda em `lambdas/<nome>/`.
- Se mexer em `gj_admin.py`, adicionar nova action no FIM da cadeia `elif action == ...`.
- Se mexer no REPO_MAP do `gj_apply.py`, manter as entradas existentes + `www.`.

### 2. Validar localmente
- `python3 -m py_compile lambdas/<nome>/*.py` (garante sintaxe).
- Conferir que nenhuma action/rota existente foi removida.

### 3. Deploy
- Commit + push em `main` do repo infra → o workflow deploya automaticamente.
- ATENÇÃO: push em `main` sempre dispara deploy das 3 lambdas (sem path filter). Para
  mudanças que NÃO são de lambda (ex.: docs), use uma branch separada para evitar deploy
  redundante.

### 4. Verificar
- Acompanhar o run: `gh run list --repo goldenjackets-community/golden-jackets-infra`.
- Testar a action/rota afetada.

## Deploy manual (fallback)
- Se o Actions falhar: empacotar e `aws lambda update-function-code --function-name <fn>
  --zip-file fileb:///tmp/<fn>.zip --profile gj`.
