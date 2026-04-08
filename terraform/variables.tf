# variables.tf - Input Variables for Terraform Configuration

variable "aws_region" {
  description = "The AWS region to deploy resources into."
  type        = string
  default     = "us-east-2" # Canonical region from FOUNDATIONAL_TRUTH.md
}
