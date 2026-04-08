# iam.tf - AWS IAM Resources for Agent Delta

# IAM User for Agent Delta
resource "aws_iam_user" "agent_delta_user" {
  name = "agent-delta"
  path = "/agents/"

  tags = {
    Project     = "BlueSoap"
    ManagedBy   = "Terraform"
    Environment = "Production"
    Role        = "AgentDelta"
  }
}

# IAM Policy for Agent Delta (Minimal permissions - Read-only for now, will be expanded)
resource "aws_iam_policy" "agent_delta_policy" {
  name        = "agent-delta-policy"
  description = "IAM policy for Agent Delta with necessary permissions."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeSecurityGroups",
          "s3:ListAllMyBuckets",
          "s3:GetBucketLocation",
          "cloudfront:ListDistributions",
          "route53:ListHostedZones",
          "ses:GetAccountSendingEnabled",
          "dynamodb:ListTables", # To allow listing of state lock tables for validation
          "dynamodb:DescribeTable", # To allow describing state lock tables for validation
          "sts:GetCallerIdentity" # To allow Delta to identify itself
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach the IAM Policy to the Agent Delta User
resource "aws_iam_user_policy_attachment" "agent_delta_policy_attach" {
  user       = aws_iam_user.agent_delta_user.name
  policy_arn = aws_iam_policy.agent_delta_policy.arn
}

# IAM Access Key for Agent Delta
resource "aws_iam_access_key" "agent_delta_access_key" {
  user = aws_iam_user.agent_delta_user.name

  # IMPORTANT: The secret_access_key is sensitive. We will retrieve it
  # after 'terraform apply' and then securely provide it to Agent Delta's environment.
  # DO NOT hardcode this in any files or commit to Git.
}

# Output the Access Key ID (for secure retrieval after apply)
output "agent_delta_access_key_id" {
  description = "The access key ID for Agent Delta IAM user."
  value       = aws_iam_access_key.agent_delta_access_key.id
  sensitive   = true
}

# Output the Secret Access Key (for secure retrieval after apply)
output "agent_delta_secret_access_key" {
  description = "The secret access key for Agent Delta IAM user."
  value       = aws_iam_access_key.agent_delta_access_key.secret
  sensitive   = true
}
