# Golden Jackets Community Platform — Tasks

> Plano de execução derivado de requirements + design. Marca o que JÁ existe (feito) e o
> que falta para a plataforma ficar padronizada, resiliente e escalável.

## Bloco A — Documentar o que já existe (baseline)
- [x] A1. Infra compartilhada operacional (Cognito, API GW, gj-apply, gj-admin, OIDC)
- [x] A2. `setup-chapter.sh` provisiona infra dedicada (Route53, ACM, S3, CF, Dynamo, Lambda counter, backup, Cognito)
- [x] A3. Observabilidade (16 health checks + alarms + gj-expiration-monitor)
- [x] A4. MCP server com 5 tools (list-members, list-chapters, chapter-status, invalidate-cache, suggest-topic)
- [x] A5. Steering: conventions, infrastructure, security
- [x] A6. Site Global (goldenjackets.org)
- [ ] A7. Consolidar RUNBOOK + esta spec como fonte única da verdade (linkar no README)

## Bloco B — Steering novo (codificar conhecimento do KB)
- [ ] B1. `community-rules.md` — régua de categorias, "chapter leads aprovam", integridade > vaidade
- [ ] B2. `chapter-operations.md` — padrão de card, markers, REPO_MAP, processo de chapter novo
- [ ] B3. `known-bugs.md` — os 5 bugs conhecidos + como prevenir/detectar
- [ ] B4. `counting-rules.md` — contagem por seção + fórmula de certs

## Bloco C — Hooks (automação de dor recorrente)
- [ ] C1. Hook validate-member-pr: on PR aberto → checa card não-vazio + LinkedIn + categoria → comenta ✅/❌
- [ ] C2. Hook recount-on-merge: on PR de membro mergeado → recalcula contadores + PR no global
- [ ] C3. Hook deploy-sanity: pós-deploy → smoke test (links, contador) → avisa se quebrou
- [ ] C4. Hook link-checker: periódico → varre sites atrás de link/domínio quebrado

## Bloco D — Expandir MCP Server (operação via Kiro)
- [ ] D1. Tool `approve-member-pr` — lista PRs, valida card, mergeia (o que foi feito na mão hoje)
- [ ] D2. Tool `recount-community` — conta membros de todos os chapters ao vivo
- [ ] D3. Tool `add-member` — adiciona membro direto (nome, LinkedIn, foto, chapter)
- [ ] D4. Tool `check-broken-links` — retorna links quebrados dos sites
- [ ] D5. Tool `community-stats` — dashboard (membros, países, certs, PRs pendentes, saúde)
- [ ] D6. Tool `validate-golden-jacket` — recebe LinkedIn/Credly, valida 12 certs

## Bloco E — Corrigir bugs na raiz
- [ ] E1. Fix gj-apply: nunca commitar PR sem o card montado (resolve BUG-1)
- [ ] E2. Unificar UX do Apply Form nos 15 sites: caminho único de aplicação (resolve BUG-4/atrito)
      (o "Get in Touch → LinkedIn" some ou vira secundário; "Join / I'm a Golden Jacket" é o CTA)
- [ ] E3. Ferramenta única de atualização de contadores do global (resolve BUG-2)
- [ ] E4. Auditar branch default de todos os repos + padronizar scripts (resolve BUG-5)

## Bloco F — Escala
- [ ] F1. `setup-chapter.sh` 100% end-to-end (incluir criação de repo + secrets + REPO_MAP + CORS + global)
- [ ] F2. Self-service tier upgrade (Rising → Challenger → Golden ao tirar cert)
- [ ] F3. Portal/dashboard de saúde da comunidade (visão do global lead)

## Prioridade sugerida (retorno x esforço)
1. B1 + B3 (steering rápido, alto valor — codifica o que se repete toda sessão)
2. C1 (hook validate-member-pr — mata BUG-1, dor de hoje)
3. D1 + D2 (tools que transformam o trabalho manual de hoje em comando)
4. E2 (UX do apply — resolve o atrito do Nishith nos 15 sites)
5. Resto conforme necessidade.

## Notas de execução
- Sessão Kiro pode rodar como user `cloud2point` (sem escrita em /home/gulias) — usar `gh api` ou /tmp quando necessário.
- Deploy dos sites: push na branch default de cada repo (detectar main vs master).
- MCP usa profile `gj-mcp` (access key estática, não SSO) — nunca quebra.
