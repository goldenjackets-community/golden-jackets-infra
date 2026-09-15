# Skill: Create Chapter

Criar um chapter novo (país) de ponta a ponta. Uso: "criar chapter da Argentina" / "novo chapter".

> Esta skill ORQUESTRA o processo. O passo-a-passo detalhado e o script vivem em:
> - `new-chapter/RUNBOOK.md` (processo completo, 5 fases)
> - `new-chapter/setup-chapter.sh` (provisiona infra dedicada)
> - `new-chapter/TEMPLATE.md` + `POST-SETUP.md` (checklist)
> NÃO duplicar esse conteúdo aqui — seguir o RUNBOOK.

## Pré-requisitos
- Chapter Lead confirmado (é Golden Jacket 12/12) + domínio registrado por ele.
- Profile AWS `gj` (conta 800712212925) + gh autenticado na org.

## Fluxo (resumo — detalhe no RUNBOOK)
1. **Infra dedicada** — rodar `new-chapter/setup-chapter.sh` (Route53, ACM, S3, CloudFront,
   DynamoDB, Lambda counter, backup vault, Cognito group + lead). ~5 min.
2. **DNS** — enviar NS ao lead → ele aponta → validar ACM → domínio custom no CloudFront →
   A/AAAA no Route53. (1–48h, depende do lead.)
3. **Site** — criar repo `golden-jackets-<code>` (clonar de um chapter-base), customizar
   (país, bandeira, mapa SVG, card do lead #1, sponsor tiers moeda local, counter URL, privacy),
   secret `CLOUDFRONT_DIST_ID` + `AWS_ACCOUNT_GJ`, push → deploy.
4. **Integrações** — `gj-apply` REPO_MAP + `gj-admin` mappings + API Gateway CORS +
   site global (contador/mapa/ticker/cards) + IAM `github-actions-deploy` (ARNs S3+CF).
5. **Comunicação** — Chapter Leader Guide (PDF) pro lead + LinkedIn Company Page + anúncio.

## Checklist rápido (copy do RUNBOOK)
```
[ ] Infra AWS (setup-chapter.sh)   [ ] NS enviados
[ ] DNS + ACM validado             [ ] CloudFront domínio custom
[ ] Route53 A+AAAA                 [ ] Repo + site customizado
[ ] CLOUDFRONT_DIST_ID secret      [ ] Deploy OK
[ ] gj-apply REPO_MAP              [ ] gj-admin mappings
[ ] CORS API Gateway              [ ] Site global atualizado
[ ] Chapter Leader Guide          [ ] LinkedIn page + anúncio
```

## Regras (ver community-rules)
- Domínio padrão `goldenjackets.{ccTLD}`.
- Só criar chapter com lead REAL confirmado (não fantasma pra bater meta).
- Trust policy OIDC já aceita repos novos (`repo:...@*`) — ver known-bugs BUG-4.
