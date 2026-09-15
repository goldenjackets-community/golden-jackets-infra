# Observability — Design

> Componentes reais de monitoramento.

## Topologia

```
Site do chapter (CloudFront/S3)
  ▲                     │
  │ health check        │ visitas
Route53 Health Check    ▼
  │               API GW → Lambda gj-<code>-counter → DynamoDB gj-<code>-visitors
  ▼
CloudWatch Alarm (DOWN / RECOVERY)
  ▼
SNS topic (gj-site-alerts / gj-<chapter>-alerts)
  ▼
Notificação (email/WhatsApp/etc.)

Diário:
Lambda gj-expiration-monitor → checa domínios + clientHold + ACM certs → SNS

Sob demanda:
Lambda gj-architecture → architecture-data.json (nós/edges) → site (diagrama vivo)
```

## Componentes

| Componente | Papel | Recurso |
|---|---|---|
| Route53 Health Check | Disponibilidade do site | 1 por chapter |
| CloudWatch Alarms | Detecta DOWN/RECOVERY | por health check |
| SNS | Entrega de alertas | `gj-site-alerts`, `gj-brazil-alerts`, ... |
| gj-expiration-monitor | Expiração domínio/cert/clientHold | Lambda diária |
| gj-poland-counter | Contador de visitas | `lambdas/gj-poland-counter/` + DynamoDB |
| gj-architecture | Dados do diagrama de arquitetura | `lambdas/gj-architecture/` → S3 json |

## Contador (gj-poland-counter)

- Atualiza `total_visits` (sempre) e `unique_visitors` (put condicional por IP) na tabela
  `gj-poland-visitors`, item `id=counter`.
- Padrão replicável: cada chapter novo ganha `gj-<code>-visitors` + `gj-<code>-counter`
  (ver chapter-provisioning).

## Métricas de comunidade

- Fonte de verdade dos números: cards nos sites + grupos Cognito. A recontagem (skill
  `recount-community` / MCP `community-stats`) agrega isso. Regra de integridade: nunca
  inflar (ver counting-rules).

## Decisões

- Monitoramento nativo AWS (Route53 + CloudWatch + SNS) por simplicidade e custo.
- Diagrama de arquitetura é gerado por Lambda para refletir o estado real dos recursos.
