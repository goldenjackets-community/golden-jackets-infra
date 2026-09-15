# Chapter Provisioning — Tasks

> Checklist por chapter novo. Baseado no RUNBOOK (fonte executável). Use este como
> visão; o passo a passo copy-paste está em `new-chapter/RUNBOOK.md`.

## Por chapter novo

- [ ] Fase 1: rodar `create-chapter.yml` (ou `setup-chapter.sh`) — infra AWS
- [ ] Fase 2: enviar nameservers ao leader; aguardar DNS; validar cert; CF domain; A/AAAA
- [ ] Fase 3: criar repo (base Chile), customizar site, secrets (`AWS_ACCOUNT_GJ`,
      `CLOUDFRONT_DIST_ID`), deploy
- [ ] Fase 4: REPO_MAP no gj-apply + gj-admin mappings + CORS + site global
- [ ] Registrar branch default no steering `chapters-registry`
- [ ] Confirmar OIDC trust aceita `@*` (senão deploy falha)
- [ ] Fase 5: Chapter Leader Guide + LinkedIn + anúncio

## Melhorias (backlog)

- [ ] Automatizar Fase 4 (integração nas Lambdas) — hoje é manual e fácil de esquecer
- [ ] Skill `create-chapter` já cobre o fluxo; manter alinhada ao RUNBOOK
- [ ] Validador pós-provisionamento (health check do novo site + apply funcionando)

## Automação relacionada

- Skill `create-chapter` (existente)
- Steering `chapters-registry` (atualizar ao final)
