# Observability — Tasks

> Sistema parcialmente implementado. Tarefas de operação e expansão.

## Operação (recorrente)

- [ ] Revisar alarmes DOWN/RECOVERY chegando no SNS
- [ ] Acompanhar alertas do gj-expiration-monitor (domínios/certs perto de expirar)
- [ ] Verificar contadores de visitantes por chapter

## Melhorias (backlog)

- [ ] Health check para TODOS os chapters (garantir 1 por site)
- [ ] Habilitar contador de visitas nos chapters que ainda não têm (padrão Poland)
- [ ] MCP `check-broken-links` para varredura periódica de links quebrados
- [ ] MCP `community-stats` para snapshot de membros/certs/países sob demanda
- [ ] Alertas de expiração com múltiplas janelas (30/15/7 dias)

## Automação relacionada

- Lambdas: `gj-poland-counter`, `gj-architecture`, `gj-expiration-monitor`
- MCP a criar: `check-broken-links`, `community-stats`
- Skill: `recount-community` (existente)
