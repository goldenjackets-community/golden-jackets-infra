# Chapter Provisioning — Design

> Arquitetura do provisionamento. Detalhe executável no RUNBOOK.

## Duas vias de provisionamento

1. **Workflow `create-chapter.yml`** (workflow_dispatch): passa inputs e a Action assume a
   role OIDC `github-actions-deploy` e cria a infra passo a passo (Route53 → ACM →
   S3 → CloudFront → DynamoDB → Lambda counter → backup vault → Cognito).
2. **Script `new-chapter/setup-chapter.sh`** (local, profile `gj`): mesmo resultado,
   rodado da máquina do operador. Ver RUNBOOK Fase 1.

## Fases (resumo — detalhe no RUNBOOK)

| Fase | O que | Automação |
|---|---|---|
| 1. Infra AWS | zone, cert, bucket, CF, dynamo, counter, vault, cognito | workflow/script |
| 2. DNS | nameservers → leader → propagação → validar cert → CF domain → A/AAAA | manual + leader |
| 3. Site | criar repo (base Chile), customizar, secrets, deploy | manual |
| 4. Integrações | REPO_MAP (gj-apply), gj-admin, CORS, site global | manual |
| 5. Comunicação | guide, LinkedIn, anúncio | manual |

## Convenções de nomes (por `code`)

- Repo: `golden-jackets-<code>`
- Bucket: `<domain>`
- Counter table: `gj-<code>-visitors`
- Counter function: `gj-<code>-counter`
- Backup vault: `gj-<code>-backups`
- Cognito group: `<code>`

## Lições aprendidas relevantes (do RUNBOOK)

- Mapa do chapter: usar SVG Wikimedia/Albers, não SimpleMaps (viewBox achatado).
- Mapa global: ativar chapter trocando fill/flight-path/pin/card status.
- Países pequenos (Israel, Singapura): só pin com radar, sem path individual.
- GitHub Pages leva 2-3 min; testar com `?v=X` ou aba anônima.
- Se Actions falhar: deploy manual via `aws s3 cp ... --profile gj`.

## Dependências compartilhadas afetadas

- gj-apply (REPO_MAP), gj-admin (mappings), API CORS, site global. Toda criação de chapter
  DEVE atualizar esses 4 pontos, senão o apply/admin do chapter novo não funciona.
