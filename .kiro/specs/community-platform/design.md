# Golden Jackets Community Platform — Design

> Como a plataforma é arquitetada para atender os requirements. Reflete a infraestrutura
> real na conta AWS 800712212925 e a org GitHub `goldenjackets-community`.

## 1. Arquitetura em duas camadas

```
┌─────────────────────────────────────────────────────────────────┐
│ INFRA COMPARTILHADA (1x, conta 800712212925)                      │
│                                                                   │
│  Cognito User Pool (us-east-1_Z0VzzrmIX)                          │
│    └─ grupos: brazil, usa, poland, india, ... (1 por chapter)     │
│                                                                   │
│  API Gateway HTTP (kqiq2bltjd)                                    │
│    ├─ /apply    → Lambda gj-apply   (cria PR no repo do chapter)  │
│    ├─ /admin    → Lambda gj-admin   (painel, isolado por grupo)   │
│    ├─ /article  → gj-apply (PR de artigo)                         │
│    ├─ /sponsor  → SNS + SES                                       │
│    └─ /click    → DynamoDB (tracking)                             │
│                                                                   │
│  IAM role github-actions-deploy (OIDC) → deploy de todos os repos │
│  Observability: 16 health checks + alarms + gj-expiration-monitor │
│  MCP Server (local) → operação via Kiro                           │
│  Site Global (goldenjackets.org, GitHub Pages)                    │
└─────────────────────────────────────────────────────────────────┘
                              │ serve / integra
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ INFRA DEDICADA (por chapter, ex: USA)                             │
│                                                                   │
│  Route53 HZ → ACM cert → CloudFront → S3 (site estático)          │
│  DynamoDB gj-usa-visitors ← Lambda gj-usa-counter (Function URL)  │
│  Backup vault gj-usa-backups (diário, 7d)                         │
│  Repo GitHub golden-jackets-usa → deploy.yml → S3 + CF invalidate │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Fluxo de aplicação de membro (self-service)

```
Membro no site do chapter
   │ clica "I'm a Golden Jacket 🏆" / "Join Us" → abre Apply Form
   │ preenche (nome, cidade/estado, cert date, LinkedIn, foto, tipo) + consent
   ▼
POST /apply (API Gateway) → Lambda gj-apply
   │ detecta chapter pelo ORIGIN header (REPO_MAP)
   │ monta card HTML + insere no index.html (antes do marker END_*)
   │ commit + abre PR no repo do chapter
   │ publica SNS gj-{code}-alerts (avisa o chapter lead)
   ▼
Chapter lead → Admin Panel (gj-admin) → valida + aprova PR
   ▼
Merge → GitHub Actions deploy.yml → S3 sync + CloudFront invalidation
   ▼
Card publicado no site + (workflow) cria Cognito user + email de boas-vindas
```

## 3. Provisionamento de chapter novo (`setup-chapter.sh`)

Ordem determinística (idempotente onde possível):
1. Route53 hosted zone → captura NS (enviar ao chapter lead)
2. ACM request-certificate + CNAME de validação na HZ
3. S3 bucket + website + public-access-block + bucket policy pública
4. CloudFront distribution (origin S3 website, redirect-to-https)
5. DynamoDB `gj-{code}-visitors`
6. Lambda `gj-{code}-counter` + Function URL pública (auth NONE)
7. Backup vault `gj-{code}-backups`
8. Cognito group `{code}` + admin-create-user (chapter lead) + add-to-group
9. Patch IAM `github-actions-deploy`: append ARNs do bucket + CloudFront

Depois (manual/RUNBOOK): criar repo GitHub, customizar site, secrets, integrar
REPO_MAP + CORS + site global.

## 4. Convenções (do steering existente)

- Domínio: `goldenjackets.{ccTLD}` (exceções: Brazil/USA).
- Código do chapter: lowercase de 2 letras quando possível (br, us, pl, in...).
- Card de membro: `<div class="member-card" data-state="XX">` + `card-number` + foto/avatar
  + tags (categoria). Inserir antes do marker da seção (END_GOLDEN_JACKETS / END_CHALLENGERS
  / etc). Card sem foto usa `<div class="avatar">` com iniciais.
- Contagem: por SEÇÃO (id=members/alumni/challengers/rising), nunca por classe CSS exata
  (founder/cofounder têm classe diferente mas SÃO golden).
- Deploy: push na branch default (detectar main vs master).

## 5. Decisões de design que resolvem os bugs conhecidos

- BUG-1 (PR vazio): validar no merge que o diff contém `member-card` e >N linhas adicionadas
  (hook/tool). Corrigir gj-apply para nunca commitar sem o card montado.
- BUG-2 (contadores): centralizar a atualização do global numa tool/hook que edita TODOS os
  pontos (ticker×2, hero data-target, tooltip, cards, meta) de uma vez.
- BUG-3 (link errado): link checker que varre os sites atrás de domínio/rota inexistente.
- BUG-4 (OIDC): trust policy com wildcard duplo (`repo:.../*` e `repo:...@*`) — já aplicado.
- BUG-5 (branch): scripts fazem `git symbolic-ref` / detectam default antes de push.

## 6. Componentes reutilizáveis

- `new-chapter/setup-chapter.sh` — provisiona infra dedicada.
- `new-chapter/template/` — site base + generate-site.sh (placeholders {{COUNTRY}}, {{CODE}}, etc).
- `new-chapter/RUNBOOK.md` — checklist do processo completo.
- `lambdas/shared/github_auth.py` — auth GitHub compartilhado.
- `mcp-server/server.py` — tools de operação.
