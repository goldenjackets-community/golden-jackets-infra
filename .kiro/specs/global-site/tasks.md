# Global Site — Tasks

> Sistema em produção. Operação e melhoria.

## Operação (recorrente)

- [ ] Ao adicionar membros/chapter: rodar `update-stats.yml` (manual) OU atualizar
      data.json + index.html à mão, mantendo todos os pontos coerentes (BUG-2)
- [ ] Conferir que ticker (2x), hero data-target, tooltips e meta batem
- [ ] Ativar chapter novo no mapa (fill/flight/pin/card) quando entrar

## Melhorias (backlog)

- [ ] Reativar o CRON com segurança (a trava "never decrease" já existe; validar que
      deploys quebrados não derrubam mais a contagem antes de religar)
- [ ] Renderizar contadores 100% a partir de data.json no client (eliminar sed no HTML)
- [ ] Distinguir rising nos certs (hoje o workflow só separa golden/challenger/alumni)
- [ ] MCP `community-stats` como fonte alternativa de conferência (Cognito × site × data.json)

## Automação relacionada

- Workflow: `golden-jackets-global/.github/workflows/update-stats.yml`
- Steering: `global-stats`, `counting-rules`, `chapters-registry`
- MCP: `community-stats`, `check-broken-links`
