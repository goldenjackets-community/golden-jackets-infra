# Chapters Registry — Fonte de Verdade

> Registro oficial dos chapters da Golden Jackets. Sempre consulte esta tabela antes
> de fazer deploy, invalidar cache, criar PR ou detectar branch. Dados extraídos do
> `mcp-server/server.py` (CHAPTERS), `lambdas/gj-apply/gj_apply.py` (REPO_MAP) e da
> GitHub API (default_branch), validados em 2026-09-14.

## Constantes globais

- **Conta AWS:** `800712212925` (GoldenJackets-Community)
- **Org GitHub:** `goldenjackets-community`
- **Cognito User Pool (único, compartilhado):** `us-east-1_Z0VzzrmIX`
- **API Gateway (único):** `https://kqiq2bltjd.execute-api.us-east-1.amazonaws.com`
- **Região:** `us-east-1`

## Tabela de Chapters (15 ativos)

| Chapter | Repo | Domínio (bucket) | CloudFront Dist | Branch default |
|---|---|---|---|---|
| brazil | golden-jackets-brazil | www.goldenjacketsbrazil.com | E3N4417EU5IQE6 | **main** |
| poland | golden-jackets-poland | goldenjackets.pl | E174XK4PPCRG0L | master |
| uk | golden-jackets-uk | goldenjackets.co.uk | E10YX1BT67IAVC | master |
| chile | golden-jackets-chile | goldenjackets.cl | EHYKP6CKN2HQ4 | master |
| india | golden-jackets-india | goldenjackets.in | E3NWIF50KGT06C | master |
| france | golden-jackets-france | goldenjackets.fr | E2O44PVJBUUR5Y | master |
| usa | golden-jackets-usa | goldenjackets.us | E9TMGWA6LF7DP | master |
| italy | golden-jackets-italy | goldenjackets.it | E1PME26ZJ9H7WV | **main** |
| peru | golden-jackets-peru | goldenjackets.pe | E3V1Z9N208C841 | master |
| israel | golden-jackets-israel | goldenjackets.co.il | E12FG4V68VTB02 | master |
| belarus (by) | golden-jackets-by | goldenjackets.by | E2OVUWFPFH9S4Z | master |
| ecuador | golden-jackets-ecuador | goldenjackets.ec | E3NV9WJS4AZL32 | master |
| colombia | golden-jackets-colombia | goldenjackets.co | E2IPBAVCWPQWL1 | master |
| belgium | golden-jackets-belgium | goldenjackets.be | EE0BVLVAL9RPX | **main** |
| uae | golden-jackets-uae | goldenjackets.ae | E3I43LMFL7RNDS | **main** |

**Site global:** `golden-jackets-global` — domínio `goldenjackets.org` (GitHub Pages) — branch **master**.

## Branch default — regra prática (BUG conhecido)

O branch default **VARIA**. Sempre detecte antes de push/PR. Nunca assuma `main`.

- **main:** brazil, belgium, italy, uae
- **master:** poland, uk, chile, india, france, usa, peru, israel, by, ecuador, colombia, global

Detectar com: `gh api repos/goldenjackets-community/golden-jackets-<chapter> --jq .default_branch`

## Domínios alternativos (REPO_MAP do gj-apply)

O `gj-apply` mapeia domínio→repo pelo header `origin`. Alguns chapters têm domínios extras:
- USA aceita também: `goldenjacketsus.com`, `www.goldenjacketsus.com`
- Todos aceitam o prefixo `www.`

**Cuidado (BUG de link):** o slug do LinkedIn NÃO segue o domínio. Ex.: USA usa a página
`golden-jackets-us` (não `-usa`). Ver steering `known-bugs`.

## Regras de integridade

- Esta tabela é a fonte de verdade para automações. Se um valor divergir do código,
  investigue antes de agir — não corrija cegamente.
- Nunca inflar número de chapters/países/membros. Ver steering `counting-rules`.
