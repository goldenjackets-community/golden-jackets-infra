# Infrastructure

## When to Apply
When discussing deploy, CI/CD, or AWS resources.

## Rules
- Region: us-east-1
- Shared infrastructure serves all chapters (Brazil, Poland, UK, Chile)
- Deploy via GitHub Actions — never manual AWS Console changes
- All resources tagged with `project: golden-jackets` and `chapter` tag
- Budget alarm at $10/month per chapter — always keep costs minimal
- Prefer serverless (Lambda, DynamoDB, API Gateway) over always-on resources
- Lambda timeout: 30s max, memory: 128MB unless justified
- API Gateway rate limiting: 10 req/s, burst 20
- DynamoDB on-demand capacity (pay-per-request)
- Default branch is `main`
