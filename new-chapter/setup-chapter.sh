#!/bin/bash
# Golden Jackets — New Chapter Setup Script (v2)
# Creates ALL infrastructure + site + global map activation
# Usage: ./setup-chapter.sh
set -e

echo "🐝 Golden Jackets — New Chapter Setup v2"
echo "=========================================="
echo ""

# --- INPUT ---
read -p "Country name (e.g., Peru): " COUNTRY
read -p "Country code lowercase (e.g., peru): " CODE
read -p "Domain (e.g., goldenjackets.pe): " DOMAIN
read -p "Chapter Leader name: " LEADER_NAME
read -p "Chapter Leader email: " LEADER_EMAIL
read -p "Chapter Leader city: " LEADER_CITY
read -p "Chapter Leader LinkedIn URL: " LEADER_LINKEDIN
read -p "Country flag emoji (e.g., 🇵🇪): " FLAG
read -p "SimpleMaps country code 2-letter (e.g., pe): " SIMPLEMAPS_CODE
read -p "GitHub branch name [master]: " BRANCH
BRANCH=${BRANCH:-master}

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
INFRA_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "📋 Summary:"
echo "   Country: ${COUNTRY} ${FLAG}"
echo "   Code: ${CODE}"
echo "   Domain: ${DOMAIN}"
echo "   Repo: ${REPO_ORG}/${REPO_NAME}"
echo "   Bucket: ${BUCKET}"
echo "   Leader: ${LEADER_NAME} (${LEADER_EMAIL})"
echo ""
read -p "Proceed? (y/n): " CONFIRM
[ "$CONFIRM" != "y" ] && echo "Aborted." && exit 1

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  PHASE 1: AWS Infrastructure             ║"
echo "╚══════════════════════════════════════════╝"
echo ""

echo "=== 1/14: Route53 Hosted Zone ==="
HZ_ID=$(aws route53 create-hosted-zone \
  --name "${DOMAIN}" \
  --caller-reference "gj-${CODE}-$(date +%s)" \
  --profile ${PROFILE} \
  --query 'HostedZone.Id' --output text | sed 's|/hostedzone/||')
echo "✅ Hosted Zone: ${HZ_ID}"
NS=$(aws route53 get-hosted-zone --id ${HZ_ID} --profile ${PROFILE} \
  --query 'DelegationSet.NameServers' --output text)
echo "   Nameservers: ${NS}"
echo ""

echo "=== 2/14: ACM Certificate ==="
CERT_ARN=$(aws acm request-certificate \
  --domain-name "${DOMAIN}" \
  --subject-alternative-names "*.${DOMAIN}" \
  --validation-method DNS \
  --profile ${PROFILE} --region ${REGION} \
  --query 'CertificateArn' --output text)
