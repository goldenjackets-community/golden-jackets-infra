# Global Stats — Como os números do site global funcionam

> Regras duras da automação de estatísticas do site global (`golden-jackets-global`).
> Consulte antes de mexer em contadores, no `data.json` ou no `update-stats.yml`.
> Validado em 2026-09-14. Complementa `counting-rules`.

## Fonte de verdade

- **Estruturada:** `data.json` (repo global) — chapters[] + stats + last_updated.
- **Pública:** os cards nos sites dos chapters (member-card / class="card").
- O `index.html` do global é DERIVADO desses dois. Não é a fonte.

## Workflow update-stats.yml

- Trigger: **`workflow_dispatch` (MANUAL)**. O CRON está **comentado de propósito**.
- **Motivo do CRON off (não religar sem cuidado):** quando um chapter tinha deploy
  quebrado, o site dele ficava sem cards; a varredura contava menos; e o número global
  era sobrescrito pra baixo. Perda de dado real.
- **Trava "never decrease":** o workflow SÓ atualiza members/certs se o valor novo for
  MAIOR que o atual em `data.json`. Nunca diminui. Essa trava é uma proteção de
  integridade — não remover.

## Como conta

- Varre `chapters[]` com `status=="active"` e `repo!=""`, usando `repo|branch` do data.json.
- Conta `class="member-card"` no `index.html`; se 0, tenta `class="card"` no `members.html`
  (chapters usam formatos diferentes — Poland/Belgium usam members.html).
- Certs = golden×12 + challenger×10 + alumni×12. (golden = total − challengers − alumni.)
  Observação: este workflow NÃO separa "rising" — é uma aproximação por design.
- Países = `chapters | length` do data.json.

## Regras ao mexer

- **Nunca inflar** (ver counting-rules). Se atualizar manual, refletir o real.
- Ao atualizar o index.html à mão, cobrir TODOS os pontos (BUG-2 em known-bugs):
  ticker (2x), hero `data-target` (members/certs/chapters/countries), tooltips dos pins,
  meta/og description.
- Ao ativar chapter no mapa: fill do path `#b8860b`, flight path `#FFD700`, pin
  planned→normal, card `status-onboarding`→`status-active` (detalhe no RUNBOOK).
- Branch do global: **master**. Domínio: `goldenjackets.org` (CNAME, GitHub Pages).

## Não confundir

- Este é o contador de MEMBROS/CERTS da comunidade (global).
- O contador de VISITAS por chapter é outro (DynamoDB + gj-<code>-counter — ver spec
  observability). São coisas diferentes.
