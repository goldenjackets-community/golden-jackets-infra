# Admin Actions — Referência do gj-admin

> Referência das 20 actions do Lambda `gj-admin` (`lambdas/gj-admin/gj_admin.py`).
> Fonte de verdade para qualquer skill/MCP que opere o painel admin. NÃO remover nem
> renomear actions existentes — o frontend (painel admin dos sites) depende delas.
> Validado em 2026-09-14.

## Endpoint e autenticação

- **URL:** `POST https://kqiq2bltjd.execute-api.us-east-1.amazonaws.com/admin`
- **Auth:** JWT do Cognito (claim `email`). O caller é identificado por email + grupos.
- **Global admins:** `ricardo.gulias@goldenjacketsbrazil.com`, `erickmancz@gmail.com`,
  `wagnermazevedo@hotmail.com` — veem/agem em todos os chapters.
- **Chapter admins:** só o próprio chapter (grupo Cognito).
- **Body:** `{ "action": "...", "chapter": "...", ... }`. Se `chapter` não vier, é
  detectado pelo header `origin` ou pelo primeiro grupo do caller.

## Controle de acesso

- Actions que **NÃO** exigem match de chapter (`skip_chapter_actions`):
  `create-chapter`, `chapter-status`, `post-job`, `list-jobs`, `delete-job`,
  `apply-job`, `submit-article`, `suggest-topic`.
- Demais actions: caller precisa ser global admin OU pertencer ao chapter alvo (403 senão).
- `restore-backup`: **somente global admin**.

## As 20 actions

### Usuários (Cognito)
| Action | O que faz | Restrição |
|---|---|---|
| `list-users` | Lista usuários do chapter (ou todos, se global admin sem filtro) | chapter |
| `create-user` | Cria user no pool + adiciona ao grupo do chapter | chapter |
| `delete-user` | Remove user (valida que pertence ao chapter do caller) | chapter |
| `resend-pending` | Reenvia convite p/ usuários em FORCE_CHANGE_PASSWORD | chapter |

### Backup (AWS Backup)
| Action | O que faz | Restrição |
|---|---|---|
| `backup-status` | Lista jobs recentes do vault do chapter | chapter |
| `restore-backup` | Restaura do backup mais recente COMPLETED → bucket | **global admin** |

Vaults: `gj-poland-backups` (PL), `gj-uk-backups` (UK), `gj-chile-backups` (CL),
`gj-site-backups` (default/BR). Role: `arn:aws:iam::800712212925:role/gj-backup-role`.

### Conteúdo / Artigos
| Action | O que faz | Restrição |
|---|---|---|
| `submit-article` | Submete artigo (cria PR/conteúdo no repo) | livre* |
| `suggest-topic` | Sugere tópico de artigo (notifica) | livre* |

### Job Board
| Action | O que faz | Restrição |
|---|---|---|
| `post-job` | Publica vaga no job board | livre* |
| `list-jobs` | Lista vagas | livre* |
| `delete-job` | Remove vaga | livre* |
| `apply-job` | Candidata-se a uma vaga | livre* |

### Pull Requests (membros)
| Action | O que faz | Restrição |
|---|---|---|
| `list-prs` | Lista PRs abertos de membros no repo do chapter | chapter |
| `merge-pr` | Faz merge do PR (aprova membro) + rebuild dos PRs restantes | chapter |
| `close-pr` | Fecha PR sem merge (rejeita) | chapter |

`merge-pr` chama `rebuild_remaining_prs` para renumerar cards dos PRs abertos após o merge.

### Membros / cards
| Action | O que faz | Restrição |
|---|---|---|
| `list-members` | Lista membros (cards) do chapter | chapter |
| `update-photo` | Atualiza foto de um membro | chapter |
| `move-member` | Move membro entre chapters/categorias | chapter |

### Operação
| Action | O que faz | Restrição |
|---|---|---|
| `chapter-status` | Status agregado do(s) chapter(s) | livre |
| `create-chapter` | Dispara criação de novo chapter | livre* (uso admin) |

\* "livre" = não exige match de chapter, mas ainda exige JWT válido.

## Regras ao mexer aqui

- Alterações no `gj_admin.py` são **aditivas**: adicione novas actions no fim da cadeia
  `elif action == ...`. Nunca remova/renomeie as 20 acima.
- Deploy: push em `main` do repo infra → workflow "Deploy Lambdas". Ver skill `deploy-lambda`.
- Preserve o modelo de acesso (global vs chapter admin) em qualquer action nova.