echo "✅ Certificate: ${CERT_ARN}"
sleep 5
# Add validation CNAME to Route53
VALIDATION=$(aws acm describe-certificate \
  --certificate-arn "${CERT_ARN}" \
  --profile ${PROFILE} --region ${REGION} \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord' --output json)
CNAME_NAME=$(echo "$VALIDATION" | python3 -c "import sys,json;print(json.load(sys.stdin)['Name'])")
CNAME_VALUE=$(echo "$VALIDATION" | python3 -c "import sys,json;print(json.load(sys.stdin)['Value'])")
aws route53 change-resource-record-sets --hosted-zone-id ${HZ_ID} --profile ${PROFILE} --change-batch "{
  \"Changes\": [{\"Action\":\"UPSERT\",\"ResourceRecordSet\":{
    \"Name\":\"${CNAME_NAME}\",\"Type\":\"CNAME\",\"TTL\":300,
    \"ResourceRecords\":[{\"Value\":\"${CNAME_VALUE}\"}]}}]}" > /dev/null
echo "✅ ACM validation CNAME added to Route53"
echo ""

echo "=== 3/14: S3 Bucket ==="
aws s3 mb "s3://${BUCKET}" --profile ${PROFILE} --region ${REGION}
aws s3api put-public-access-block --bucket "${BUCKET}" --profile ${PROFILE} \
  --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
aws s3 website "s3://${BUCKET}" --index-document index.html --error-document index.html
aws s3api put-bucket-policy --bucket "${BUCKET}" --profile ${PROFILE} --policy "{
  \"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"PublicRead\",\"Effect\":\"Allow\",
  \"Principal\":\"*\",\"Action\":\"s3:GetObject\",\"Resource\":\"arn:aws:s3:::${BUCKET}/*\"}]}"
echo "✅ S3 bucket: ${BUCKET}"
echo ""

echo "=== 4/14: CloudFront Distribution ==="
CF_ID=$(aws cloudfront create-distribution \
  --profile ${PROFILE} \
  --distribution-config "{
    \"CallerReference\":\"gj-${CODE}-$(date +%s)\",
    \"Origins\":{\"Quantity\":1,\"Items\":[{\"Id\":\"S3-${BUCKET}\",
      \"DomainName\":\"${BUCKET}.s3-website-${REGION}.amazonaws.com\",
      \"CustomOriginConfig\":{\"HTTPPort\":80,\"HTTPSPort\":443,\"OriginProtocolPolicy\":\"http-only\"}}]},
    \"DefaultCacheBehavior\":{\"TargetOriginId\":\"S3-${BUCKET}\",\"ViewerProtocolPolicy\":\"redirect-to-https\",
      \"AllowedMethods\":{\"Quantity\":2,\"Items\":[\"GET\",\"HEAD\"]},
      \"ForwardedValues\":{\"QueryString\":false,\"Cookies\":{\"Forward\":\"none\"}},
      \"Compress\":true,\"MinTTL\":0,\"DefaultTTL\":86400,\"MaxTTL\":31536000},
    \"Comment\":\"Golden Jackets ${COUNTRY}\",\"Enabled\":true,\"DefaultRootObject\":\"index.html\",
    \"PriceClass\":\"PriceClass_100\",
    \"CustomErrorResponses\":{\"Quantity\":1,\"Items\":[{\"ErrorCode\":404,\"ResponsePagePath\":\"/index.html\",\"ResponseCode\":\"200\",\"ErrorCachingMinTTL\":300}]}
  }" --query 'Distribution.{Id:Id,Domain:DomainName}' --output json)
CF_DIST_ID=$(echo "$CF_ID" | python3 -c "import sys,json;print(json.load(sys.stdin)['Id'])")
CF_DOMAIN=$(echo "$CF_ID" | python3 -c "import sys,json;print(json.load(sys.stdin)['Domain'])")
echo "✅ CloudFront: ${CF_DIST_ID} (${CF_DOMAIN})"
echo ""

echo "=== 5/14: DynamoDB ==="
aws dynamodb create-table \
  --table-name "${COUNTER_TABLE}" \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --profile ${PROFILE} --region ${REGION} > /dev/null
echo "✅ DynamoDB: ${COUNTER_TABLE}"
echo ""

echo "=== 6/14: Counter Lambda ==="
cat > /tmp/gj_counter_${CODE}.py << LAMBDA
import json, boto3
from datetime import datetime
dynamodb = boto3.resource('dynamodb', region_name='${REGION}')
table = dynamodb.Table('${COUNTER_TABLE}')
def lambda_handler(event, context):
    table.update_item(Key={'id':'counter'},
        UpdateExpression='SET total_visits = if_not_exists(total_visits, :zero) + :one, unique_visitors = if_not_exists(unique_visitors, :zero)',
        ExpressionAttributeValues={':one':1,':zero':0})
    ip = event.get('requestContext',{}).get('http',{}).get('sourceIp','unknown')
    try:
        table.put_item(Item={'id':f'ip#{ip}','first_visit':datetime.utcnow().isoformat()},ConditionExpression='attribute_not_exists(id)')
        table.update_item(Key={'id':'counter'},UpdateExpression='SET unique_visitors = if_not_exists(unique_visitors, :zero) + :one',ExpressionAttributeValues={':one':1,':zero':0})
    except: pass
    resp = table.get_item(Key={'id':'counter'})
    item = resp.get('Item',{})
    return {'statusCode':200,'headers':{'Access-Control-Allow-Origin':'*'},
        'body':json.dumps({'total_visits':int(item.get('total_visits',0)),'unique_visitors':int(item.get('unique_visitors',0))})}
LAMBDA
cd /tmp && zip -j "gj_counter_${CODE}.zip" "gj_counter_${CODE}.py" > /dev/null
aws lambda create-function \
  --function-name "${COUNTER_FUNCTION}" --runtime python3.12 \
  --handler "gj_counter_${CODE}.lambda_handler" \
  --zip-file "fileb:///tmp/gj_counter_${CODE}.zip" \
  --role "arn:aws:iam::${ACCOUNT}:role/gj-apply-lambda" \
  --timeout 10 --profile ${PROFILE} --region ${REGION} > /dev/null
FUNC_URL=$(aws lambda create-function-url-config \
  --function-name "${COUNTER_FUNCTION}" --auth-type NONE \
  --cors '{"AllowOrigins":["*"]}' \
  --profile ${PROFILE} --region ${REGION} --query 'FunctionUrl' --output text)
aws lambda add-permission \
  --function-name "${COUNTER_FUNCTION}" --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl --principal "*" --function-url-auth-type NONE \
  --profile ${PROFILE} --region ${REGION} > /dev/null
echo "✅ Lambda: ${COUNTER_FUNCTION} (${FUNC_URL})"
echo ""

echo "=== 7/14: Backup Vault ==="
aws backup create-backup-vault --backup-vault-name "${BACKUP_VAULT}" \
  --profile ${PROFILE} --region ${REGION} > /dev/null
echo "✅ Backup vault: ${BACKUP_VAULT}"
echo ""

echo "=== 8/14: Cognito Group + Chapter Leader ==="
aws cognito-idp create-group --group-name "${CODE}" --user-pool-id "${POOL_ID}" \
  --description "Golden Jackets ${COUNTRY}" --profile ${PROFILE} --region ${REGION} > /dev/null
aws cognito-idp admin-create-user --user-pool-id "${POOL_ID}" --username "${LEADER_EMAIL}" \
  --user-attributes Name=email,Value="${LEADER_EMAIL}" Name=email_verified,Value=true \
  --desired-delivery-mediums EMAIL --profile ${PROFILE} --region ${REGION} > /dev/null 2>&1 || true
aws cognito-idp admin-add-user-to-group --user-pool-id "${POOL_ID}" \
  --username "${LEADER_EMAIL}" --group-name "${CODE}" --profile ${PROFILE} --region ${REGION}
echo "✅ Cognito: ${LEADER_EMAIL} → ${CODE}"
echo ""

echo "=== 9/14: IAM Deploy Policy (add S3 + CloudFront) ==="
POLICY=$(aws iam get-role-policy --role-name github-actions-deploy --policy-name deploy-policy \
  --profile ${PROFILE} --region ${REGION} --query 'PolicyDocument' --output json)
# Add S3 bucket to policy
POLICY=$(echo "$POLICY" | python3 -c "
import sys,json
p=json.load(sys.stdin)
s3_stmt=next(s for s in p['Statement'] if 's3:PutObject' in s.get('Action',[]))
new_resources=['arn:aws:s3:::${BUCKET}','arn:aws:s3:::${BUCKET}/*']
for r in new_resources:
    if r not in s3_stmt['Resource']:
        s3_stmt['Resource'].append(r)
cf_stmt=next(s for s in p['Statement'] if s.get('Action')=='cloudfront:CreateInvalidation')
cf_arn='arn:aws:cloudfront::${ACCOUNT}:distribution/${CF_DIST_ID}'
if cf_arn not in cf_stmt['Resource']:
    cf_stmt['Resource'].append(cf_arn)
print(json.dumps(p))
")
aws iam put-role-policy --role-name github-actions-deploy --policy-name deploy-policy \
  --policy-document "${POLICY}" --profile ${PROFILE} --region ${REGION}
echo "✅ IAM policy updated (S3 + CloudFront)"
echo ""

echo "=== 10/14: Update gj-apply + gj-admin + CORS ==="
APPLY_FILE="${INFRA_DIR}/lambdas/gj-apply/gj_apply.py"
if ! grep -q "'${DOMAIN}'" "${APPLY_FILE}" 2>/dev/null; then
  sed -i "/^REPO_MAP = {/a\\    '${DOMAIN}': '${REPO_ORG}/${REPO_NAME}',\n    'www.${DOMAIN}': '${REPO_ORG}/${REPO_NAME}'," "${APPLY_FILE}"
fi
# CORS
CURRENT_ORIGINS=$(aws apigatewayv2 get-api --api-id kqiq2bltjd --profile ${PROFILE} --region ${REGION} \
  --query 'CorsConfiguration.AllowOrigins' --output json)
NEW_ORIGINS=$(echo "$CURRENT_ORIGINS" | python3 -c "
import sys,json
o=json.load(sys.stdin)
for u in ['https://${DOMAIN}','https://www.${DOMAIN}']:
    if u not in o: o.append(u)
print(json.dumps(o))
")
aws apigatewayv2 update-api --api-id kqiq2bltjd --profile ${PROFILE} --region ${REGION} \
  --cors-configuration "{\"AllowOrigins\":${NEW_ORIGINS},\"AllowMethods\":[\"POST\",\"OPTIONS\",\"GET\"],\"AllowHeaders\":[\"Content-Type\",\"Authorization\"]}" > /dev/null
echo "✅ REPO_MAP + CORS updated"
echo ""

echo "=== 11/14: SNS Subscription ==="
aws sns subscribe --topic-arn "arn:aws:sns:${REGION}:${ACCOUNT}:goldenjackets-alerts" \
  --protocol email --notification-endpoint "${LEADER_EMAIL}" \
  --profile ${PROFILE} --region ${REGION} > /dev/null 2>&1
echo "✅ SNS subscription (pending email confirm)"
echo ""

echo "╔══════════════════════════════════════════╗"
echo "║  PHASE 2: GitHub Repo + Site             ║"
echo "╚══════════════════════════════════════════╝"
echo ""

echo "=== 12/14: Create Repo + Site ==="
gh repo create "${REPO_ORG}/${REPO_NAME}" --public \
  --description "Golden Jackets ${COUNTRY} ${FLAG} — Community of AWS professionals with all 12 certifications" 2>/dev/null || true

# Clone Chile as base
TMPDIR=$(mktemp -d)
gh repo clone ${REPO_ORG}/golden-jackets-chile "${TMPDIR}/site" -- --depth 1 2>/dev/null
cd "${TMPDIR}/site"
rm -rf .git BACKLOG.md
git init && git checkout -b ${BRANCH}

# Download country map SVG from SimpleMaps
curl -sL "https://simplemaps.com/static/svg/country/${SIMPLEMAPS_CODE}/admin1/${SIMPLEMAPS_CODE}.svg" -o assets/${CODE}-map-regions.svg 2>/dev/null
if [ ! -s "assets/${CODE}-map-regions.svg" ]; then
  echo "⚠️  Could not download map SVG. Add manually later."
fi

# Customize SVG (dark theme, gray labels, no stroke on text)
if [ -s "assets/${CODE}-map-regions.svg" ]; then
  sed -i 's/fill="[^"]*"/fill="#2d2d4e"/' assets/${CODE}-map-regions.svg
  sed -i 's/stroke="[^"]*"/stroke="#555"/' assets/${CODE}-map-regions.svg
  sed -i 's/stroke-width="[^"]*"/stroke-width="0.5"/' assets/${CODE}-map-regions.svg
  # Add style block
  sed -i 's|<g id="features">|<style>\n  path { transition: fill 0.3s, stroke 0.3s; cursor: pointer; }\n  path:hover { fill: #3d3d6e; }\n  text { font-family: Arial, sans-serif; fill: #888; font-weight: 400; text-anchor: middle; pointer-events: none; stroke: none; }\n</style>\n<g id="features">|' assets/${CODE}-map-regions.svg
  sed -i "s|<svg |<svg id=\"${CODE}-map\" |" assets/${CODE}-map-regions.svg
fi

# Remove Chile-specific assets
rm -f assets/chile-map-regions.svg assets/jacket-chile.png assets/members/*.jpg

# Bulk replace
find . -name "*.html" -o -name "*.js" -o -name "*.xml" -o -name "*.txt" | while read f; do
  sed -i "s/Golden Jackets Chile/Golden Jackets ${COUNTRY}/g" "$f"
  sed -i "s/goldenjackets\.cl/${DOMAIN}/g" "$f"
  sed -i "s/Chile/${COUNTRY}/g" "$f"
  sed -i "s/chile/${CODE}/g" "$f"
  sed -i "s/Chilean/${COUNTRY}n/g" "$f"
  sed -i "s/🇨🇱/${FLAG}/g" "$f"
  sed -i "s|jacket-chile.png|jacket-${CODE}.png|g" "$f"
  sed -i "s|chile-map-regions.svg|${CODE}-map-regions.svg|g" "$f"
done

# Fix map img size
sed -i 's|max-width:120px|max-width:700px;width:100%|g' index.html

# Update deploy.yml
sed -i "s|s3://goldenjackets.cl/|s3://${BUCKET}/|g" .github/workflows/deploy.yml
sed -i "s|d245cwyl4dcv9y.cloudfront.net|${CF_DOMAIN}|g" .github/workflows/deploy.yml
sed -i "s|\"chapter\":\"chile\"|\"chapter\":\"${CODE}\"|g" .github/workflows/deploy.yml

# Update config.js
cat > config.js << CONF
var GJ_CONFIG = {
  ADMIN_API: 'https://kqiq2bltjd.execute-api.us-east-1.amazonaws.com/admin',
  ADMIN_EMAILS: ['${LEADER_EMAIL}', 'ricardo.gulias@goldenjacketsbrazil.com'],
  CHAPTER: '${CODE}'
};
CONF

# Update counter URL
sed -i "s|https://[a-z0-9]*\.lambda-url\.us-east-1\.on\.aws/|${FUNC_URL}|g" index.html

# Replace member card with chapter leader
sed -i "s|Oscar Alexander Gaviria González|${LEADER_NAME}|g" index.html
sed -i "s|Oscar Gaviria|${LEADER_NAME}|g" index.html
sed -i "s|Santiago, Región Metropolitana, ${COUNTRY}|${LEADER_CITY}, ${COUNTRY}|g" index.html
sed -i "s|https://www.linkedin.com/in/oscar-alexander-gaviria-gonzelez-11286883/|${LEADER_LINKEDIN}|g" index.html

# Update README
cat > README.md << README
# Golden Jackets ${COUNTRY} ${FLAG}

Community site celebrating ${COUNTRY}n AWS professionals who earned all 12 active certifications.

## Deploy
Push to \`${BRANCH}\` → GitHub Actions syncs to S3 + CloudFront invalidation.

## 🤖 Built With AI
This project was built using **Kiro CLI** (powered by Claude, Anthropic).
README

# Push to GitHub
git add -A
git commit -m "Initial ${COUNTRY} site"
git remote add origin "https://github.com/${REPO_ORG}/${REPO_NAME}.git"
git push -u origin ${BRANCH}
cd /home/gulias
rm -rf "${TMPDIR}"
echo "✅ Repo created and pushed: ${REPO_ORG}/${REPO_NAME}"
echo ""

echo "=== 13/14: GitHub Secrets ==="
gh secret set CLOUDFRONT_DIST_ID --repo "${REPO_ORG}/${REPO_NAME}" --body "${CF_DIST_ID}"
GH_TOKEN=$(gh auth token)
gh secret set GH_PAT --repo "${REPO_ORG}/${REPO_NAME}" --body "${GH_TOKEN}"
echo "✅ Secrets: CLOUDFRONT_DIST_ID + GH_PAT"
echo ""

echo "=== 14/14: Update Global Site ==="
cd /home/gulias/golden-jackets-global
git pull origin master 2>/dev/null

# Add chapter to data.json
python3 -c "
import json
with open('data.json') as f:
    d = json.load(f)
# Check if already exists
if not any(ch['id'] == '${CODE}' for ch in d['chapters']):
    d['chapters'].append({
        'id': '${CODE}',
        'name': '${COUNTRY}',
        'flag': '${FLAG}',
        'domain': '${DOMAIN}',
        'status': 'active',
        'repo': '${REPO_ORG}/${REPO_NAME}',
        'branch': '${BRANCH}'
    })
    d['stats']['active_chapters'] = sum(1 for c in d['chapters'] if c['status']=='active')
    d['stats']['countries'] = len(d['chapters'])
with open('data.json','w') as f:
    json.dump(d, f, indent=2)
print('data.json updated')
"

# Activate pin (remove planned if exists, or add new pin)
if grep -q "planned.*${CODE}\|${CODE}.*planned" index.html; then
  sed -i "s|class=\"pin planned\"\(.*${CODE}\)|class=\"pin\"\1|" index.html
  sed -i "s|Coming soon</div></div>\(.*${CODE}\)|Founded $(date +%B\ %Y)</div></div>\1|" index.html
fi

# Update ticker
sed -i "s|Expanding to.*${COUNTRY}|${FLAG} ${COUNTRY} · Live!|g" index.html

git add -A
git commit -m "Add ${COUNTRY} chapter to global site" 2>/dev/null || true
git push origin master 2>/dev/null || true
echo "✅ Global site updated"
echo ""

# Push infra changes (gj-apply)
cd "${INFRA_DIR}"
git add -A
git commit -m "Add ${COUNTRY} to chapter mappings" 2>/dev/null || true
git push origin main 2>/dev/null || true

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ SETUP COMPLETE!                       ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "📝 Resources:"
echo "   Hosted Zone: ${HZ_ID}"
echo "   Certificate: ${CERT_ARN}"
echo "   S3 Bucket: ${BUCKET}"
echo "   CloudFront: ${CF_DIST_ID} (${CF_DOMAIN})"
echo "   DynamoDB: ${COUNTER_TABLE}"
echo "   Lambda: ${COUNTER_FUNCTION} (${FUNC_URL})"
echo "   Backup Vault: ${BACKUP_VAULT}"
echo "   Cognito: ${CODE} (${LEADER_EMAIL})"
echo "   Repo: ${REPO_ORG}/${REPO_NAME}"
echo ""
echo "⏳ Send these nameservers to ${LEADER_NAME}:"
echo "   $(echo ${NS} | tr '\t' '\n' | head -4)"
echo ""
echo "📋 After DNS propagates:"
echo "   1. ACM certificate validates automatically"
echo "   2. Add custom domain to CloudFront: ${DOMAIN} + www.${DOMAIN}"
echo "   3. Create Route53 A+AAAA alias → ${CF_DIST_ID}"
echo "   4. Add country map highlight on global site (manual — find path in SVG)"
echo ""
echo "⚠️  Manual steps remaining:"
echo "   - Upload chapter leader photo to assets/members/"
echo "   - Upload jacket-${CODE}.png to assets/"
echo "   - Highlight country on global map SVG (find path, change fill to #b8860b)"
echo "   - Customize region dropdowns in index.html"
echo "   - Add region labels to map SVG"
