#!/bin/bash
# Golden Jackets — New Chapter Setup Script
# Usage: ./setup-chapter.sh
# Prerequisites: AWS CLI configured with profile 'gj', GitHub CLI authenticated
set -e

echo "🐝 Golden Jackets — New Chapter Setup"
echo "======================================"
echo ""

# --- INPUT ---
read -p "Country name (e.g., USA): " COUNTRY
read -p "Country code lowercase (e.g., usa): " CODE
read -p "Domain (e.g., goldenjackets.us): " DOMAIN
read -p "Chapter Leader name: " LEADER_NAME
read -p "Chapter Leader email: " LEADER_EMAIL
read -p "Chapter Leader city: " LEADER_CITY
read -p "GitHub branch name [main]: " BRANCH
BRANCH=${BRANCH:-main}

PROFILE="gj"
REGION="us-east-1"
ACCOUNT="800712212925"
POOL_ID="us-east-1_Z0VzzrmIX"
REPO_ORG="goldenjackets-community"
REPO_NAME="golden-jackets-${CODE}"
BUCKET="${DOMAIN}"
COUNTER_TABLE="gj-${CODE}-visitors"
COUNTER_FUNCTION="gj-${CODE}-counter"
BACKUP_VAULT="gj-${CODE}-backups"

echo ""
echo "📋 Summary:"
echo "   Country: ${COUNTRY}"
echo "   Code: ${CODE}"
echo "   Domain: ${DOMAIN}"
echo "   Repo: ${REPO_ORG}/${REPO_NAME}"
echo "   Bucket: ${BUCKET}"
echo "   Leader: ${LEADER_NAME} (${LEADER_EMAIL})"
echo ""
read -p "Proceed? (y/n): " CONFIRM
[ "$CONFIRM" != "y" ] && echo "Aborted." && exit 1

echo ""
echo "=== STEP 1: Route53 Hosted Zone ==="
HZ_ID=$(aws route53 create-hosted-zone \
  --name "${DOMAIN}" \
  --caller-reference "gj-${CODE}-$(date +%s)" \
  --profile ${PROFILE} \
  --query 'HostedZone.Id' --output text | sed 's|/hostedzone/||')
echo "✅ Hosted Zone: ${HZ_ID}"
echo ""
echo "⚠️  NAMESERVERS (send to chapter leader to point domain):"
aws route53 get-hosted-zone --id ${HZ_ID} --profile ${PROFILE} \
  --query 'DelegationSet.NameServers' --output table
echo ""

echo "=== STEP 2: ACM Certificate ==="
CERT_ARN=$(aws acm request-certificate \
  --domain-name "${DOMAIN}" \
  --subject-alternative-names "*.${DOMAIN}" \
  --validation-method DNS \
  --profile ${PROFILE} --region ${REGION} \
  --query 'CertificateArn' --output text)
echo "✅ Certificate requested: ${CERT_ARN}"
echo "⚠️  DNS validation record will be added after nameservers propagate."
echo ""

echo "=== STEP 3: S3 Bucket ==="
aws s3 mb "s3://${BUCKET}" --profile ${PROFILE} --region ${REGION}
aws s3 website "s3://${BUCKET}" --index-document index.html --error-document index.html
aws s3api put-bucket-policy --bucket "${BUCKET}" --profile ${PROFILE} --policy "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [{
    \"Sid\": \"PublicRead\",
    \"Effect\": \"Allow\",
    \"Principal\": \"*\",
    \"Action\": \"s3:GetObject\",
    \"Resource\": \"arn:aws:s3:::${BUCKET}/*\"
  }]
}"
echo "✅ S3 bucket: ${BUCKET} (website hosting enabled)"
echo ""

echo "=== STEP 4: CloudFront Distribution ==="
CF_ID=$(aws cloudfront create-distribution \
  --profile ${PROFILE} \
  --origin-domain-name "${BUCKET}.s3-website-${REGION}.amazonaws.com" \
  --default-root-object index.html \
  --query 'Distribution.Id' --output text \
  2>/dev/null || echo "MANUAL")
