# AWS Infrastructure Deployment

This Terraform configuration deploys the Competitor Analysis System to AWS with minimal architecture:

## Infrastructure Components

- **Elastic Beanstalk**: Python 3.12 app hosting (frontend + backend together)
- **RDS PostgreSQL**: Smallest instance (db.t3.micro) for LangGraph checkpointing
- **ElastiCache Valkey**: Redis cache (cache.t3.micro)
- **MongoDB Atlas**: External managed MongoDB
- **VPC**: Simple network with public/private subnets

## Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **Terraform >= 1.0** installed
3. **MongoDB Atlas cluster** created and connection string ready
4. **API Keys** for OpenAI and Tavily services

## Deployment Steps

### 1. Configure Variables

```bash
# Copy and edit the variables file
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your actual values
```

### 2. Initialize and Deploy

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the infrastructure
terraform apply
```

### 3. Deploy Application

```bash
# Use the simple deployment script
./deploy.sh

# Or manually:
cd frontend && npm run build
cp -r frontend/build backend/static
cd backend && zip -r ../app.zip .
# Upload app.zip to Elastic Beanstalk
```

## Environment Variables

The following environment variables are automatically configured in Elastic Beanstalk:

- `POSTGRES_URL`: PostgreSQL connection for LangGraph checkpointing
- `REDIS_URL`: Valkey (Redis) connection for caching
- `DATABASE_URL`: MongoDB Atlas URI (from terraform.tfvars)
- `OPENAI_API_KEY`: OpenAI API key (from terraform.tfvars)
- `TAVILY_API_KEY`: Tavily API key (from terraform.tfvars)
- `CORS_ORIGINS`: CloudFront domain for CORS configuration

## Costs Estimate (Monthly)

- **Elastic Beanstalk (t3.small)**: ~$15-30
- **RDS PostgreSQL (db.t3.micro)**: ~$12-15
- **ElastiCache Valkey (cache.t3.micro)**: ~$12-15

**Total estimated cost**: ~$40-60/month

## Security Features

- VPC with private subnets for databases
- Security groups with minimal required access
- Encrypted storage for RDS and ElastiCache
- CloudFront HTTPS enforcement
- IAM roles with least privilege access

## Monitoring

- Elastic Beanstalk health monitoring enabled
- CloudWatch logs for application monitoring
- RDS automated backups (7-day retention)

## Cleanup

To destroy all infrastructure:

```bash
terraform destroy
```

**Warning**: This will delete all data in RDS and ElastiCache. Ensure you have backups if needed.
