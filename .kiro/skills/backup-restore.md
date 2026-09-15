# Skill: Backup & Restore

Verificar status de backup e restaurar um site de chapter a partir do backup mais
recente. Uso: "qual o status dos backups do chapter X?" ou "restaura o site do chapter Y".

## Regras (ver steering admin-actions — AÇÃO SENSÍVEL)
- Actions do gj-admin: `backup-status` (leitura) e `restore-backup` (destrutiva).
- `restore-backup` é EXCLUSIVO de global admin. Chapter admin não pode restaurar.
- Restore sobrescreve o bucket do site com o backup — confirmar antes.
- Vaults: `gj-poland-backups` (PL), `gj-uk-backups` (UK), `gj-chile-backups` (CL),
  `gj-site-backups` (default/BR). Role: `arn:aws:iam::800712212925:role/gj-backup-role`.

## Passos

### 1. Ver status (backup-status)
- `POST /admin` com `action=backup-status` e o chapter → lista jobs recentes do vault.
- Confirmar que há um backup COMPLETED antes de pensar em restaurar.

### 2. Restaurar (restore-backup) — só global admin
- CONFIRMAR com o operador que o restore é necessário (é destrutivo: sobrescreve o site).
- `action=restore-backup` restaura do backup mais recente COMPLETED para o bucket do chapter.
- Se não houver backup COMPLETED, a action retorna aviso — não força nada.

### 3. Verificar
- Após restore, validar o site no ar e invalidar cache CloudFront se necessário
  (ver MCP/skill de invalidate-cache).

## Segurança
- Nunca afrouxar a checagem de global admin no restore.
- Registrar quem executou o restore (auditoria — backlog na spec admin-panel).
