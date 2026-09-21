#!/usr/bin/env bash
# Golden Jackets — Post-Provisioning Validator (#45)
# Verifica se um chapter recém-provisionado está 100% funcional:
# recursos AWS (REQ-CP-2) + integrações compartilhadas (REQ-CP-6) + site/apply no ar.
#
# Uso:
#   ./validate-chapter.sh <code> [domain]
#   ./validate-chapter.sh peru goldenjackets.pe
#
# Se o domain for omitido, valida só os recursos AWS por convenção de nome.
# Não altera nada — é somente leitura. Exit code 0 se tudo passou, 1 se houve falha.

set -u
# Nota: pipefail é intencionalmente omitido. Vários checks usam `... | grep -q X`,
# e grep -q fecha o pipe ao achar o match, fazendo o comando a montante receber
# SIGPIPE — com pipefail isso viraria falso negativo.

PROFILE="gj"
REGION="us-east-1"
ACCOUNT="800712212925"
POOL_ID="us-east-1_Z0VzzrmIX"
ORG="goldenjackets-community"

CODE="${1:-}"
DOMAIN="${2:-}"

if [ -z "$CODE" ]; then
  echo "Uso: $0 <code> [domain]   (ex: $0 peru goldenjackets.pe)"
  exit 2
fi

REPO="golden-jackets-${CODE}"
COUNTER_TABLE="gj-${CODE}-visitors"
COUNTER_FUNCTION="gj-${CODE}-counter"
BACKUP_VAULT="gj-${CODE}-backups"

PASS=0
FAIL=0
WARN=0

ok()   { echo "  ✅ $1"; PASS=$((PASS+1)); }
bad()  { echo "  ❌ $1"; FAIL=$((FAIL+1)); }
warn() { echo "  ⚠️  $1"; WARN=$((WARN+1)); }

echo "🐝 Golden Jackets — Validador pós-provisionamento"
echo "=================================================="
echo "   Chapter: ${CODE}   Repo: ${ORG}/${REPO}"
[ -n "$DOMAIN" ] && echo "   Domain: ${DOMAIN}"
echo ""

# --- Fase 1: recursos AWS (REQ-CP-2) ---
echo "── Fase 1 · Infra AWS ──"

# DynamoDB visitors table
if aws dynamodb describe-table --profile "$PROFILE" --region "$REGION" \
     --table-name "$COUNTER_TABLE" >/dev/null 2>&1; then
  ok "DynamoDB table $COUNTER_TABLE existe"
else
  bad "DynamoDB table $COUNTER_TABLE NÃO encontrada"
fi

# Lambda counter
if aws lambda get-function --profile "$PROFILE" --region "$REGION" \
     --function-name "$COUNTER_FUNCTION" >/dev/null 2>&1; then
  ok "Lambda $COUNTER_FUNCTION existe"
  # Function URL configurada?
  FURL=$(aws lambda get-function-url-config --profile "$PROFILE" --region "$REGION" \
           --function-name "$COUNTER_FUNCTION" --query "FunctionUrl" --output text 2>/dev/null)
  if [ -n "$FURL" ] && [ "$FURL" != "None" ]; then
    ok "Function URL configurada: $FURL"
    # Testa se responde 200 com o formato esperado
    BODY=$(curl -s -m 10 "$FURL" 2>/dev/null)
    if echo "$BODY" | grep -q "total_visits" && echo "$BODY" | grep -q "unique_visitors"; then
      ok "Counter responde com {total_visits,unique_visitors}"
    else
      bad "Counter respondeu inesperado: ${BODY:0:80}"
    fi
  else
    bad "Function URL do counter NÃO configurada"
  fi
else
  bad "Lambda $COUNTER_FUNCTION NÃO encontrada"
fi

# Backup vault
if aws backup describe-backup-vault --profile "$PROFILE" --region "$REGION" \
     --backup-vault-name "$BACKUP_VAULT" >/dev/null 2>&1; then
  ok "Backup vault $BACKUP_VAULT existe"
else
  warn "Backup vault $BACKUP_VAULT NÃO encontrado"
fi

# Grupo Cognito
if aws cognito-idp get-group --profile "$PROFILE" --region "$REGION" \
     --user-pool-id "$POOL_ID" --group-name "$CODE" >/dev/null 2>&1; then
  ok "Grupo Cognito '$CODE' existe"
else
  bad "Grupo Cognito '$CODE' NÃO encontrado"
fi

# S3 bucket (= domínio)
if [ -n "$DOMAIN" ]; then
  if aws s3api head-bucket --profile "$PROFILE" --bucket "$DOMAIN" >/dev/null 2>&1; then
    ok "S3 bucket $DOMAIN existe"
  else
    warn "S3 bucket $DOMAIN não acessível (pode ser nome www.$DOMAIN)"
  fi
fi

echo ""