if [ "$CF_ID" = "MANUAL" ]; then
  echo "⚠️  CloudFront needs manual creation (complex config). Create with:"
  echo "   - Origin: ${BUCKET}.s3-website-${REGION}.amazonaws.com (HTTP only)"
  echo "   - Aliases: ${DOMAIN}, www.${DOMAIN}"
  echo "   - SSL: ${CERT_ARN} (after validation)"
  echo "   - Default root: index.html"
  echo "   - Price class: PriceClass_100"
else
  echo "✅ CloudFront: ${CF_ID}"
fi
echo ""

echo "=== STEP 5: DynamoDB (visitor counter) ==="
aws dynamodb create-table \
  --table-name "${COUNTER_TABLE}" \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --profile ${PROFILE} --region ${REGION} > /dev/null
echo "✅ DynamoDB table: ${COUNTER_TABLE}"
echo ""

echo "=== STEP 6: Counter Lambda ==="
cat > /tmp/gj_counter_${CODE}.py << LAMBDA
import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='${REGION}')
table = dynamodb.Table('${COUNTER_TABLE}')

def lambda_handler(event, context):
    table.update_item(
        Key={'id': 'counter'},
        UpdateExpression='SET total_visits = if_not_exists(total_visits, :zero) + :one, unique_visitors = if_not_exists(unique_visitors, :zero)',
        ExpressionAttributeValues={':one': 1, ':zero': 0}
    )
    ip = event.get('requestContext', {}).get('http', {}).get('sourceIp', 'unknown')
    try:
        table.put_item(
            Item={'id': f'ip#{ip}', 'first_visit': datetime.utcnow().isoformat()},
            ConditionExpression='attribute_not_exists(id)'
        )
        table.update_item(
            Key={'id': 'counter'},
            UpdateExpression='SET unique_visitors = if_not_exists(unique_visitors, :zero) + :one',
            ExpressionAttributeValues={':one': 1, ':zero': 0}
        )
    except:
        pass
    resp = table.get_item(Key={'id': 'counter'})
    item = resp.get('Item', {})
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'total_visits': int(item.get('total_visits', 0)),
            'unique_visitors': int(item.get('unique_visitors', 0))
        })
    }
LAMBDA

cd /tmp && zip -j "gj_counter_${CODE}.zip" "gj_counter_${CODE}.py"
aws lambda create-function \
  --function-name "${COUNTER_FUNCTION}" \
  --runtime python3.12 \
  --handler "gj_counter_${CODE}.lambda_handler" \
  --zip-file "fileb:///tmp/gj_counter_${CODE}.zip" \
  --role "arn:aws:iam::${ACCOUNT}:role/gj-apply-lambda" \
  --timeout 10 \
  --profile ${PROFILE} --region ${REGION} > /dev/null

FUNC_URL=$(aws lambda create-function-url-config \
  --function-name "${COUNTER_FUNCTION}" \
  --auth-type NONE \
  --cors '{"AllowOrigins":["*"]}' \
  --profile ${PROFILE} --region ${REGION} \
  --query 'FunctionUrl' --output text)

aws lambda add-permission \
  --function-name "${COUNTER_FUNCTION}" \
  --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  --profile ${PROFILE} --region ${REGION} > /dev/null

echo "✅ Counter Lambda: ${COUNTER_FUNCTION}"
echo "   Function URL: ${FUNC_URL}"
echo ""

echo "=== STEP 7: Backup Vault ==="
aws backup create-backup-vault \
  --backup-vault-name "${BACKUP_VAULT}" \
  --profile ${PROFILE} --region ${REGION} > /dev/null
echo "✅ Backup vault: ${BACKUP_VAULT}"
echo ""

