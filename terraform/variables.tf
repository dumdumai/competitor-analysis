variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "competitor-analysis"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

# Database credentials
variable "db_username" {
  description = "PostgreSQL database username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}

# MongoDB Atlas
variable "mongodb_uri" {
  description = "MongoDB Atlas connection URI"
  type        = string
  sensitive   = true
}

# API Keys
variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "tavily_api_key" {
  description = "Tavily API Key"
  type        = string
  sensitive   = true
}

# Optional Azure OpenAI configuration
variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint"
  type        = string
  default     = ""
}

variable "azure_openai_api_key" {
  description = "Azure OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_openai_deployment" {
  description = "Azure OpenAI deployment name"
  type        = string
  default     = ""
}

# ECS Configuration
variable "ecr_repository_url" {
  description = "ECR repository URL for backend image"
  type        = string
  default     = "151973317602.dkr.ecr.us-east-1.amazonaws.com/competitor-analysis-backend"
}

variable "ecs_cpu" {
  description = "ECS task CPU units"
  type        = number
  default     = 1024
}

variable "ecs_memory" {
  description = "ECS task memory in MB"
  type        = number
  default     = 2048
}
