# Golden Jackets — Counting Rules (Steering)

Como contar membros e certificações de forma consistente em toda a comunidade.

## Contagem de membros
- Contar por **SEÇÃO do HTML**, não por classe CSS exata:
  - `#members` (Golden) — inclui founder + cofounders (que têm classe diferente mas SÃO golden)
  - `#alumni`
  - `#challengers`
  - `#rising`
- Chapters pequenos podem não ter markers END_* — contar todas as `class="member-card"` da área.
- Método confiável: baixar index.html e contar `class="member-card` por seção com script (Python),
  com assert do count esperado. NUNCA usar sed cego (há muitos números que são coordenadas SVG).

## Fórmula de certificações (para o site global)
```
certs = (golden × 12) + (challenger × 10) + (rising × 8) + (alumni × 12)
```
Arredondar conservador pra baixo e usar sufixo "+" (ex: "2456+ Certifications").

## Onde os números aparecem (atualizar TODOS — ver known-bugs BUG-2)
No `golden-jackets-global`: ticker (2x), hero `data-target`, tooltip do mapa, cards de chapter,
meta description, status line. Não mexer no histórico/timeline datado.

## Snapshot de referência (validar ao vivo antes de usar como verdade)
Contagem é dinâmica — sempre recontar ao vivo antes de publicar número novo.
Fonte da verdade = cards nos sites LIVE de cada chapter (não valores hardcoded no ticker,
que são fallback pré-JS).

## Estados/regiões no card
`data-state="XX"` deve ser a UF/região real do membro. Evitar `data-state="Other"`
(infla o contador de "estados" com um fantasma). Corrigir para a sigla correta.