echo "=== STEP 8: Cognito Group ==="
aws cognito-idp create-group \
  --group-name "${CODE}" \
  --user-pool-id "${POOL_ID}" \
  --description "Golden Jackets ${COUNTRY}" \
  --profile ${PROFILE} --region ${REGION} > /dev/null
echo "✅ Cognito group: ${CODE}"

# Create chapter leader user
aws cognito-idp admin-create-user \
  --user-pool-id "${POOL_ID}" \
  --username "${LEADER_EMAIL}" \
  --user-attributes Name=email,Value="${LEADER_EMAIL}" Name=email_verified,Value=true \
  --desired-delivery-mediums EMAIL \
  --profile ${PROFILE} --region ${REGION} > /dev/null 2>&1 || echo "   (user may already exist)"
aws cognito-idp admin-add-user-to-group \
  --user-pool-id "${POOL_ID}" \
  --username "${LEADER_EMAIL}" \
  --group-name "${CODE}" \
  --profile ${PROFILE} --region ${REGION}
echo "✅ Chapter leader added: ${LEADER_EMAIL} → ${CODE}"
echo ""

echo "=== STEP 9: GitHub Repository ==="
# Create repo from Chile template using gh CLI
gh repo create "${REPO_ORG}/${REPO_NAME}" --public --clone --template "${REPO_ORG}/golden-jackets-chile" 2>/dev/null || echo "   (repo may already exist)"
if [ -d "${REPO_NAME}" ]; then
  cd "${REPO_NAME}"
  # Set default branch
  git checkout -b ${BRANCH} 2>/dev/null || git checkout ${BRANCH}
  if [ "${BRANCH}" != "main" ]; then
    git push -u origin ${BRANCH} 2>/dev/null
    gh repo edit "${REPO_ORG}/${REPO_NAME}" --default-branch ${BRANCH}
  fi
  cd ..
  rm -rf "${REPO_NAME}"
fi
# Add CLOUDFRONT_DIST_ID secret (CF_ID from step 4)
if [ -n "${CF_ID}" ] && [ "${CF_ID}" != "MANUAL" ]; then
  gh secret set CLOUDFRONT_DIST_ID --repo "${REPO_ORG}/${REPO_NAME}" --body "${CF_ID}" 2>/dev/null || true
fi
echo "✅ GitHub repo: ${REPO_ORG}/${REPO_NAME} (branch: ${BRANCH})"
echo ""

echo "=== STEP 10: Update gj-apply Lambda (REPO_MAP) ==="
APPLY_FILE="/home/gulias/golden-jackets-infra/lambdas/gj-apply/gj_apply.py"
# Add domain mappings to REPO_MAP
if ! grep -q "'${DOMAIN}'" "${APPLY_FILE}" 2>/dev/null; then
  sed -i "/^REPO_MAP = {/a\\    '${DOMAIN}': '${REPO_ORG}/${REPO_NAME}',\n    'www.${DOMAIN}': '${REPO_ORG}/${REPO_NAME}'," "${APPLY_FILE}"
  echo "✅ REPO_MAP updated in gj-apply"
else
  echo "   (already in REPO_MAP)"
fi
echo ""

echo "=== STEP 11: Update gj-admin Lambda (chapter mappings) ==="
ADMIN_FILE="/home/gulias/golden-jackets-infra/lambdas/gj-admin/gj_admin.py"
# Add to ORIGIN_MAP if it exists
if grep -q "ORIGIN_MAP" "${ADMIN_FILE}" 2>/dev/null; then
  if ! grep -q "'${DOMAIN}'" "${ADMIN_FILE}"; then
    sed -i "/ORIGIN_MAP = {/a\\    '${DOMAIN}': '${CODE}',\n    'www.${DOMAIN}': '${CODE}'," "${ADMIN_FILE}"
    echo "✅ ORIGIN_MAP updated in gj-admin"
  else
    echo "   (already in ORIGIN_MAP)"
  fi
