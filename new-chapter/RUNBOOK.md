# Golden Jackets — New Chapter Runbook

## Pré-requisitos
- AWS CLI com profile `gj` configurado (conta 800712212925)
- GitHub CLI autenticado na org `goldenjackets-community`
- Domínio registrado pelo Chapter Leader

## Processo Completo

### Fase 1: Infra AWS (~5 min, automatizado)

```bash
cd golden-jackets-infra/new-chapter
./setup-chapter.sh
```

O script cria automaticamente:
- Route53 hosted zone + nameservers
- ACM certificate (wildcard)
- S3 bucket com website hosting
- CloudFront distribution (pode precisar ajuste manual)
- DynamoDB table para visitor counter
- Lambda counter com Function URL
- Backup vault
- Cognito group + chapter leader user

### Fase 2: DNS (~1-48h, depende do chapter leader)

1. Enviar nameservers pro chapter leader
2. Chapter leader aponta domínio no registrar
3. Após propagação: validar certificado ACM (CNAME)
4. Adicionar domínio customizado no CloudFront
5. Criar records A + AAAA alias no Route53 → CloudFront

### Fase 3: Site (~30 min, manual)

1. Criar repo na org GitHub (clonar do Chile como base)
2. Customizar:
   - `index.html`: nome do país, bandeira, traduções
   - Mapa SVG do país (SimpleMaps ou similar)
   - Card do chapter leader (#1)
   - Sponsor tiers na moeda local
   - Counter URL (Function URL da Lambda)
   - Privacy page (GDPR/LGPD conforme país)
3. Adicionar secret `CLOUDFRONT_DIST_ID` no repo
4. Push → deploy automático via GitHub Actions

### Fase 4: Integrações (~10 min, manual)

1. **gj-apply Lambda** — adicionar ao REPO_MAP:
   ```python
   'dominio.xx': 'goldenjackets-community/golden-jackets-xx',
   'www.dominio.xx': 'goldenjackets-community/golden-jackets-xx',
   ```

2. **gj-admin Lambda** — adicionar chapter nos mappings

3. **API Gateway CORS** — adicionar origin `https://dominio.xx`

4. **Site Global** — atualizar:
   - Contador de membros/países
   - Flight paths no mapa
   - Ticker com novo chapter

5. Push no repo `golden-jackets-infra` → deploy automático das Lambdas

### Fase 5: Comunicação

1. Enviar Chapter Leader Guide (PDF) pro leader
2. Criar LinkedIn Company Page (ou leader cria)
3. Anunciar no grupo WhatsApp Chapter Leaders
4. Post na company page Brazil

---

## Checklist Rápido (copy-paste)

```
[ ] Infra AWS (script)
[ ] Nameservers enviados pro leader
[ ] DNS propagado + certificado validado
[ ] CloudFront com domínio customizado
[ ] Route53 A+AAAA → CloudFront
[ ] Repo criado + site customizado
[ ] CLOUDFRONT_DIST_ID secret no repo
[ ] Deploy funcionando (push → site atualiza)
[ ] gj-apply REPO_MAP atualizado
[ ] gj-admin mappings atualizado
[ ] CORS atualizado na API Gateway
[ ] Site global atualizado (contador, mapa, ticker)
[ ] Chapter Leader Guide enviado
[ ] LinkedIn page criada
[ ] Anúncio feito
```

---

## Lições Aprendidas (Junho 2026)

### Mapa do Chapter Site
- **NÃO usar SimpleMaps** — viewBox achatado (1000x259), mapa fica minúsculo
- **Usar SVG Wikimedia/Albers** — proporções reais, aspect ratio ~2:1
- **Labels**: calcular centroide parseando coordenadas relativas (`m`, `l`, `c`) somando offsets
- **CSS**: nunca colocar `height: auto` que sobrescreve o SVG. Usar `max-width: 700-910px` no container
- **Alaska/Hawaii (USA)**: o SVG Wikimedia já inclui posicionados no canto — não precisa remover

### Mapa Global (golden-jackets-global)
- **Ativar um chapter**: trocar fill do path pra `#b8860b`, flight path pra `#FFD700`, pin de `planned` pra normal, card de `status-onboarding` pra `status-active`
- **USA no world SVG**: Canadá e USA compartilham o mesmo path. O path laranja "In Negotiation" (com animation:blink) É o USA separado — ativar esse
- **Países pequenos (Israel, Singapura)**: não têm path individual no world SVG. Usar apenas pin com radar
- **Flight paths**: laranja `#FFA500` = onboarding, dourado `#FFD700` = active
- **GitHub Pages**: demora 2-3 min pra propagar. Usar `?v=X` ou aba anônima pra testar

### Deploy / GitHub Actions
- **Secret `AWS_ACCOUNT_GJ`** precisa ser setado em cada repo novo (valor: `800712212925`)
- **Secret `CLOUDFRONT_DIST_ID`** precisa ser setado por repo
- Se Actions não roda, fazer deploy manual: `aws s3 cp index.html s3://BUCKET/ --content-type "text/html" --profile gj`

| Chapter | Domínio | CloudFront | Hosted Zone | Backup Vault |
|---------|---------|------------|-------------|--------------|
| Brazil | goldenjacketsbrazil.com | E3N4417EU5IQE6 | Z01877031V3TFGYA6MIEA | gj-site-backups |
| Poland | goldenjackets.pl | E174XK4PPCRG0L | Z07410873K29FYP3PO6JN | gj-poland-backups |
| UK | goldenjackets.co.uk | E10YX1BT67IAVC | Z03540612CJAESUCY0I5D | gj-uk-backups |
| Chile | goldenjackets.cl | EHYKP6CKN2HQ4 | Z06351033U1V5Y6NG588Z | gj-chile-backups |
| India | goldenjackets.in | E3NWIF50KGT06C | Z09802801P2NF2IURPLMW | gj-india-backups |
| France | goldenjackets.fr | (pending) | (pending) | gj-france-backups |

## Conta AWS
- **Account:** 800712212925 (GoldenJackets-Community)
- **Profile:** gj
- **Region:** us-east-1
- **Cognito Pool:** us-east-1_Z0VzzrmIX
- **API:** https://kqiq2bltjd.execute-api.us-east-1.amazonaws.com/admin
