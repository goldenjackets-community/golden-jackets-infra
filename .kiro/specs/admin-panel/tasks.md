# Admin Panel — Tasks

> Sistema em produção. Tarefas de melhoria/operação, não construção do zero.

## Melhorias (backlog)

- [ ] Mover `GLOBAL_ADMINS` para env var/config (hoje hardcoded no código)
- [ ] Restringir CORS ao domínio do chapter em vez de `*`
- [ ] Log de auditoria das actions destrutivas (delete-user, restore-backup, close-pr)
- [ ] Paginação consistente em list-users/list-members
- [ ] Testes de autorização (chapter admin não age em chapter alheio; restore só global)

## Novas actions (se necessário — aditivas)

- [ ] Espelhar no gj-admin qualquer capability nova; documentar no steering `admin-actions`
- [ ] Nunca remover/renomear as 20 actions existentes

## Automação relacionada

- MCP tools a criar que orquestram actions: `approve-member-pr` (merge-pr),
  `community-stats` (list-members agregado), `add-member` (create-user)
- Skills: `backup-restore`, `manage-jobs`