fi
# Add to REPO_MAP in admin if exists
if grep -q "REPO_MAP" "${ADMIN_FILE}" 2>/dev/null; then
  if ! grep -q "'${CODE}'" "${ADMIN_FILE}"; then
    sed -i "/REPO_MAP.*=.*{/a\\    '${CODE}': '${REPO_ORG}/${REPO_NAME}'," "${ADMIN_FILE}"
    echo "✅ REPO_MAP updated in gj-admin"
  fi
fi
echo ""

echo "=== STEP 12: Update API Gateway CORS ==="
API_ID="kqiq2bltjd"
CURRENT_CORS=$(aws apigatewayv2 get-api --api-id ${API_ID} --profile ${PROFILE} --region ${REGION} --query 'CorsConfiguration.AllowOrigins' --output text 2>/dev/null)
if ! echo "${CURRENT_CORS}" | grep -q "${DOMAIN}"; then
  # Get current origins and add new one
  aws apigatewayv2 update-api --api-id ${API_ID} \
    --cors-configuration "AllowOrigins=https://${DOMAIN},https://www.${DOMAIN},https://goldenjacketsbrazil.com,https://www.goldenjacketsbrazil.com,https://goldenjackets.pl,https://www.goldenjackets.pl,https://goldenjackets.co.uk,https://www.goldenjackets.co.uk,https://goldenjackets.cl,https://www.goldenjackets.cl,AllowMethods=POST,OPTIONS,GET,AllowHeaders=Content-Type,Authorization" \
    --profile ${PROFILE} --region ${REGION} > /dev/null 2>&1
  echo "✅ CORS updated: https://${DOMAIN}"
else
  echo "   (CORS already includes ${DOMAIN})"
fi
echo ""

echo "=== STEP 13: Deploy updated Lambdas ==="
cd /home/gulias/golden-jackets-infra
git add -A
git commit -m "Add ${COUNTRY} to all chapter mappings (REPO_MAP, ORIGIN_MAP, CORS)" 2>/dev/null || true
git push origin main 2>/dev/null || true
echo "✅ Lambda code pushed (GitHub Actions will deploy)"
echo ""

echo "=== STEP 14: Add SNS subscription for chapter leader ==="
aws sns subscribe \
  --topic-arn "arn:aws:sns:${REGION}:${ACCOUNT}:goldenjackets-alerts" \
  --protocol email \
  --notification-endpoint "${LEADER_EMAIL}" \
  --profile ${PROFILE} --region ${REGION} > /dev/null 2>&1
echo "✅ SNS subscription created (${LEADER_EMAIL} needs to confirm)"
echo ""

echo "======================================"
echo "🎉 SETUP COMPLETE!"
echo ""
echo "📝 Resources created:"
echo "   Hosted Zone: ${HZ_ID}"
echo "   Certificate: ${CERT_ARN}"
echo "   S3 Bucket: ${BUCKET}"
echo "   CloudFront: ${CF_ID}"
echo "   DynamoDB: ${COUNTER_TABLE}"
echo "   Lambda: ${COUNTER_FUNCTION} (${FUNC_URL})"
echo "   Backup Vault: ${BACKUP_VAULT}"
echo "   Cognito Group: ${CODE}"
echo "   Chapter Leader: ${LEADER_EMAIL}"
echo "   GitHub Repo: ${REPO_ORG}/${REPO_NAME}"
echo ""
echo "⏳ Remaining (requires DNS propagation):"
echo "   1. Chapter leader points nameservers at registrar"
echo "   2. ACM certificate validates automatically"
echo "   3. Add custom domain to CloudFront"
echo "   4. Create Route53 A+AAAA alias → CloudFront"
echo ""
echo "🌐 Nameservers to send to ${LEADER_NAME}:"
aws route53 get-hosted-zone --id ${HZ_ID} --profile ${PROFILE} \
  --query 'DelegationSet.NameServers' --output table
echo ""
echo "📱 Customize site: clone repo, update index.html (map, members, translations)"
