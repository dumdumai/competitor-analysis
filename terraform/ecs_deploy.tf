# ECS Task Definition for Backend using existing databases
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-backend"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_cpu
  memory                   = var.ecs_memory

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "${var.ecr_repository_url}:latest"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "MONGODB_URI"
          value = var.mongodb_uri
        },
        {
          name  = "REDIS_URL"
          value = "redis://${aws_elasticache_replication_group.valkey.primary_endpoint_address}:${aws_elasticache_replication_group.valkey.port}"
        },
        {
          name  = "POSTGRES_URL"
          value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
        },
        {
          name  = "AZURE_OPENAI_API_KEY"
          value = var.azure_openai_api_key
        },
        {
          name  = "AZURE_OPENAI_ENDPOINT"
          value = var.azure_openai_endpoint
        },
        {
          name  = "TAVILY_API_KEY"
          value = var.tavily_api_key
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "LOG_LEVEL"
          value = "INFO"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs_logs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name        = "${var.project_name}-backend"
    Environment = var.environment
  }
}

# ECS Service
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = aws_subnet.public[*].id
    assign_public_ip = true
  }

  tags = {
    Name        = "${var.project_name}-backend"
    Environment = var.environment
  }
}

# Output the ECS service endpoint
output "ecs_service_endpoint" {
  description = "ECS service endpoint"
  value       = "Will be available after deployment - check ECS console for public IP"
}
