# Member Lifecycle — Requirements

> Como um profissional AWS vira membro de um chapter da Golden Jackets, do apply até
> aparecer no site, e como é movido/recontado depois. Reverse-engineered de `gj-apply`,
> `gj-admin` e dos sites. Referência-cruzada: steering `counting-rules`, `known-bugs`,
> `admin-actions`, `chapters-registry`.

## 1. Visão

Um membro se auto-aplica pelo site do chapter. Isso gera um PR no repo do chapter com o
card do membro. Um admin do chapter (ou global) aprova (merge) ou rejeita (close). Após o
merge, o site é publicado e os contadores são atualizados. Membros podem ser movidos entre
categorias (Golden/Challenger/Rising/Alumni) ou chapters.

## 2. Categorias (régua sagrada)

- **Golden Jacket:** 12/12 certificações AWS ativas
- **Challenger:** 10–11
- **Rising:** 7–9
- **Alumni:** já foi Golden, deixou expirar
- Fórmula de certs por chapter: `golden×12 + challenger×10 + rising×8 + alumni×12`

## 3. Requisitos

- **REQ-ML-1:** O apply é self-service pelo botão "I'm a Golden Jacket 🏆" / "Join Us" do
  site. NÃO pelo "Get in Touch" (esse aponta pra LinkedIn — ver known-bugs).
- **REQ-ML-2:** O `gj-apply` detecta o chapter pelo header `origin` (REPO_MAP) e cria um
  PR no repo correto, no branch default correto (varia main/master — ver chapters-registry).
- **REQ-ML-3:** O PR DEVE conter um card completo: `member-card`, nome, cidade, `data-state`
  com UF/estado real (nunca "Other"), data, LinkedIn, categoria, foto/avatar, `card-number`.
- **REQ-ML-4:** Um PR com card vazio ou incompleto NÃO deve ser aprovado (BUG conhecido:
  gj-apply às vezes gera PR vazio — validar diff antes do merge).
- **REQ-ML-5:** Aprovação = `merge-pr` (renumera cards dos PRs restantes via
  `rebuild_remaining_prs`). Rejeição = `close-pr`.
- **REQ-ML-6:** Governança: chapter lead aprova PRs do próprio chapter; Global Lead valida
  antes de mergear direto. Ver steering `community-rules`.
- **REQ-ML-7:** Após merge, atualizar contadores em TODOS os pontos (ver counting-rules) e
  invalidar cache CloudFront se necessário.
- **REQ-ML-8:** `move-member` move entre chapters/categorias mantendo integridade dos números.
- **REQ-ML-9:** Nunca inflar números. Recontagem deve refletir o estado real do site.

## 4. Fora de escopo

- Login no Lounge (Cognito) — coberto pela spec `admin-panel` e infra compartilhada.
- Criação de chapter novo — spec `chapter-provisioning`.
