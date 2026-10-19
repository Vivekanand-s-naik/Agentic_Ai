# AWS Instructions

## Architecture
- Use managed services over self-hosted when possible
- Multi-AZ for production; use Auto Scaling Groups
- Separate accounts per environment (Organizations)
- Store secrets in Secrets Manager/SSM; never in code

## Security
- Least-privilege IAM policies; use roles over long-lived keys
- Enable CloudTrail, GuardDuty, Config
- Encrypt at rest (KMS) and in transit (TLS)
- Use VPC endpoints for AWS service access

## Deployment
- IaC (CDK/Terraform) for all infra; review via PR
- Blue/green or canary deployments; rollback plan
- Tag resources for cost allocation

## Cost
- Right-size instances; use Savings Plans/Spot
- Enable S3 lifecycle policies; clean up unused resources
