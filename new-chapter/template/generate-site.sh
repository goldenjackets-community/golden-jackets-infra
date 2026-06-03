#!/bin/bash
# Gera site a partir do template
# Usage: ./generate-site.sh config.env

source "$1"

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
  template/index.html > output/index.html

echo "✅ Site gerado em output/index.html"
