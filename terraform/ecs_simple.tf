# Simple ECS deployment using existing infrastructure

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "competitor-analysis-cluster"

  tags = {
    Name = "competitor-analysis-cluster"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/competitor-analysis"
  retention_in_days = 7

  tags = {
    Name = "competitor-analysis-ecs-logs"
  }
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "competitor-analysis-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from anywhere"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "competitor-analysis-ecs-tasks-sg"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "competitor-analysis-backend"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024
  memory                   = 2048

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "151973317602.dkr.ecr.us-east-1.amazonaws.com/competitor-analysis-backend:latest"

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
          value = "production"
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
    Name = "competitor-analysis-backend"
  }
}

# ECS Service
resource "aws_ecs_service" "backend" {
  name            = "competitor-analysis-backend"
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
    Name = "competitor-analysis-backend"
  }
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "competitor-analysis-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for ECS Task
resource "aws_iam_role" "ecs_task_role" {
  name = "competitor-analysis-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Output the ECS service endpoint
output "ecs_service_endpoint" {
  description = "ECS service endpoint"
  value       = "Will be available after deployment - check ECS console for public IP"
}
