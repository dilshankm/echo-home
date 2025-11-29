# 🔐 Required GitHub Secrets for AWS Deployment

## Docker Hub Secrets
- `DOCKER_USERNAME` - Your Docker Hub username
- `DOCKER_PASSWORD` - Your Docker Hub password or access token

## AWS Credentials
- `AWS_ACCESS_KEY_ID` - AWS access key ID
- `AWS_SECRET_ACCESS_KEY` - AWS secret access key
- `AWS_SESSION_TOKEN` - AWS session token (if using temporary credentials)
- `AWS_REGION` - AWS region (e.g., `eu-central-1`, `us-east-1`)

## Application Secrets
- `OPENAI_API_KEY` - OpenAI API key (required)

## Optional Application Configuration
- `USE_MOCK_NEO4J` - Set to `true` to use mock Neo4j (NetworkX) - Default: `true`
- `LOG_LEVEL` - Logging level - Default: `INFO`

## Neo4j Configuration (Only if USE_MOCK_NEO4J=false)
- `NEO4J_URI` - Neo4j connection URI: `neo4j+s://cc774f1a.databases.neo4j.io`
- `NEO4J_USER` - Neo4j username: `neo4j`
- `NEO4J_PASSWORD` - Neo4j password: `dHhS4kVpj0UmPLLYTjcMoRp7C7bpPPT6KjJnWqfXoBo`

## ECS Configuration (Optional - defaults provided)
- `ECS_CLUSTER_NAME` - ECS cluster name - Default: `echo-home-cluster`
- `ECS_SERVICE_NAME` - ECS service name - Default: `echo-home-service`
- `ECS_TASK_EXECUTION_ROLE_ARN` - IAM role ARN for task execution
- `ECS_TASK_ROLE_ARN` - IAM role ARN for task role

## Minimum Required Secrets
For basic deployment with mock Neo4j:
1. `DOCKER_USERNAME`
2. `DOCKER_PASSWORD`
3. `AWS_ACCESS_KEY_ID`
4. `AWS_SECRET_ACCESS_KEY`
5. `AWS_REGION`
6. `OPENAI_API_KEY`

## Setup Instructions
1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret from the list above
4. For AWS credentials, you can use IAM user or temporary credentials

## Port Configuration
- **Container Port:** 8000
- **Host Port:** 8000 (mapped in ECS service)
- **Health Check:** `/api/health`

## AWS Resources to Create First
1. ECS Cluster: `echo-home-cluster`
2. ECS Service: `echo-home-service`
3. IAM Roles:
   - Task Execution Role (for pulling images and logging)
   - Task Role (for application permissions)
4. CloudWatch Log Group: `/ecs/echo-home`
5. Load Balancer (if needed) with target group on port 8000
