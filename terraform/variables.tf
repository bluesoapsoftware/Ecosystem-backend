# variables.tf - Input Variables for Terraform Configuration

variable "aws_region" {
  description = "The AWS region to deploy resources into."
  type        = string
  default     = "us-east-2" # Canonical region from FOUNDATIONAL_TRUTH.md
}

variable "db_username" {
  description = "Master username for the RDS database."
  type        = string
  sensitive   = true # Mark as sensitive to prevent showing in plan/apply output
}

variable "db_password" {
  description = "Master password for the RDS database."
  type        = string
  sensitive   = true # Mark as sensitive to prevent showing in plan/apply output
}
