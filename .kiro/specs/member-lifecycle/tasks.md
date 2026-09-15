# Member Lifecycle — Tasks

> Este é um sistema JÁ EM PRODUÇÃO. As tarefas abaixo são de operação e melhoria
> incremental, não construção do zero. Marcar apenas o que for realmente executado.

## Operação (recorrente)

- [ ] Ao receber PR de membro: validar diff contém `member-card` não-vazio
- [ ] Validar `data-state` real (não "Other") e categoria correta
- [ ] Aprovar (merge-pr) ou rejeitar (close-pr) conforme governança de chapter lead
- [ ] Após merge: recontar e atualizar contadores em todos os pontos (counting-rules)
- [ ] Invalidar cache CloudFront se o site não refletir a mudança

## Melhorias (backlog)

- [ ] Validação automática de card no gj-apply (bloquear PR vazio na origem)
- [ ] Normalizar `state` na entrada do formulário (impedir "Other")
- [ ] Recontagem automática pós-merge (hook/MCP `recount-community`)
- [ ] Relatório de consistência: cards no site × membros no Cognito × contadores

## Automação disponível (já existe)

- Skill `approve-member` — passo a passo de aprovação
- Skill `recount-community` — recontagem
- Skill `move-member` — mover categoria/chapter
- MCP (a criar): `approve-member-pr`, `recount-community`, `add-member`,
  `validate-golden-jacket`, `community-stats`
