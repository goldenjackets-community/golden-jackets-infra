# Project Conventions

## When to Apply
Always apply when editing any file in this repository.

## Rules
- This repo contains shared infrastructure code (Lambdas, IAM, Cognito config)
- All Lambda functions are Python 3.12 with minimal dependencies
- Use boto3 for AWS SDK calls — no other AWS SDKs
- Each Lambda has its own directory with handler.py and optional requirements.txt
- Input validation is mandatory on all Lambda handlers
- Use environment variables for configuration — never hardcode ARNs or account IDs
- Keep functions small and single-purpose
- All responses follow consistent JSON structure: {statusCode, headers, body}
- CORS headers must be set for all API responses
