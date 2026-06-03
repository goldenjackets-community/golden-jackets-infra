#!/bin/bash
# Gera site a partir do template
# Usage: ./generate-site.sh config.env
# Requires: config.env + regions.html (dropdown options for that country)

set -e

if [ -z "$1" ] || [ ! -f "$1" ]; then
  echo "Usage: ./generate-site.sh <config.env>"
  echo "Example: ./generate-site.sh configs/israel.env"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$1"

CONFIG_DIR=$(cd "$(dirname "$1")" && pwd)
REGIONS_FILE="${CONFIG_DIR}/regions.html"

if [ ! -f "$REGIONS_FILE" ]; then
  echo "⚠️  regions.html not found at ${REGIONS_FILE} — {{REGIONS_OPTIONS}} will be empty"
  REGIONS_OPTIONS=""
else
  REGIONS_OPTIONS=$(cat "$REGIONS_FILE")
fi

mkdir -p output

# Replace all placeholders using sed + awk for multiline REGIONS_OPTIONS
sed \
  -e "s|{{COUNTRY}}|${COUNTRY}|g" \
  -e "s|{{CODE}}|${CODE}|g" \
  -e "s|{{DOMAIN}}|${DOMAIN}|g" \
  -e "s|{{FLAG}}|${FLAG}|g" \
  -e "s|{{LEADER_NAME}}|${LEADER_NAME}|g" \
  -e "s|{{LEADER_EMAIL}}|${LEADER_EMAIL}|g" \
  -e "s|{{LEADER_CITY}}|${LEADER_CITY}|g" \
  -e "s|{{LEADER_STATE}}|${LEADER_STATE}|g" \
  -e "s|{{LEADER_REGION}}|${LEADER_REGION}|g" \
  -e "s|{{LEADER_PHOTO}}|${LEADER_PHOTO}|g" \
  -e "s|{{LEADER_LINKEDIN}}|${LEADER_LINKEDIN}|g" \
  -e "s|{{COUNTER_URL}}|${COUNTER_URL}|g" \
  -e "s|{{SPONSOR_FOUNDING}}|${SPONSOR_FOUNDING}|g" \
  -e "s|{{SPONSOR_GOLD}}|${SPONSOR_GOLD}|g" \
  -e "s|{{SPONSOR_SILVER}}|${SPONSOR_SILVER}|g" \
  -e "s|{{SPONSOR_BRONZE}}|${SPONSOR_BRONZE}|g" \
  "${SCRIPT_DIR}/index.html" | \
  awk -v regions="$REGIONS_OPTIONS" '{gsub(/\{\{REGIONS_OPTIONS\}\}/, regions); print}' \
  > output/index.html

echo "✅ Site gerado em output/index.html"
echo ""
echo "📋 Próximos passos:"
echo "   1. Copie output/index.html para o repo do chapter"
echo "   2. Adicione assets: jacket-${CODE}.png, ${CODE}-map-regions.svg, members/${LEADER_PHOTO}"
echo "   3. Crie privacy.html (GDPR/LGPD conforme país)"
echo "   4. Ajuste max-width do mapa no CSS:"
echo "      - Países altos (Brazil, India, Italy): max-width: 500px"
echo "      - Países largos (USA, France, UK): max-width: 900-1100px"
echo "   5. Customize mapa SVG com highlight do estado do leader"
