# Skill: Approve Member PR

Aprovar PR de novo membro de um chapter, com validação anti-bug. Uso: "aprova o PR X do chapter Y"
ou "quais PRs de membro estão abertos?".

## Regras (ver steering community-rules + known-bugs)
- Chapter leads aprovam os PRs dos SEUS chapters; Global Lead só mergeia direto após validar.
- SEMPRE validar antes de aprovar (BUG-1: PR pode vir vazio).

## Passos

### 1. Listar PRs abertos na org
```bash
for repo in $(gh repo list goldenjackets-community --limit 50 --json name -q '.[].name'); do
  prs=$(gh pr list --repo goldenjackets-community/$repo --state open --json number,title,author 2>/dev/null)
  [ "$prs" != "[]" ] && [ -n "$prs" ] && echo ">>> $repo:" && echo "$prs" | \
    python3 -c "import json,sys;[print(f\"   #{p['number']} {p['title']} (@{p['author']['login']})\") for p in json.load(sys.stdin)]"
done
```

### 2. Extrair LinkedIn do PR (validar perfil)
```bash
gh pr view <N> --repo goldenjackets-community/<repo> --json body -q .body | grep -iE "linkedin"
```
Abrir o LinkedIn e confirmar que a pessoa tem 12 certs ativas (Golden) / 10-11 (Challenger) / 7-9 (Rising).

### 3. VALIDAR que o card não veio vazio (crítico — BUG-1)
```bash
gh pr diff <N> --repo goldenjackets-community/<repo> | grep -c 'member-card'
```
- Retorno ≥ 1 → card presente, pode aprovar.
- Retorno = 0 → PR VAZIO. NÃO mergear; inserir card manualmente com dados do corpo do PR.

### 4. Mergear
```bash
gh pr merge <N> --repo goldenjackets-community/<repo> --merge
```

### 5. Confirmar
```bash
gh pr view <N> --repo goldenjackets-community/<repo> --json state -q .state   # deve ser MERGED
```
Deploy é automático (Actions → S3 → CloudFront). Card aparece no site em ~1-2 min.

## Depois
- Se o chapter lead não aprovou (você aprovou por ele), avisar o lead que você validou e mergeou.
- Atualizar contadores do global se quiser refletir o novo total (ver skill recount-community).
