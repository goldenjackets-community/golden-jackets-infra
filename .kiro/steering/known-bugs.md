# Golden Jackets — Known Bugs & Gotchas (Steering)

Bugs e armadilhas recorrentes da plataforma. Verificar SEMPRE antes de operar.

## BUG-1 — gj-apply gera PR de membro VAZIO
Às vezes o Lambda `gj-apply` abre o PR mas NÃO insere o card no index.html (commit sem diff
do card). O deploy "passa" mas o membro não aparece no site.
- **Detectar antes de aprovar:** o diff do PR DEVE conter `member-card` e ~15 linhas adicionadas.
  `gh pr diff <n> --repo goldenjackets-community/<repo> | grep -c member-card` → tem que ser ≥1.
- Se vier vazio: inserir o card manualmente (dados vêm do corpo do PR).

## BUG-2 — Contadores do site global em MÚLTIPLOS lugares
Ao mudar contagem (membros/certs/países) no `golden-jackets-global`, atualizar TODOS os pontos:
1. Ticker rolante (aparece 2x — duplicado pro loop de scroll)
2. **Hero `data-target="N"`** (contador animado — o número GRANDE; MAIS fácil de esquecer)
3. Tooltip do mapa (por país)
4. Cards de chapter
5. Meta/social description
6. Status line
NÃO mexer nos números do histórico/timeline (têm datas grudadas, são eventos passados).
Esquecer o `data-target` = número grande visível continua errado ("parece que não mudou").

## BUG-3 — Link quebrado por typo de domínio
Ex real: site USA apontava pra `golden-jackets-usa` (não existe); correto é `golden-jackets-us`.
Sempre conferir o slug real da página LinkedIn / domínio antes de linkar.

## BUG-4 — OIDC sub claim (deploy falha silencioso)
GitHub mudou o formato do `sub` claim para repos criados após ~jul/2026
(`repo:goldenjackets-community@<id>/...`). A trust policy da role `github-actions-deploy`
DEVE aceitar `repo:goldenjackets-community/*` E `repo:goldenjackets-community@*`.
Sintoma: PRs mergeiam mas o site não atualiza (Actions falha em AssumeRoleWithWebIdentity).

## BUG-5 — Branch default varia por repo
Alguns repos usam `main` (brazil, belgium, italy, uae), outros `master` (resto).
Detectar antes de push: `git symbolic-ref refs/remotes/origin/HEAD` ou `gh repo view`.

## Gotcha — Contagem de membros
Contar por SEÇÃO (id=members/alumni/challengers/rising), NUNCA por classe CSS exata.
Cards founder/cofounder (Brazil) têm classe diferente mas SÃO golden.
Chapters pequenos (belgium/by/ecuador/italy/poland/uae) não têm marker END_GOLDEN_JACKETS —
contar todas as `class="member-card"` da área.

## Gotcha — Permissão de filesystem
Sessão pode rodar como user `cloud2point` (uid 1001) sem escrita em /home/gulias.
Nesse caso: editar via `gh api` (baixa base64 → edita em /tmp → PUT com sha+branch) ou escrever em /tmp.

## Gotcha — Deploy é automático
Push na branch default de cada repo dispara GitHub Actions (S3 sync + CloudFront invalidation).
NÃO precisa deploy manual. Site atualiza em ~1-2 min.
