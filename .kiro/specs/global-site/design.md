# Global Site — Design

> Arquitetura real do site global.

## Componentes

```
data.json (fonte estruturada: chapters[] + stats + last_updated)
   │
   ├──► index.html (renderiza: mapa mundi SVG, pins, ticker, contadores hero, lista chapters)
   │
   └──► update-stats.yml (workflow MANUAL)
            │  varre repos de chapter ativos (data.json → repo|branch)
            │  conta member-card / class="card"
            │  calcula certs (golden×12 + challenger×10 + alumni×12)
            │  trava "never decrease" (só sobe)
            │  atualiza data.json + index.html (via jq + sed)
            └──► commit + push (GitHub Pages publica)

Hospedagem: GitHub Pages, domínio goldenjackets.org (CNAME), branch master.
```

## data.json — schema

```
{
  "chapters": [
    { "id", "name", "iso", "flag", "code", "domain", "repo", "branch",
      "lead", "founded", "status" (active|onboarding), "pin": {top,left}, "members" }
  ],
  "stats": { "members", "certifications", "active_chapters", "countries" },
  "last_updated": "ISO8601"
}
```

## Pontos do index.html que carregam número (BUG-2)

| Ponto | Descrição |
|---|---|
| ticker-content | Rolante; DUPLICADO 2x pro loop CSS infinito |
| hero `data-target` | Active Chapters, In Negotiation, Members, Certifications, Countries |
| tooltips dos pins | "🇧🇷 Brazil · 91 members · ..." por chapter |
| meta description / og:description | "214 members across 21 countries" etc. |

Ao atualizar, TODOS precisam bater. O workflow cobre ticker/hero/tooltips via sed; a meta
pode precisar de ajuste manual.

## Mapa mundi

- SVG world; países ativos com fill dourado, "in negotiation" com path laranja + blink.
- USA e Canadá compartilham path — o path laranja com animation:blink É o USA.
- Países pequenos (Israel, etc.): só pin com radar, sem path individual.
- Flight paths: laranja #FFA500 = onboarding, dourado #FFD700 = active.

## Decisões

- **CRON desligado de propósito:** deploys quebrados de chapter zeravam a contagem. Solução:
  execução manual + trava "never decrease".
- **data.json como fonte:** desacopla os números da varredura frágil de HTML.
