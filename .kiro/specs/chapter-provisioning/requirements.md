# Chapter Provisioning — Requirements

> Como um chapter novo é criado, da infra AWS ao anúncio. NÃO duplica o RUNBOOK — este
> spec é o contrato/visão; o passo a passo executável vive em `new-chapter/RUNBOOK.md`,
> `new-chapter/TEMPLATE.md`, `new-chapter/POST-SETUP.md` e no workflow
> `.github/workflows/create-chapter.yml`. Referência: steering `chapters-registry`,
> `github-app`, `known-bugs`.

## 1. Visão

Criar um chapter = provisionar infra dedicada (DNS, cert, S3, CloudFront, DynamoDB,
Lambda counter, backup vault, grupo Cognito) + repo do site + integrar nas Lambdas
compartilhadas (gj-apply REPO_MAP, gj-admin, CORS) + atualizar o site global. Meta: um
chapter novo em minutos na parte automatizada.

## 2. Requisitos

- **REQ-CP-1:** A infra AWS é provisionada por automação: workflow `create-chapter.yml`
  (workflow_dispatch com inputs: country, code, domain, leader_*, flag, simplemaps_code,
  branch) OU script `new-chapter/setup-chapter.sh`.
- **REQ-CP-2:** Recursos criados por chapter: Route53 zone, ACM cert (wildcard), S3 bucket
  (= domínio), CloudFront dist, DynamoDB `gj-<code>-visitors`, Lambda `gj-<code>-counter`
  com Function URL, backup vault `gj-<code>-backups`, grupo Cognito + user do leader.
- **REQ-CP-3:** DNS depende do leader (apontar nameservers). Cert só valida após propagação.
- **REQ-CP-4:** O repo do site é criado clonando um chapter base (ex.: Chile) e customizado
  (nome, bandeira, mapa, card do leader #1, sponsors moeda local, counter URL, privacy).
- **REQ-CP-5:** Secrets por repo novo: `AWS_ACCOUNT_GJ` = 800712212925 e `CLOUDFRONT_DIST_ID`.
- **REQ-CP-6:** Integração obrigatória nas Lambdas: adicionar domínio ao REPO_MAP do
  gj-apply, mappings do gj-admin, e origin no CORS da API.
- **REQ-CP-7:** Atualizar o site global (contador países/membros, mapa, ticker) sem inflar.
- **REQ-CP-8:** Branch default do repo novo deve ser registrado no steering
  `chapters-registry` (varia main/master).
- **REQ-CP-9:** OIDC trust policy deve aceitar `repo:goldenjackets-community@*` além de
  `/*` (chapters criados após ~jul/2026 usam formato novo — ver known-bugs).
- **REQ-CP-10:** Comunicação: enviar Chapter Leader Guide, criar LinkedIn page, anunciar.

## 3. Fora de escopo

- Passo a passo detalhado (está no RUNBOOK) — não repetir aqui.
