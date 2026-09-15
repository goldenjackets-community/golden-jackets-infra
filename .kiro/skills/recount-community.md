# Skill: Recount Community

Recontar membros e certificações de todos os chapters ao vivo e atualizar o site global.
Uso: "reconta a comunidade" / "quantos membros temos agora?".

## Regras (ver steering counting-rules + known-bugs)
- Contar por SEÇÃO, não por classe CSS exata. Fonte da verdade = cards nos sites LIVE.
- Fórmula certs: golden×12 + challenger×10 + rising×8 + alumni×12.

## Passos

### 1. Baixar index.html de cada chapter e contar por seção
Repos (branch default varia — main: brazil/belgium/italy/uae; master: resto):
```bash
for repo in golden-jackets-brazil golden-jackets-usa golden-jackets-india golden-jackets-uk \
  golden-jackets-colombia golden-jackets-chile golden-jackets-france golden-jackets-peru \
  golden-jackets-israel golden-jackets-italy golden-jackets-poland golden-jackets-belgium \
  golden-jackets-uae golden-jackets-by golden-jackets-ecuador; do
  # baixar via gh api (branch default) e contar 'class="member-card' por seção com Python
  echo "$repo"
done
```
Usar Python com assert do count por seção (id=members / #alumni / #challengers / #rising).
Cuidado: founder/cofounder do Brazil têm classe diferente mas SÃO golden.

### 2. Calcular total + certs
```
total = soma de todos os membros de todos os chapters
certs = golden×12 + challenger×10 + rising×8 + alumni×12  (arredondar pra baixo, sufixo "+")
```

### 3. Atualizar o site global (golden-jackets-global) — TODOS os pontos (BUG-2)
1. Ticker (2x — duplicado)
2. Hero `data-target="N"` (Members) e `data-target="N+"` (Certifications) ← NÃO ESQUECER
3. Tooltip do mapa (por país)
4. Cards de chapter
5. Meta/social description
6. Status line
NÃO mexer no histórico/timeline datado.

### 4. Deploy
Global roda em GitHub Pages (repo golden-jackets-global, branch master, arquivo CNAME=goldenjackets.org).
Push no master → workflow "pages build and deployment" publica automático.

### 5. Validar ao vivo
`curl -s https://goldenjackets.org/ | grep -o "N Members"` etc. Confirmar que bateu.
