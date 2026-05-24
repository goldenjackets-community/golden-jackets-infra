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
echo "⚠️  Create repo manually on GitHub:"
echo "   1. Go to https://github.com/organizations/${REPO_ORG}/repositories/new"
echo "   2. Name: ${REPO_NAME}"
echo "   3. Private → Public"
echo "   4. Clone golden-jackets-chile as template"
echo "   5. Add secret CLOUDFRONT_DIST_ID = <CloudFront ID from step 4>"
echo ""

echo "=== STEP 10: Update Shared Lambdas ==="
echo "⚠️  MANUAL — Add to gj-apply REPO_MAP:"
echo "   '${DOMAIN}': '${REPO_ORG}/${REPO_NAME}',"
echo "   'www.${DOMAIN}': '${REPO_ORG}/${REPO_NAME}',"
echo ""
echo "⚠️  MANUAL — Add to gj-admin chapter mappings"
echo "⚠️  MANUAL — Add CORS origin: https://${DOMAIN}"
echo ""

echo "======================================"
echo "🎉 INFRA DONE! Next steps:"
echo ""
echo "1. Wait for nameservers to propagate (chapter leader points domain)"
echo "2. Validate ACM certificate (add DNS CNAME record)"
echo "3. Add custom domain to CloudFront (after cert validates)"
echo "4. Create Route53 A+AAAA alias records → CloudFront"
echo "5. Clone site from Chile, customize (map, translations, members)"
echo "6. Push to repo → GitHub Actions deploys automatically"
echo "7. Update global site (counter, flight paths, ticker)"
echo ""
echo "📝 Resources created:"
echo "   Hosted Zone: ${HZ_ID}"
echo "   Certificate: ${CERT_ARN}"
echo "   S3 Bucket: ${BUCKET}"
echo "   DynamoDB: ${COUNTER_TABLE}"
echo "   Lambda: ${COUNTER_FUNCTION} (${FUNC_URL})"
echo "   Backup Vault: ${BACKUP_VAULT}"
echo "   Cognito Group: ${CODE}"
echo "   Chapter Leader: ${LEADER_EMAIL}"
