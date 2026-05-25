# Security

## When to Apply
When editing Lambda functions, IAM policies, or authentication config.

## Rules
- Least privilege IAM policies — scope to specific resources, never use *
- Cognito User Pools per chapter — never share pools across chapters
- Never log sensitive data (emails, tokens, passwords)
- Sanitize all user input (name, email, URLs) before processing
- Never expose AWS credentials or account IDs in responses
- Use OIDC federation for GitHub Actions — no static IAM credentials
- All secrets in AWS Secrets Manager or environment variables — never in code
- API Gateway authorizers validate JWT tokens from Cognito
- CORS restricted to chapter-specific domains only