# --- Site / DNS / cert (Fase 2/3) ---
echo "── Fase 2/3 · Site & DNS ──"
if [ -n "$DOMAIN" ]; then
  HTTP=$(curl -s -o /dev/null -m 15 -w "%{http_code}" "https://${DOMAIN}" 2>/dev/null)
  if [ "$HTTP" = "200" ]; then
    ok "https://${DOMAIN} responde 200"
  elif [[ "$HTTP" =~ ^3 ]]; then
    # 301/302/308: site no ar, apenas redireciona (ex.: apex -> www ou domínio alternativo)
    ok "https://${DOMAIN} responde ${HTTP} (redirect — site no ar)"
  else
    bad "https://${DOMAIN} respondeu HTTP ${HTTP:-timeout}"
  fi
  # cert ACM emitido para o domínio?
  CERT_ARN=$(aws acm list-certificates --profile "$PROFILE" --region "$REGION" \
    --query "CertificateSummaryList[?DomainName=='${DOMAIN}'||DomainName=='*.${DOMAIN}'].CertificateArn | [0]" \
    --output text 2>/dev/null)
  if [ -n "$CERT_ARN" ] && [ "$CERT_ARN" != "None" ]; then
    CERT_STATUS=$(aws acm describe-certificate --profile "$PROFILE" --region "$REGION" \
      --certificate-arn "$CERT_ARN" --query "Certificate.Status" --output text 2>/dev/null)
    [ "$CERT_STATUS" = "ISSUED" ] && ok "Cert ACM ISSUED" || warn "Cert ACM em estado: $CERT_STATUS"
  else
    warn "Cert ACM para ${DOMAIN} não encontrado"
  fi
else
  warn "Domain não informado — pulei checagem de site/DNS/cert"
fi

echo ""

# --- Repo do site (Fase 3) ---
echo "── Fase 3 · Repositório ──"
if gh repo view "${ORG}/${REPO}" >/dev/null 2>&1; then
  ok "Repo ${ORG}/${REPO} existe"
  DB=$(gh api "repos/${ORG}/${REPO}" --jq '.default_branch' 2>/dev/null)
  ok "Branch default: ${DB}"
  # index.html com apply form? (jq content + base64, removendo quebras de linha)
  if gh api "repos/${ORG}/${REPO}/contents/index.html?ref=${DB}" --jq '.content' 2>/dev/null \
       | tr -d '\n' | base64 -d 2>/dev/null | grep -q "applyForm"; then
    ok "index.html tem o Apply Form"
  else
    bad "index.html sem Apply Form (applyForm)"
  fi
else
  bad "Repo ${ORG}/${REPO} NÃO encontrado"
fi

echo ""

# --- Fase 4: integrações compartilhadas (REQ-CP-6) ---
echo "── Fase 4 · Integrações (gj-apply / gj-admin / CORS) ──"

# gj-apply REPO_MAP contém o domínio do chapter? (a chave do REPO_MAP é o domínio, não o code)
APPLY_SRC=$(aws lambda get-function --profile "$PROFILE" --region "$REGION" \
  --function-name gj-apply --query "Code.Location" --output text 2>/dev/null)
if [ -n "$APPLY_SRC" ] && [ "$APPLY_SRC" != "None" ]; then
  TMPZ=$(mktemp /tmp/gjapply.XXXX.zip)
  curl -s -o "$TMPZ" "$APPLY_SRC" 2>/dev/null
  # procura pelo domínio (chave real do REPO_MAP) ou pelo nome do repo; grep no pipe evita null byte
  if { [ -n "$DOMAIN" ] && unzip -p "$TMPZ" 2>/dev/null | grep -q "$DOMAIN"; } \
     || unzip -p "$TMPZ" 2>/dev/null | grep -q "golden-jackets-${CODE}"; then
    ok "gj-apply REPO_MAP referencia o chapter ${CODE}"
  else
    bad "gj-apply REPO_MAP NÃO referencia o chapter (apply não vai funcionar)"
  fi
  rm -f "$TMPZ"
else
  warn "Não consegui inspecionar o código do gj-apply"
fi

# gj-admin referencia o chapter?
ADMIN_SRC=$(aws lambda get-function --profile "$PROFILE" --region "$REGION" \
  --function-name gj-admin --query "Code.Location" --output text 2>/dev/null)
if [ -n "$ADMIN_SRC" ] && [ "$ADMIN_SRC" != "None" ]; then
  TMPZ=$(mktemp /tmp/gjadmin.XXXX.zip)
  curl -s -o "$TMPZ" "$ADMIN_SRC" 2>/dev/null
  if { [ -n "$DOMAIN" ] && unzip -p "$TMPZ" 2>/dev/null | grep -q "$DOMAIN"; } \
     || unzip -p "$TMPZ" 2>/dev/null | grep -q "golden-jackets-${CODE}" \
     || unzip -p "$TMPZ" 2>/dev/null | grep -q "'${CODE}'"; then
    ok "gj-admin referencia o chapter ${CODE}"
  else
    warn "gj-admin NÃO referencia o chapter ${CODE}"
  fi
  rm -f "$TMPZ"
else
  warn "Não consegui inspecionar o código do gj-admin"
fi

echo ""
echo "── Observabilidade ──"
# Health check + alarm existem para o chapter?
if aws cloudwatch describe-alarms --profile "$PROFILE" --region "$REGION" \
     --alarm-names "gj-down-${CODE}" --query "MetricAlarms[0].AlarmName" --output text 2>/dev/null \
     | grep -q "gj-down-${CODE}"; then
  ok "CloudWatch alarm gj-down-${CODE} existe"
else
  warn "Alarm gj-down-${CODE} não encontrado (rodar deploy da stack gj-observability)"
fi

echo ""
echo "=================================================="
echo "Resultado: ${PASS} ✅  ${WARN} ⚠️   ${FAIL} ❌"
if [ "$FAIL" -gt 0 ]; then
  echo "❌ Chapter ${CODE} tem pendências críticas — revisar antes de anunciar."
  exit 1
else
  echo "✅ Chapter ${CODE} validado (avisos ⚠️ são opcionais/manuais)."
  exit 0
fi
