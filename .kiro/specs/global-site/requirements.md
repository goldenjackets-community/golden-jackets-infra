# Global Site — Requirements

> O site global da comunidade (`goldenjackets.org`, repo `golden-jackets-global`, GitHub
> Pages). Agrega todos os chapters: mapa mundi, ticker, contadores, lista de chapters.
> Reverse-engineered de `index.html`, `data.json` e `.github/workflows/update-stats.yml`.
> Referência: steering `global-stats`, `counting-rules`, `chapters-registry`, `known-bugs`.

## 1. Visão

`goldenjackets.org` é a vitrine unificada da comunidade. Mostra o mapa mundi com pins dos
chapters ativos e "in negotiation", um ticker rolante com membros por país, contadores
animados (chapters, membros, certs, países) e a lista de chapters com status. Os números
derivam de `data.json` (fonte estruturada) e são refletidos no `index.html`.

## 2. Requisitos

- **REQ-GS-1:** `data.json` é a fonte estruturada: array `chapters[]` (id, name, iso, flag,
  code, domain, repo, branch, lead, founded, status, pin, members) + objeto `stats`
  (members, certifications, active_chapters, countries) + `last_updated`.
- **REQ-GS-2:** O `index.html` reflete os números do `data.json` em MÚLTIPLOS pontos:
  ticker (duplicado 2x pro loop), hero `data-target` (chapters/members/certs/countries),
  tooltips dos pins, meta/og description. Todos devem bater. Ver known-bugs (BUG-2).
- **REQ-GS-3:** A atualização de stats é feita pelo workflow `update-stats.yml`
  (workflow_dispatch — MANUAL). O CRON está DESABILITADO de propósito.
- **REQ-GS-4:** Trava de integridade "never decrease": o workflow só AUMENTA members/certs;
  nunca diminui (evita zerar quando um deploy de chapter está quebrado). Ver global-stats.
- **REQ-GS-5:** Contagem de membros varre os repos de chapter ativos: conta `class="member-card"`
  no index.html OU `class="card"` no members.html (formatos variam por chapter).
- **REQ-GS-6:** Certs calculadas: golden×12 + challenger×10 + alumni×12 (coerente com
  counting-rules; o rising não aparece separado neste workflow — ver observação).
- **REQ-GS-7:** Ativar um chapter novo no mapa: trocar fill do path (#b8860b), flight path
  (#FFD700), pin de planned→normal, card status-onboarding→status-active (ver RUNBOOK).
- **REQ-GS-8:** Nunca inflar números manualmente. Se subir manual, deve refletir o real.

## 3. Observações / riscos

- O workflow conta member-card de forma heurística (grep). Rising challengers podem não
  ser distinguidos perfeitamente — o número de certs é aproximado por design.
- Por isso o CRON foi desligado: quando um chapter tinha deploy quebrado, o site dele não
  tinha os cards e a contagem caía, sobrescrevendo o número correto. A trava "never
  decrease" + execução manual mitigam isso.

## 4. Fora de escopo

- Sites dos chapters individuais (spec member-lifecycle / chapter-provisioning).
