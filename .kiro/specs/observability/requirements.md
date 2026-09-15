# Observability — Requirements

> Como a comunidade monitora saúde dos sites, expiração de domínios/certs e métricas.
> Reverse-engineered da infra (Route53 health checks, CloudWatch alarms, SNS,
> gj-poland-counter) e da spec-mãe. Referência: steering `chapters-registry`, `known-bugs`.

## 1. Visão

Cada site tem um health check; alarmes notificam quando um site cai ou volta; um monitor
diário checa expiração de domínios, clientHold e certificados ACM; contadores de visitantes
existem por chapter (começando pela Poland). Notificações via SNS.

## 2. Requisitos

- **REQ-OB-1:** Route53 Health Check por site (1 por chapter) monitorando disponibilidade.
- **REQ-OB-2:** CloudWatch Alarms notificam via SNS em DOWN e em RECOVERY.
- **REQ-OB-3:** Tópico SNS de alertas (ex.: `gj-site-alerts`, `gj-brazil-alerts`).
- **REQ-OB-4:** Monitor diário de expiração (`gj-expiration-monitor`): domínios, clientHold
  e certificados ACM. Alertar com antecedência.
- **REQ-OB-5:** Contador de visitantes por chapter via DynamoDB + Lambda counter
  (`gj-poland-counter` → tabela `gj-poland-visitors`; padrão replicável por chapter).
- **REQ-OB-6:** Métricas de comunidade (membros por chapter/categoria, países) devem ser
  obteníveis sob demanda (base para MCP `community-stats`). Nunca inflar.
- **REQ-OB-7:** Diagrama de arquitetura ao vivo: Lambda `gj-architecture` gera
  `architecture-data.json` (nós/edges) consumido pelo site.

## 3. Constraints

- Health checks e alarms na conta 800712212925, região us-east-1.
- Poland tem contador próprio (DynamoDB); demais chapters seguem o mesmo padrão quando
  habilitados.

## 4. Fora de escopo

- Dashboards de terceiros; APM. Aqui é o monitoramento nativo AWS + notificação.
