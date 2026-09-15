# Skill: Manage Jobs (Job Board)

Operar o job board da comunidade: publicar, listar, remover vagas e registrar
candidaturas. Uso: "posta uma vaga X no chapter Y", "lista as vagas", "remove a vaga Z".

## Regras (ver steering admin-actions)
- Actions reais do gj-admin: `post-job`, `list-jobs`, `delete-job`, `apply-job`.
- Essas actions estão em `skip_chapter_actions` (não exigem match de chapter), mas exigem
  JWT válido.
- Não reimplementar — orquestrar as actions existentes.

## Passos

### 1. Publicar vaga (post-job)
- Chamar `POST /admin` com `action=post-job` e os campos da vaga (título, empresa,
  descrição, link, chapter).
- Confirmar que a vaga aparece com `list-jobs`.

### 2. Listar vagas (list-jobs)
- `action=list-jobs` retorna as vagas ativas.

### 3. Remover vaga (delete-job)
- `action=delete-job` com o id da vaga. Confirmar remoção com `list-jobs`.

### 4. Candidatura (apply-job)
- `action=apply-job` registra o candidato numa vaga.

## Boas práticas
- Manter descrições sem PII desnecessária.
- Vagas expiradas devem ser removidas (delete-job) para o board ficar limpo.
