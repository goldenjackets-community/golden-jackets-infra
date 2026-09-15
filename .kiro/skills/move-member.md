# Skill: Move Member

Mover um membro entre categorias (Golden/Challenger/Rising/Alumni) ou entre chapters,
mantendo a integridade dos números. Uso: "move o membro X pra Alumni" ou "move o Fulano
do chapter Y pro Z".

## Regras (ver steering counting-rules + community-rules + admin-actions)
- Categorias pela régua sagrada: Golden=12/12, Challenger=10-11, Rising=7-9, Alumni=expirou.
- Nunca inflar números. Após mover, RECONTAR (ver skill recount-community).
- Chapter lead move dentro do próprio chapter; movimentação entre chapters = Global Lead valida.
- A action real é `move-member` do gj-admin (não reimplementar).

## Passos

### 1. Identificar o membro e o destino
- Confirmar chapter atual, categoria atual, chapter/categoria destino.
- Se for troca de chapter, confirmar com Global Lead.

### 2. Executar via gj-admin
- Chamar action `move-member` (POST /admin) com o membro e destino.
- Alternativamente, editar o card no `index.html` do(s) repo(s) via PR se for só categoria.

### 3. Atualizar o card e os contadores
- Ajustar a categoria/tags no card do membro.
- Recontar e atualizar contadores em TODOS os pontos (ver counting-rules): ticker (2x),
  hero data-target, tooltip do mapa, cards, meta.

### 4. Validar
- Conferir que o total bate: cards no site × grupos Cognito × contadores.
- Nunca deixar número inflado ou inconsistente.

## Bugs a evitar (known-bugs)
- Esquecer o hero `data-target` ao recontar.
- Branch default varia (main/master) ao abrir PR — detectar antes.
