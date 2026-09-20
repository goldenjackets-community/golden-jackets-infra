# Golden Jackets Community Power

> **Platform-as-a-Power** — a operação completa da comunidade Golden Jackets
> empacotada num único Kiro Power. Instala por URL, opera qualquer chapter sem setup manual.

**Versão:** 1.0
**Autor:** Ricardo Gulias (Founder & Global Lead, Golden Jackets)
**Repo:** goldenjackets-community/golden-jackets-infra
**Conta AWS da comunidade:** 800712212925 · Cognito pool `us-east-1_Z0VzzrmIX` · API `kqiq2bltjd`

---

## O que é

Este Power empacota tudo que um **chapter leader** precisa pra operar sua comunidade
Golden Jackets pelo Kiro — sem clonar repo, configurar MCP na mão, copiar steering ou
instalar hooks um a um. Uma URL, e o ambiente vem pronto.

**Antes deste Power:** cada líder de chapter (Vishnu/Índia, Eyal/Israel, Justin/USA...)
precisava montar o ambiente manualmente — clonar o repo, editar `mcp.json`, copiar as
regras, setar profile AWS. Só o founder sabia fazer.

**Com este Power:** `instalar → operar`. Distribuição de ownership de verdade.

---

## O que vem dentro (a caixa)

### 🔌 MCP Server — `goldenjackets` (11 tools)
Servidor MCP conectado à conta da comunidade (profile `gj-mcp`, chave estática read-only + ações controladas).

| Tool | O que faz | Tipo |
|------|-----------|------|
| `list-members` | Lista membros de um chapter | leitura |
| `list-chapters` | Lista todos os chapters | leitura |
| `chapter-status` | Status CloudFront/S3 de todos os chapters | leitura |
| `community-stats` | Estatísticas consolidadas da comunidade | leitura |
| `validate-golden-jacket` | Valida categoria por nº de certs (12=Golden, 10-11=Challenger, 7-9=Rising) | leitura |
| `recount-community` | Reconta membros e certs por chapter | leitura |
| `check-broken-links` | Varre links quebrados/typos de domínio | leitura |
| `invalidate-cache` | Invalida cache CloudFront de um chapter | escrita |
| `suggest-topic` | Sugere tópico de artigo (SNS) | escrita |
| `approve-member-pr` | Aprova PR de novo membro (orquestra gj-admin) | escrita* |
| `add-member` | Adiciona membro (orquestra gj-admin) | escrita* |

\* Ações de escrita exigem `GJ_ADMIN_TOKEN` (JWT Cognito) — sem token, retornam erro seguro (não fazem nada).

### 🛠️ Skills (7)
Habilidades operacionais que o Kiro executa a pedido:
- `approve-member` — aprova membro (apply → PR → merge → card → recount)
- `move-member` — move membro entre categorias/chapters
- `recount-community` — recontagem oficial (régua sagrada 12/12)
- `create-chapter` — provisiona um chapter novo (infra + site)
- `deploy-lambda` — deploy das Lambdas compartilhadas
- `backup-restore` — backup e restauração de chapter
- `manage-jobs` — gerencia o Job Board da comunidade

### 🪝 Hooks (6) — validação automática no save
Rodam sozinhos toda vez que um arquivo é salvo, blindando o líder de erro:
- **Validate Member Card on Save** — garante card completo (nome, `data-state` real, categoria, foto, nº)
- **Global Counters Consistency Check** — contadores do site batem com os cards
- **Broken Link & Domain Typo Check** — pega link/domínio errado antes do deploy
- **Chapter Branch Awareness Before Deploy** — avisa branch correto (main vs master varia por chapter)
- **MCP Server Edit Guard** — protege o server MCP de edição acidental
- **Spec Sync Reminder** — lembra de sincronizar a spec quando o código muda

### 📐 Steering (10) — as regras já embutidas
O Kiro do líder já "sabe" tudo, sem precisar repetir contexto:
- `chapters-registry` — domínio, bucket, CloudFront dist, branch de cada chapter (fonte da verdade)
- `counting-rules` — a régua sagrada: Golden 12/12, Challenger 10-11, Rising 7-9, Alumni; fórmula de certs
- `community-rules` — regras de convivência/aprovação da comunidade
- `admin-actions` — as 20 ações do gj-admin documentadas
- `conventions` — convenções de card, código, deploy
- `security` — least privilege, sem segredo em prompt/repo
- `github-app` — GitHub App, OIDC role, REPO_MAP
- `global-stats` — regra do site global (data.json fonte, never-decrease)
- `infrastructure` — arquitetura serverless da comunidade
- `known-bugs` — armadilhas conhecidas (ex: bug do gj-apply gerando PR vazio)

---

## Instalação (o pitch do "uma URL")

```
# No Kiro do chapter leader:
kiro power install https://github.com/goldenjackets-community/golden-jackets-infra

# Configurar credencial da comunidade (fornecida pelo founder):
export GJ_ADMIN_TOKEN=<jwt-cognito>   # só pra ações de escrita
```

Pronto. O líder passa a operar o chapter dele pelo Kiro:
- "lista os membros do meu chapter"
- "recont a comunidade"
- "qual o status dos chapters?"
- "valida se fulano é Golden Jacket (12 certs)"
- "aprova o PR do novo membro"

---

## Por que isso importa (a visão)

A maior fragilidade de uma comunidade global é depender de **uma pessoa só**.
Este Power transforma a operação da Golden Jackets de *"a ferramenta do founder"*
em **infraestrutura distribuída** — cada líder de chapter, em qualquer país, instala
uma URL e opera com a mesma potência, respeitando as mesmas regras (steering embutido)
e blindado pelos mesmos hooks de validação.

**Spec-driven → Steering → Skills → Hooks → MCP → Power.**
O topo da montanha: platform-as-code virando **comunidade-as-a-Power**.

---

## Segurança

- MCP read-only por padrão; ações de escrita gated por token Cognito.
- Zero credenciais no manifesto (só nome de profile/env var).
- Steering `security` embutido reforça least-privilege em qualquer operação.
- Hooks previnem erro humano antes do deploy (card inválido, link quebrado, branch errado).

---

*Golden Jackets Community · Kiro Power v1.0 · Setembro 2026*
