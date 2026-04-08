# iam.tf - AWS IAM Resources for Agent Delta

# 1. Create the IAM User for Agent Delta
resource "aws_iam_user" "agent_delta" {
  name = "agent-delta-monitor"
  path = "/system/" # Logically separates service accounts

  tags = {
    Project     = "BlueSoap"
    Role        = "MonitoringAndDiagnostics"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# 2. Define the Least-Privilege Policy (Comprehensive Monitoring Focus)
resource "aws_iam_policy" "delta_monitoring_policy" {
  name        = "AgentDeltaMonitoringPolicy"
  description = "Minimal read-only permissions for Agent Delta monitoring and diagnostics across BlueSoap's AWS services."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowMonitoringRead"
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricData",
          "cloudwatch:ListMetrics",
          "cloudwatch:DescribeAlarms",
          "ec2:DescribeInstances",
          "s3:ListAllMyBuckets",
          "s3:GetBucketLocation",
          "cloudfront:ListDistributions",  # Added for full visibility
          "route53:ListHostedZones",       # Added for full visibility
          "ses:GetAccountSendingEnabled",  # Added for email health
          "dynamodb:ListTables",           # Added for state lock table validation
          "dynamodb:DescribeTable",        # Added for state lock table validation
          "sts:GetCallerIdentity"          # Added for self-identification
        ]
        Resource = "*"
      }
    ]
  })
}

# 3. Attach the Policy to the User
resource "aws_iam_user_policy_attachment" "delta_attach" {
  user       = aws_iam_user.agent_delta.name
  policy_arn = aws_iam_policy.delta_monitoring_policy.arn
}

# 4. Generate Programmatic Credentials (To be handled securely)
resource "aws_iam_access_key" "delta_key" {
  user = aws_iam_user.agent_delta.name
}

# 5. Output the Access Key ID (for secure retrieval after apply)
output "agent_delta_access_key_id" {
  description = "The access key ID for Agent Delta IAM user."
  value       = aws_iam_access_key.delta_key.id
  sensitive   = true
}

# 6. Output the Secret Access Key (for secure retrieval after apply)
output "agent_delta_secret_access_key" {
  description = "The secret access key for Agent Delta IAM user."
  value       = aws_iam_access_key.delta_key.secret
  sensitive   = true
}
