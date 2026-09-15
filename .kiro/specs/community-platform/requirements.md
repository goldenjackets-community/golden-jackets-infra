# Golden Jackets Community Platform — Requirements

> Spec-mãe da plataforma da comunidade Golden Jackets. Especifica COMO a comunidade
> é construída: chapters, infraestrutura dedicada por chapter, infraestrutura
> compartilhada e o processo de operação. Fonte da verdade para recriar/escalar de
> forma padronizada.

## 1. Visão

A Golden Jackets é uma comunidade global de profissionais AWS all-certified (12/12 certs).
Cada país é um **chapter** com site próprio, mas todos compartilham a mesma fundação de
autenticação, automação e governança. A plataforma precisa permitir criar um chapter novo
em minutos, operar novos membros sem gargalo humano, e manter tudo padronizado.

Estado atual (referência): 15 chapters ativos, 21 países, ~214 membros, conta AWS
800712212925 (GoldenJackets-Community), org GitHub `goldenjackets-community`.

## 2. Categorias de Membro (régua sagrada)

- **Golden Jacket**: 12/12 certificações AWS ativas.
- **Challenger**: 10–11 certificações.
- **Rising**: 7–9 certificações.
- **Alumni**: já foi Golden Jacket, deixou alguma cert expirar.

REQ-CAT-1: Toda validação de membro DEVE respeitar essa régua. Nunca inflar números.
REQ-CAT-2: A contagem de certs por chapter usa: golden×12 + challenger×10 + rising×8 + alumni×12.

## 3. Requisitos — Infraestrutura Compartilhada (única, na conta 800712212925)

REQ-SHARED-1: **Cognito User Pool único** (`us-east-1_Z0VzzrmIX`) para todos os chapters,
com um **grupo por chapter** (brazil, usa, poland, ...). Isolamento por grupo.
REQ-SHARED-2: **API Gateway HTTP** único (`kqiq2bltjd`) com rotas `/apply`, `/article`,
`/sponsor`, `/click`, `/admin`. CORS deve aceitar o domínio de cada chapter.
REQ-SHARED-3: **Lambdas compartilhadas**:
  - `gj-apply` — recebe aplicação do site, cria PR no repo do chapter (detecta chapter pelo origin header via REPO_MAP).
  - `gj-admin` — painel admin (aprovar/rejeitar PR, criar/deletar Cognito user, métricas), isolado por grupo Cognito.
  - `gj-architecture` — descoberta de recursos para diagrama.
REQ-SHARED-4: **IAM role `github-actions-deploy`** com OIDC, permitindo cada repo de chapter
fazer deploy (S3 sync + CloudFront invalidation). Trust policy DEVE aceitar tanto
`repo:goldenjackets-community/*` quanto `repo:goldenjackets-community@*` (formato novo do
sub claim do GitHub para repos criados após ~jul/2026).
REQ-SHARED-5: **Observabilidade** — 16 Route53 Health Checks (1 por site) + CloudWatch Alarms
(notificam down E recovery) + Lambda `gj-expiration-monitor` (checa expiração de domínios,
clientHold e ACM certs, diário). SNS `gj-site-alerts`.
REQ-SHARED-6: **MCP Server** local (`mcp-server/server.py`) com tools de operação da comunidade.
REQ-SHARED-7: **Site Global** (`goldenjackets.org`, GitHub Pages, repo golden-jackets-global)
agrega números de todos os chapters ativos.

## 4. Requisitos — Infraestrutura Dedicada (por chapter)

Cada chapter DEVE ter, criado de forma idêntica (via `setup-chapter.sh`):

REQ-CHAP-1: **Route53 Hosted Zone** para o domínio do chapter (padrão `goldenjackets.{ccTLD}`;
exceções históricas: Brazil `goldenjacketsbrazil.com`, USA `goldenjacketsus.com`).
REQ-CHAP-2: **ACM Certificate** (wildcard) validado por DNS.
REQ-CHAP-3: **S3 bucket** com website hosting + bucket policy pública de leitura + block public
access configurado para website.
REQ-CHAP-4: **CloudFront distribution** (redirect-to-https, PriceClass_100) com o domínio custom
+ SSL do ACM.
REQ-CHAP-5: **DynamoDB table** `gj-{code}-visitors` (contador de visitas).
REQ-CHAP-6: **Lambda counter** `gj-{code}-counter` + Function URL pública (contador).
REQ-CHAP-7: **Backup vault** `gj-{code}-backups` (S3 do site, diário, retenção 7 dias).
REQ-CHAP-8: **Cognito group** `{code}` + usuário do chapter lead adicionado ao grupo.
REQ-CHAP-9: **Repo GitHub** `golden-jackets-{code}` (clonado de um chapter-base) com:
  - `index.html` (site), `members.html` (Lounge), `admin.html`, `privacy.html`
  - `.github/workflows/deploy.yml` (deploy no push)
  - secret `CLOUDFRONT_DIST_ID` + `AWS_ACCOUNT_GJ`
  - `.kiro/steering/` (regras do projeto)

## 5. Requisitos — Integração de um Chapter Novo

REQ-INT-1: `gj-apply` REPO_MAP DEVE mapear o domínio novo → repo do chapter.
REQ-INT-2: `gj-admin` DEVE reconhecer o chapter novo nos mappings.
REQ-INT-3: API Gateway CORS DEVE incluir o domínio novo.
REQ-INT-4: Site Global DEVE ser atualizado (contador de membros/países, mapa, ticker, cards).
REQ-INT-5: IAM `github-actions-deploy` DEVE incluir ARNs do novo bucket S3 e da nova CloudFront.

## 6. Requisitos — Operação de Membros (self-service)

REQ-OP-1: Aplicação acontece PELO SITE (Apply Form), não por adição manual. Fluxo:
  Membro preenche form → `gj-apply` cria PR no repo do chapter → chapter lead aprova no
  Admin Panel → deploy automático publica o card → membro recebe acesso ao Lounge.
REQ-OP-2: Chapter leads aprovam os PRs dos SEUS chapters. Global lead NÃO mergeia direto
  sem validar (evitar atropelar o lead + risco de card vazio).
REQ-OP-3: Antes de aprovar, validar: card não veio vazio (bug conhecido do gj-apply),
  LinkedIn confere, categoria correta pela contagem de certs.
REQ-OP-4: UX de aplicação DEVE ter caminho único e claro (hoje há atrito: "Get in Touch"
  aponta pro LinkedIn e "Join Us"/"I'm a Golden Jacket" abre o form — gera confusão).

## 7. Bugs Conhecidos (a plataforma deve prevenir)

- BUG-1: `gj-apply` às vezes gera PR VAZIO (card não inserido no index.html). Deploy "passa"
  mas membro não aparece. Requer validação pós-abertura de PR.
- BUG-2: Contadores do site global precisam ser atualizados em MÚLTIPLOS lugares (ticker 2x,
  hero `data-target`, tooltip mapa, cards, meta). Esquecer o `data-target` deixa o número
  grande visível errado.
- BUG-3: Links quebrados por typo de domínio (ex: `golden-jackets-usa` vs `golden-jackets-us`).
- BUG-4: OIDC sub claim mudou formato para repos novos → deploy falha silenciosamente se a
  trust policy não aceitar `repo:goldenjackets-community@*`.
- BUG-5: Branch default varia por repo (main vs master) — scripts devem detectar.

## 8. Fora de Escopo

- Monetização / Study Program (futuro).
- Migração de domínios existentes fora do padrão (Brazil/USA ficam como estão).
