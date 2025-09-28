output "application_url" {
  description = "Application URL"
  value       = aws_elastic_beanstalk_environment.main.endpoint_url
}

output "deployment_instructions" {
  description = "Simple deployment instructions"
  value = <<-EOT
Deployment:
1. Build frontend: cd frontend && npm run build
2. Copy build to backend: cp -r frontend/build backend/static
3. Deploy: cd backend && eb init && eb deploy

Access: ${aws_elastic_beanstalk_environment.main.endpoint_url}
EOT
}
