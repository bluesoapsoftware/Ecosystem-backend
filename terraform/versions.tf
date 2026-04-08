# versions.tf - Terraform Version and Backend Configuration

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # Specify a compatible version
    }
  }

  # Configure S3 Backend for state management
  # This stores your Terraform state file securely in an S3 bucket,
  # enabling collaboration and preventing local state issues.
  backend "s3" {
    bucket         = "bluesoap-backups" # Our designated S3 bucket for backups
    key            = "terraform/state/ecosystem.tfstate"
    region         = "us-east-2"
    encrypt        = true # Enable server-side encryption for the state file
    dynamodb_table = "terraform-locks" # For state locking to prevent concurrent modifications
  }
}
