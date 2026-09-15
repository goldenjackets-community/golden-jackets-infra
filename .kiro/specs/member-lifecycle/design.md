# Member Lifecycle — Design

> Como o fluxo de membro está implementado hoje. Descreve os componentes reais.

## Fluxo ponta a ponta

```
Membro no site do chapter
  │  clica "I'm a Golden Jacket 🏆" / "Join Us" → formulário de apply
  ▼
API Gateway (kqiq2bltjd) /apply
  ▼
Lambda gj-apply
  │  - lê header origin → REPO_MAP → repo do chapter
  │  - github_auth (App 4409622) → installation token
  │  - build_card(name, city, state, date, linkedin, member_type, photo, card_number)
  │  - get_file(index.html, branch) → insere card antes do marker → put_file (cria PR)
  ▼
PR aberto no repo do chapter (branch default: main OU master)
  ▼
Admin (chapter ou global) via painel admin → API /admin → gj-admin
  │  - list-prs → vê PRs abertos
  │  - (valida card não-vazio no diff)
  │  - merge-pr → aprova + rebuild_remaining_prs (renumera cards)
  │      OU close-pr → rejeita
  ▼
GitHub Pages / deploy publica o site
  ▼
Recontagem: atualizar contadores em todos os pontos (counting-rules)
  ▼
(opcional) invalidate-cache CloudFront
```

## Componentes

| Componente | Papel | Arquivo/Recurso |
|---|---|---|
| Site do chapter | Formulário de apply, cards | repo `golden-jackets-<chapter>` |
| gj-apply | Cria PR com o card | `lambdas/gj-apply/gj_apply.py` |
| github_auth | Token do GitHub App | `lambdas/shared/github_auth.py` |
| gj-admin | list/merge/close PR, move-member, list-members | `lambdas/gj-admin/gj_admin.py` |
| Cognito | Identidade/grupos (Lounge + admin) | pool `us-east-1_Z0VzzrmIX` |

## Estrutura do card (build_card)

Campos: `name, city, state, date, linkedin, member_type, photo_path, card_number`.
`member_type` mapeia a categoria (Golden/Challenger/Rising/Alumni). O card é HTML inserido
antes de um marker fixo na seção de membros do `index.html`.

## Pontos de atenção (known-bugs)

- PR vazio: sempre validar que o diff contém `member-card` antes de mergear.
- `data-state="Other"`: rejeitar; exigir UF/estado real.
- Branch varia: detectar antes de operar.
- Contadores: atualizar em ticker (2x), hero `data-target`, tooltip do mapa, cards, meta.

## Decisões

- Reuso do gj-admin em vez de nova automação: as actions merge-pr/close-pr/move-member já
  existem e são a fonte de verdade. Skills e MCP tools apenas orquestram essas actions.
